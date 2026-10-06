import asyncio
import logging
from pathlib import Path
from typing import List

from fastapi import (
    APIRouter,
    Depends,
    File,
    Form,
    HTTPException,
    Request,
    UploadFile,
)

from backend.api.auth import get_current_user
from backend.api.dependencies import (
    history_pdf_rate_limit,
    pdf_rate_limit,
    resume_analysis_rate_limit,
)

from backend.models.schemas import (
    AnalysisResponse,
    ComponentScores,
    JDComparison,
    SkillValidationDetails,
    GrammarAnalysis,
    GrammarError,
)

from backend.services.jd_intelligence import (
    analyze_job_description,
)

from backend.services.llm.quota import (
    FreeQuotaExceededError,
    require_free_quota_or_byok,
)


logger = logging.getLogger("ats_resume_scorer")


router = APIRouter(
    prefix="/api/v1",
    tags=["Analysis"],
)


# ================================================================
# SECURITY / VALIDATION CONSTANTS
# ================================================================

MAX_FILE_SIZE_BYTES = 5 * 1024 * 1024
MAX_JOB_DESCRIPTION_CHARS = 20_000

ALLOWED_RESUME_EXTENSIONS = {
    ".pdf",
    ".doc",
    ".docx",
}


# ================================================================
# HELPERS
# ================================================================

def _clean(text: str) -> str:
    for prefix in (
        "✅",
        "🌟",
        "❌",
        "⚠️",
        "📝",
        "🔴",
        "🟡",
        "🟢",
        "🟠",
        "👍",
    ):
        text = text.lstrip(prefix)

    return text.strip()


def _validate_resume_file(
    data: bytes,
    filename: str,
) -> None:
    """
    Validate resume extension, size and basic file signature.

    This is an initial validation layer.
    The actual resume parser must still validate
    the complete document structure.
    """

    if not data:
        raise HTTPException(
            status_code=422,
            detail="The uploaded resume is empty.",
        )

    extension = Path(filename).suffix.lower()

    # ------------------------------------------------------------
    # Extension validation
    # ------------------------------------------------------------

    if extension not in ALLOWED_RESUME_EXTENSIONS:
        raise HTTPException(
            status_code=415,
            detail=(
                "Unsupported resume file type. "
                "Upload a PDF, DOC, or DOCX file."
            ),
        )

    # ------------------------------------------------------------
    # Size validation
    # ------------------------------------------------------------

    if len(data) > MAX_FILE_SIZE_BYTES:
        raise HTTPException(
            status_code=413,
            detail=(
                "Resume file is too large. "
                "Maximum size is 5 MB."
            ),
        )

    # ------------------------------------------------------------
    # Basic file signature validation
    # ------------------------------------------------------------

    if extension == ".pdf":
        valid_signature = data.startswith(b"%PDF-")

    elif extension == ".docx":
        # DOCX is a ZIP-based Office document.
        valid_signature = data.startswith(b"PK\x03\x04")

    elif extension == ".doc":
        # Legacy Microsoft Office OLE compound document.
        valid_signature = data.startswith(
            b"\xd0\xcf\x11\xe0\xa1\xb1\x1a\xe1"
        )

    else:
        valid_signature = False

    if not valid_signature:
        raise HTTPException(
            status_code=422,
            detail=(
                "The uploaded file does not match "
                "its file type."
            ),
        )


# ================================================================
# ANALYZE RESUME
# ================================================================

