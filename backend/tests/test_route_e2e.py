import asyncio, sys, threading, time, types, socket
import pathlib; sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[2]))
sys.modules.setdefault("spacy", types.SimpleNamespace(Language=object, load=lambda *a, **k: None))

import httpx, uvicorn
from fastapi import FastAPI
import backend.api.routes as routes
from backend.models.schemas import ResumeProfile, ResumeQualityResult

EVENTS = {}

def make_fake_modules():
    rp = types.ModuleType("backend.services.resume_parser")
    rp.parse_resume_file = lambda b, f: ("resume text " * 20, {})
    rp.parse_resume_profile = lambda t: ResumeProfile()
    class ATSBaseError(Exception): ...
    class FileValidationError(Exception): ...
    rp.ATSBaseError, rp.FileValidationError = ATSBaseError, FileValidationError
    sys.modules["backend.services.resume_parser"] = rp

    rq = types.ModuleType("backend.services.resume_quality_engine")
    rq.analyze_resume_quality = lambda p: ResumeQualityResult(
        overall_score=75, contact_score=1, structure_score=1, experience_score=1,
        projects_score=1, skills_score=1, content_score=1)
    sys.modules["backend.services.resume_quality_engine"] = rq

    an = types.ModuleType("backend.services.resume_analyzer")
    async def analyze_full_resume(**kw):
        EVENTS["analyze_redis"] = kw.get("redis", "MISSING")
        return {"ats_score": 70, "component_scores": {"formatting": 1, "keywords": 1, "content": 1,
                "skill_validation": 1, "ats_compatibility": 1},
                "issues_summary": [],
                "detailed_feedback": [], "skill_validation_details": {}, "skills": ["python"],
                "jd_comparison": None, "interpretation": "ok", "missing_keywords": [], "matched_keywords": []}
    an.analyze_full_resume = analyze_full_resume
    sys.modules["backend.services.resume_analyzer"] = an

    rag = types.ModuleType("backend.services.rag.resume_rag")
    async def index_resume(**kw):
        await asyncio.sleep(0.8)
        EVENTS["rag_done"] = time.perf_counter()
        EVENTS["rag_analysis_id"] = kw["source_analysis_id"]
        return {"ok": True}
    rag.index_resume = index_resume
    sys.modules["backend.services.rag.resume_rag"] = rag

    import backend.database.supabase_db as db
    async def save_analysis(user_id, filename, result):
        await asyncio.sleep(0.8)
        EVENTS["save_done"] = time.perf_counter()
        EVENTS["saved_keys"] = set(result)
        return "analysis-123"
    db.save_analysis = save_analysis

def start_server():
    make_fake_modules()
    async def no_quota(**kw): return None
    routes.require_free_quota_or_byok = no_quota
    app = FastAPI()
    app.include_router(routes.router)
    app.dependency_overrides[routes.resume_analysis_rate_limit] = lambda: "user-1"
    app.state.nlp = None; app.state.embedder = object(); app.state.redis = "REDIS-SENTINEL"
    s = socket.socket(); s.bind(("127.0.0.1", 0)); port = s.getsockname()[1]; s.close()
    server = uvicorn.Server(uvicorn.Config(app, host="127.0.0.1", port=port, log_level="error"))
    th = threading.Thread(target=server.run, daemon=True); th.start()
    for _ in range(100):
        if server.started: break
        time.sleep(0.05)
    return server, port

def test_response_returns_before_persistence_and_persists_after():
    server, port = start_server()
    try:
        pdf = b"%PDF-1.4 fake pdf content " * 10
        t0 = time.perf_counter()
        r = httpx.post(f"http://127.0.0.1:{port}/api/v1/analyze-resume" if False else f"http://127.0.0.1:{port}{routes.router.prefix}/analyze-resume",
                       files={"resume": ("cv.pdf", pdf, "application/pdf")},
                       data={"job_description": ""}, timeout=30)
        response_time = time.perf_counter() - t0
        assert r.status_code == 200, r.text
        body = r.json()
        assert isinstance(body["ats_score"], (int, float)) and body["ats_score"] > 0

        # client got its answer well before the 0.8s + 0.8s of persistence work
        assert response_time < 0.7, f"response took {response_time:.2f}s"
        assert "save_done" not in EVENTS, "save should not have finished before the response"

        # ...but persistence still happens, in order, with the right analysis id
        for _ in range(60):
            if "rag_done" in EVENTS: break
            time.sleep(0.1)
        assert "rag_done" in EVENTS and "save_done" in EVENTS
        assert EVENTS["save_done"] < EVENTS["rag_done"]
        assert EVENTS["rag_analysis_id"] == "analysis-123"
        assert {"resume_profile", "resume_quality", "final_ats_score", "final_jd_match"} <= EVENTS["saved_keys"]
        assert EVENTS["analyze_redis"] == "REDIS-SENTINEL"
        print(f"\nclient-visible response time: {response_time:.2f}s (persistence ~1.6s now happens afterwards)")
    finally:
        server.should_exit = True