@router.post(
    "/analyze-resume",
    response_model=AnalysisResponse,
)
async def analyze_resume(
    request: Request,
    resume: UploadFile = File(
        ...,
        description="Resume file — PDF, DOC, or DOCX, max 5 MB",
    ),
    job_description: str = Form(
        "",
        description="Job description text (optional)",
    ),
    provider: str = Form(
        "",
        description="Optional LLM provider override.",
    ),
    user_id: str = Depends(
        resume_analysis_rate_limit
    ),
):
    # ============================================================
    # PHASE 7B — FREE RESUME ANALYSIS QUOTA
    # ============================================================

    try:
        await require_free_quota_or_byok(
            user_id=user_id,
            feature="resume_analysis",
        )

    except FreeQuotaExceededError as exc:
        logger.info(
            "Resume analysis quota exhausted for user=%s",
            user_id,
        )

        raise HTTPException(
            status_code=403,
            detail={
                "code": "RESUME_FREE_QUOTA_EXCEEDED",
                "message": (
                    "You have used all 3 free resume analyses. "
                    "Connect your own AI provider API key "
                    "to continue analyzing resumes."
                ),
                "feature": "resume_analysis",
                "used": exc.used,
                "limit": exc.limit,
                "remaining": 0,
            },
        ) from exc

    except Exception as exc:
        logger.exception(
            "Resume analysis quota check failed."
        )

        raise HTTPException(
            status_code=500,
            detail=(
                "Could not verify resume analysis "
                "usage quota."
            ),
        ) from exc

    warnings: List[str] = []

    nlp = request.app.state.nlp
    embedder = request.app.state.embedder

    # ============================================================
    # STEP 0 — Validate Job Description
    # ============================================================

    job_description = job_description or ""

    if len(job_description) > MAX_JOB_DESCRIPTION_CHARS:
        raise HTTPException(
            status_code=413,
            detail=(
                "Job description is too long. "
                "Maximum length is 20,000 characters."
            ),
        )

    # ============================================================
    # STEP 1 — Read and parse uploaded resume
    # ============================================================

    try:
        filename = (resume.filename or "").strip()

        if not filename:
            raise HTTPException(
                status_code=422,
                detail="Please upload a resume file.",
            )

        extension = Path(filename).suffix.lower()

        if extension not in ALLOWED_RESUME_EXTENSIONS:
            raise HTTPException(
                status_code=415,
                detail=(
                    "Unsupported resume file type. "
                    "Upload a PDF, DOC, or DOCX file."
                ),
            )

        # --------------------------------------------------------
        # IMPORTANT:
        # Read only 5 MB + 1 byte.
        #
        # This prevents unnecessarily loading a huge upload
        # into memory.
        # --------------------------------------------------------

        file_bytes = await resume.read(
            MAX_FILE_SIZE_BYTES + 1
        )

        if len(file_bytes) > MAX_FILE_SIZE_BYTES:
            raise HTTPException(
                status_code=413,
                detail=(
                    "Resume file is too large. "
                    "Maximum size is 5 MB."
                ),
            )

        _validate_resume_file(
            file_bytes,
            filename,
        )

        from backend.services.resume_parser import (
            parse_resume_file,
        )

        resume_text, _metadata = parse_resume_file(
            file_bytes,
            filename,
        )

        logger.info(
            "Parsed '%s': %d chars extracted",
            filename,
            len(resume_text),
        )

    except HTTPException:
        # Preserve our intentional 4xx responses.
        raise

    except Exception as exc:
        logger.exception(
            "File parsing failed for uploaded resume"
        )

        # Only expose errors specifically designed to be
        # safe for end users.
        try:
            from backend.services.resume_parser import (
                ATSBaseError,
                FileValidationError,
            )
        except ImportError:
            ATSBaseError = ()
            FileValidationError = ()

        if isinstance(
            exc,
            (ATSBaseError, FileValidationError),
        ):
            raise HTTPException(
                status_code=422,
                detail=str(exc),
            ) from exc

        raise HTTPException(
            status_code=422,
            detail=(
                "The uploaded resume could not be "
                "processed."
            ),
        ) from exc

    # ============================================================
    # STEP 2 — Phase 3B
    # Structured Resume Profile
    # ============================================================

    try:
        from backend.services.resume_parser import (
            parse_resume_profile,
        )

        resume_profile = parse_resume_profile(
            resume_text
        )

        logger.info(
            "Structured resume profile created successfully"
        )

    except Exception:
        logger.exception(
            "Structured resume parsing failed"
        )

        # Do not expose internal exception details
        # through the API response.
        warnings.append(
            "Structured resume parsing could not be completed."
        )

        from backend.models.schemas import ResumeProfile

        resume_profile = ResumeProfile()

    # ============================================================
    # STEP 3 — Phase 3C
    # Resume Quality Analysis
    # ============================================================

    try:
        from backend.services.resume_quality_engine import (
            analyze_resume_quality,
        )

        resume_quality = analyze_resume_quality(
            resume_profile
        )

        logger.info(
            "Resume quality score: %s",
            resume_quality.overall_score,
        )

    except Exception:
        logger.exception(
            "Resume quality analysis failed"
        )

        warnings.append(
            "Resume quality analysis could not be completed."
        )

        from backend.models.schemas import ResumeQualityResult

        resume_quality = ResumeQualityResult(
            overall_score=0,
            contact_score=0,
            structure_score=0,
            experience_score=0,
            projects_score=0,
            skills_score=0,
            content_score=0,
        )

    # ============================================================
    # STEP 4 — Phase 3D
    # Advanced ATS Analysis
    # ============================================================

    advanced_ats = None

    # ============================================================
    # STEP 3E — Job Description Intelligence
    # ============================================================

    jd_intelligence = None

    if job_description.strip():

        try:
            jd_intelligence = analyze_job_description(
                job_description
            )

            logger.info(
                "Job Description Intelligence completed: "
                "role=%s, required_skills=%d, "
                "preferred_skills=%d",
                jd_intelligence.role_title,
                len(jd_intelligence.required_skills),
                len(jd_intelligence.preferred_skills),
            )

        except Exception:
            logger.exception(
                "Job Description Intelligence failed"
            )

            warnings.append(
                "Job Description Intelligence could not "
                "be completed."
            )

    else:
        # We can still calculate a resume-only advanced score.

        try:
            from backend.services.advanced_ats_engine import (
                calculate_advanced_ats_score,
            )

            advanced_ats = calculate_advanced_ats_score(
                resume_profile=resume_profile,
                job_description="",
                embedder=embedder,
                resume_quality_score=resume_quality.overall_score,
            )

        except Exception:
            logger.exception(
                "Resume-only advanced ATS failed"
            )

            warnings.append(
                "Advanced ATS analysis could not be completed."
            )

    # ============================================================
    # STEP 5 — Existing SmartHire analysis
    #
    # KEEPING EXISTING FUNCTIONALITY
    # ============================================================

    try:
        from backend.services.resume_analyzer import (
            analyze_full_resume,
        )

        result = await analyze_full_resume(
            resume_text=resume_text,
            nlp=nlp,
            embedder=embedder,
            job_description=job_description,
            user_id=user_id,
            provider=provider.strip() or None,
        )

    except Exception:
        logger.exception(
            "Full analysis pipeline failed"
        )

        raise HTTPException(
            status_code=500,
            detail=(
                "SmartHire could not complete the "
                "analysis right now. Please try again "
                "in a few moments."
            ),
        )
            # ============================================================
    # STEP 5.5 — Grammar & Spelling Analysis
    # ============================================================

    grammar_raw = (
        result.get("grammar_analysis")
        or result.get("grammar_results")
        or result.get("grammar")
        or {}
    )

    # ------------------------------------------------------------
    # Convert Pydantic model → dictionary if necessary
    # ------------------------------------------------------------

    if hasattr(grammar_raw, "model_dump"):
        grammar_raw = grammar_raw.model_dump()

    if not isinstance(grammar_raw, dict):
        logger.warning(
            "Grammar result has unexpected type: %s",
            type(grammar_raw).__name__,
        )

        grammar_raw = {}

    # ------------------------------------------------------------
    # Safely normalize error lists
    # ------------------------------------------------------------

    critical_errors_raw = (
        grammar_raw.get("critical_errors", [])
        or []
    )

    moderate_errors_raw = (
        grammar_raw.get("moderate_errors", [])
        or []
    )

    minor_errors_raw = (
        grammar_raw.get("minor_errors", [])
        or []
    )

    # ------------------------------------------------------------
    # Convert individual grammar errors
    # ------------------------------------------------------------

    def _build_grammar_errors(errors):

        normalized = []

        for error in errors:

            if hasattr(error, "model_dump"):
                error = error.model_dump()

            if not isinstance(error, dict):
                continue

            normalized.append(
                GrammarError(
                    error_text=str(
                        error.get(
                            "error_text",
                            "",
                        )
                    ),

                    suggestions=list(
                        error.get(
                            "suggestions",
                            [],
                        )
                        or []
                    )[:5],

                    message=str(
                        error.get(
                            "message",
                            "",
                        )
                    ),

                    rule_id=str(
                        error.get(
                            "rule_id",
                            "",
                        )
                    ),

                    category=str(
                        error.get(
                            "category",
                            "",
                        )
                    ),

                    issue_type=str(
                        error.get(
                            "issue_type",
                            "",
                        )
                    ),

                    offset=int(
                        error.get(
                            "offset",
                            0,
                        )
                        or 0
                    ),

                    length=int(
                        error.get(
                            "length",
                            0,
                        )
                        or 0
                    ),

                    severity=str(
                        error.get(
                            "severity",
                            "minor",
                        )
                    ),
                )
            )

        return normalized

    critical_errors = _build_grammar_errors(
        critical_errors_raw
    )

    moderate_errors = _build_grammar_errors(
        moderate_errors_raw
    )

    minor_errors = _build_grammar_errors(
        minor_errors_raw
    )

    # ------------------------------------------------------------
    # Build final GrammarAnalysis object
    # ------------------------------------------------------------

    grammar_analysis_result = GrammarAnalysis(

        total_errors=int(
            grammar_raw.get(
                "total_errors",
                len(critical_errors)
                + len(moderate_errors)
                + len(minor_errors),
            )
            or 0
        ),

        critical_errors=critical_errors,

        moderate_errors=moderate_errors,

        minor_errors=minor_errors,

        grammar_score=(
            float(
                grammar_raw["grammar_score"]
            )
            if grammar_raw.get(
                "grammar_score"
            ) is not None
            else None
        ),

        penalty_applied=float(
            grammar_raw.get(
                "penalty_applied",
                0.0,
            )
            or 0.0
        ),

        error_free_percentage=(
            float(
                grammar_raw[
                    "error_free_percentage"
                ]
            )
            if grammar_raw.get(
                "error_free_percentage"
            ) is not None
            else None
        ),

        component_status=grammar_raw.get(
            "_component_status",
            grammar_raw.get(
                "component_status",
                None,
            ),
        ),

        note=grammar_raw.get(
            "_note",
            grammar_raw.get(
                "note",
                None,
            ),
        ),
    )

    # ------------------------------------------------------------
    # Grammar debug logging
    # ------------------------------------------------------------

    logger.info(
        "========== API GRAMMAR RESPONSE =========="
    )

    logger.info(
        "GRAMMAR API STATUS: %s",
        grammar_analysis_result.component_status,
    )

    logger.info(
        "GRAMMAR API TOTAL: %s",
        grammar_analysis_result.total_errors,
    )

    logger.info(
        "GRAMMAR API CRITICAL: %s",
        len(
            grammar_analysis_result.critical_errors
        ),
    )

    logger.info(
        "GRAMMAR API MODERATE: %s",
        len(
            grammar_analysis_result.moderate_errors
        ),
    )

    logger.info(
        "GRAMMAR API MINOR: %s",
        len(
            grammar_analysis_result.minor_errors
        ),
    )

    logger.info(
        "GRAMMAR API SCORE: %s",
        grammar_analysis_result.grammar_score,
    )

    logger.info(
        "=========================================="
    )

    # ============================================================
    # STEP 6 — Existing JD comparison
    # ============================================================

    jd_comparison_result = None

    if result.get("jd_comparison"):

        jd_comparison_result = JDComparison(
            match_percentage=round(
                float(
                    result["jd_comparison"].get(
                        "match_percentage",
                        0.0,
                    )
                ),
                1,
            ),

            semantic_similarity=round(
                float(
                    result["jd_comparison"].get(
                        "semantic_similarity",
                        0.0,
                    )
                ),
                3,
            ),

            matched_keywords=result[
                "jd_comparison"
            ].get(
                "matched_keywords",
                [],
            )[:20],

            missing_keywords=result[
                "jd_comparison"
            ].get(
                "missing_keywords",
                [],
            )[:15],

            skills_gap=result[
                "jd_comparison"
            ].get(
                "skills_gap",
                [],
            )[:10],
        )

    # ============================================================
    # STEP 7 — Existing skill validation
    # ============================================================

    detailed_fb = result.get(
        "detailed_feedback",
        [],
    )

    svd_raw = (
        result.get(
            "skill_validation_details"
        )
        or {}
    )

    skill_val_details = SkillValidationDetails(
        validated=svd_raw.get(
            "validated",
            [],
        ),

        unvalidated=svd_raw.get(
            "unvalidated",
            [],
        ),

        total=svd_raw.get(
            "total",
            0,
        ),

        validated_count=svd_raw.get(
            "validated_count",
            0,
        ),

        validation_pct=svd_raw.get(
            "validation_pct",
            0.0,
        ),
    )

    # ============================================================
    # STEP 8 — Determine final ATS score
    # ============================================================

    final_ats_score = result["ats_score"]

    if advanced_ats is not None:
        final_ats_score = advanced_ats.ats_score

    # ============================================================
    # STEP 9 — Determine JD match
    # ============================================================

    final_jd_match = 0.0

    if advanced_ats is not None:
        final_jd_match = float(
            advanced_ats.jd_match
        )

    elif jd_comparison_result is not None:
        final_jd_match = (
            jd_comparison_result.match_percentage
        )

    # ============================================================
    # STEP 10 — Build response
    # ============================================================

    response = AnalysisResponse(

        # --------------------------------------------------------
        # Main score
        # --------------------------------------------------------

        ATS_score=final_ats_score,

        ats_score=final_ats_score,

        # --------------------------------------------------------
        # Existing component scores
        # --------------------------------------------------------

        component_scores=ComponentScores(
            **result["component_scores"]
        ),

        # --------------------------------------------------------
        # Existing analysis
        # --------------------------------------------------------

        issues_summary=result[
            "issues_summary"
        ],

        detailed_feedback=detailed_fb,

        jd_match_analysis=jd_comparison_result,

        skill_validation_details=skill_val_details,

        # --------------------------------------------------------
        # Grammar & Spelling Analysis
        # --------------------------------------------------------

        grammar_analysis=grammar_analysis_result,

        # Backward-compatible alias
        grammar_results=grammar_analysis_result,

        # --------------------------------------------------------
        # Existing compatibility fields
        # --------------------------------------------------------

        # --------------------------------------------------------
        # Existing compatibility fields
        # --------------------------------------------------------

        keyword_match=(
            advanced_ats.score_breakdown.keyword_match
            if advanced_ats
            else (
                jd_comparison_result.match_percentage
                if jd_comparison_result
                else 0.0
            )
        ),

        missing_keywords=(
            advanced_ats.keyword_analysis.missing_keywords
            if advanced_ats
            else result.get(
                "missing_keywords",
                [],
            )
        ),

        matched_keywords=(
            advanced_ats.keyword_analysis.matched_keywords
            if advanced_ats
            else result.get(
                "matched_keywords",
                [],
            )
        ),

        skills=list(
            result.get(
                "skills",
                [],
            )[:20]
        ),

        jd_comparison=jd_comparison_result,

        interpretation=result.get(
            "interpretation",
            "",
        ),

        # --------------------------------------------------------
        # Phase 3D
        # --------------------------------------------------------

        advanced_ats=advanced_ats,

        resume_quality=resume_quality,

        resume_profile=resume_profile,

        warnings=warnings,
    )

    # ============================================================
    # STEP 11 — Save history
    # ============================================================

    try:
        from backend.database.supabase_db import (
            save_analysis,
        )

        # Start with the existing result so old history
        # continues to work.

        history_result = dict(result)

        # ========================================================
        # Preserve Grammar & Spelling Analysis
        # ========================================================

        history_result[
            "grammar_analysis"
        ] = grammar_analysis_result.model_dump()

        # Backward-compatible alias
        history_result[
            "grammar_results"
        ] = grammar_analysis_result.model_dump()

        # ========================================================
        # Add Phase 3B/3C/3D information
        # ========================================================

        history_result[
            "resume_profile"
        ] = resume_profile.model_dump()

        history_result[
            "resume_quality"
        ] = resume_quality.model_dump()

        if advanced_ats is not None:
            history_result[
                "advanced_ats"
            ] = advanced_ats.model_dump()

        history_result[
            "final_ats_score"
        ] = final_ats_score

        history_result[
            "final_jd_match"
        ] = final_jd_match

        if jd_intelligence is not None:
            history_result[
                "jd_intelligence"
            ] = jd_intelligence.model_dump()

        analysis_id = await save_analysis(
            user_id,
            filename,
            history_result,
        )

        # ========================================================
        # PHASE 2.2 — RESUME RAG INDEXING
        # ========================================================

        try:
            from backend.services.rag.resume_rag import (
                index_resume,
            )

            rag_result = await index_resume(
                user_id=user_id,
                resume_name=filename,
                resume_profile=resume_profile.model_dump(),
                embedder=embedder,
                source_analysis_id=analysis_id,
            )

            logger.info(
                "Phase 2.2 Resume RAG indexing completed: %s",
                rag_result,
            )

        except Exception:
            logger.exception(
                "Phase 2.2 Resume RAG indexing failed "
                "(non-blocking)"
            )

            warnings.append(
                "Resume semantic indexing could not "
                "be completed."
            )

    except Exception as exc:
        logger.warning(
            "History save failed (non-blocking): %s",
            exc,
        )

    return response


# ================================================================
# HEALTH
# ================================================================

@router.get("/health")
async def health_check(request: Request):
    return {
        "status": "healthy",

        "nlp_loaded":
            request.app.state.nlp is not None,

        "embedder_loaded":
            request.app.state.embedder is not None,
    }


# ================================================================
# HISTORY
# ================================================================

@router.get("/history")
async def get_history(
    user_id: str = Depends(get_current_user),
):
    from backend.database.supabase_db import (
        get_user_history,
    )

    try:
        return await get_user_history(user_id)

    except Exception:
        logger.exception(
            "History fetch failed"
        )

        raise HTTPException(
            status_code=500,
            detail=(
                "SmartHire could not load your history "
                "right now. Please try again in a few "
                "moments."
            ),
        )


@router.delete("/history/{analysis_id}")
async def delete_history_entry(
    analysis_id: str,
    user_id: str = Depends(get_current_user),
):
    from backend.database.supabase_db import (
        delete_analysis,
    )

    try:
        success = await delete_analysis(
            analysis_id,
            user_id,
        )

        if not success:
            raise HTTPException(
                status_code=404,
                detail=(
                    "Analysis not found or not owned "
                    "by this user."
                ),
            )

        return {
            "status": "deleted",
            "id": analysis_id,
        }

    except HTTPException:
        raise

    except Exception:
        logger.exception(
            "History delete failed"
        )

        raise HTTPException(
            status_code=500,
            detail=(
                "SmartHire could not delete this "
                "history item right now. Please try "
                "again in a few moments."
            ),
        )


# ================================================================
# PDF
# ================================================================

@router.post("/generate-pdf")
async def generate_pdf(
    data: AnalysisResponse,
    user_id: str = Depends(
        pdf_rate_limit
    ),
):
    from backend.services.report_generator import (
        generate_html_reports,
    )

    from backend.services.pdf_export import (
        generate_combined_pdf,
    )

    from fastapi.responses import Response

    try:
        html_docs = generate_html_reports(
            data.model_dump()
        )

        pdf_bytes = await asyncio.to_thread(
            generate_combined_pdf,
            html_docs,
        )

        return Response(
            content=pdf_bytes,
            media_type="application/pdf",
            headers={
                "Content-Disposition":
                    "attachment; filename=ats_report.pdf"
            },
        )

    except Exception:
        logger.exception(
            "Failed to generate PDF"
        )

        raise HTTPException(
            status_code=500,
            detail=(
                "SmartHire could not generate the PDF "
                "right now. Please try again in a few "
                "moments."
            ),
        )


@router.get("/history/{analysis_id}/pdf")
async def generate_history_pdf(
    analysis_id: str,
    user_id: str = Depends(
        history_pdf_rate_limit
    ),
):
    from backend.database.supabase_db import (
        get_user_history,
    )

    from backend.services.report_generator import (
        generate_html_reports,
    )

    from backend.services.pdf_export import (
        generate_combined_pdf,
    )

    from fastapi.responses import Response

    history = await get_user_history(
        user_id
    )

    analysis_data = next(
        (
            item["analysis_result"]
            for item in history
            if item["id"] == analysis_id
        ),
        None,
    )

    if not analysis_data:
        raise HTTPException(
            status_code=404,
            detail="Analysis not found",
        )

    try:
        html_docs = generate_html_reports(
            analysis_data
        )

        pdf_bytes = await asyncio.to_thread(
            generate_combined_pdf,
            html_docs,
        )

        return Response(
            content=pdf_bytes,
            media_type="application/pdf",
            headers={
                "Content-Disposition":
                    f"attachment; "
                    f"filename=ats_report_{analysis_id}.pdf"
            },
        )

    except Exception:
        logger.exception(
            "Failed to generate PDF for history"
        )

        raise HTTPException(
            status_code=500,
            detail=(
                "SmartHire could not generate the "
                "history PDF right now. Please try "
                "again in a few moments."
            ),
        )