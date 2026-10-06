from datetime import datetime

from typing import Any, Dict, List, Optional

from pydantic import BaseModel, Field


# ============================================================
# COMPONENT SCORES
# ============================================================

class ComponentScores(BaseModel):
    formatting: float
    keywords: float
    content: float
    skill_validation: float
    ats_compatibility: float


# ============================================================
# JD COMPARISON
# ============================================================

class JDComparison(BaseModel):
    match_percentage: float
    semantic_similarity: float
    matched_keywords: List[str]
    missing_keywords: List[str]
    skills_gap: List[str]


# ============================================================
# SKILL VALIDATION
# ============================================================

class SkillValidationDetails(BaseModel):
    validated: List[Dict[str, Any]] = Field(
        default_factory=list
    )

    unvalidated: List[str] = Field(
        default_factory=list
    )

    total: int = 0
    validated_count: int = 0
    validation_pct: float = 0.0


# ============================================================
# ISSUE DETAILS
# ============================================================

class IssueDetail(BaseModel):
    issue_title: str
    severity_level: str
    ats_impact: str
    explanation: str
    where_it_appears: str
    how_to_fix: str

    action_items: List[str] = Field(
        default_factory=list
    )

    example_improvement: str



# ============================================================
# RESUME CONTACT
# ============================================================

class ResumeContact(BaseModel):
    name: Optional[str] = None
    email: Optional[str] = None
    phone: Optional[str] = None
    linkedin: Optional[str] = None
    github: Optional[str] = None
    portfolio: Optional[str] = None


# ============================================================
# RESUME EDUCATION
# ============================================================

class ResumeEducation(BaseModel):
    institution: Optional[str] = None
    degree: Optional[str] = None
    field_of_study: Optional[str] = None
    location: Optional[str] = None
    start_date: Optional[str] = None
    end_date: Optional[str] = None
    grade: Optional[str] = None


# ============================================================
# RESUME EXPERIENCE
# ============================================================

class ResumeExperience(BaseModel):
    company: Optional[str] = None
    role: Optional[str] = None
    location: Optional[str] = None
    start_date: Optional[str] = None
    end_date: Optional[str] = None

    bullets: List[str] = Field(
        default_factory=list
    )


# ============================================================
# RESUME PROJECT
# ============================================================

class ResumeProject(BaseModel):
    name: Optional[str] = None

    technologies: List[str] = Field(
        default_factory=list
    )

    description: Optional[str] = None

    bullets: List[str] = Field(
        default_factory=list
    )

    url: Optional[str] = None


# ============================================================
# RESUME CERTIFICATION
# ============================================================

class ResumeCertification(BaseModel):
    name: Optional[str] = None
    issuer: Optional[str] = None
    date: Optional[str] = None
    url: Optional[str] = None


# ============================================================
# RESUME ACHIEVEMENT
# ============================================================

class ResumeAchievement(BaseModel):
    title: Optional[str] = None
    description: Optional[str] = None
    date: Optional[str] = None


# ============================================================
# RESUME PROFILE
# ============================================================

class ResumeProfile(BaseModel):
    contact: ResumeContact = Field(
        default_factory=ResumeContact
    )

    summary: Optional[str] = None

    education: List[ResumeEducation] = Field(
        default_factory=list
    )

    experience: List[ResumeExperience] = Field(
        default_factory=list
    )

    projects: List[ResumeProject] = Field(
        default_factory=list
    )

    skills: List[str] = Field(
        default_factory=list
    )

    certifications: List[ResumeCertification] = Field(
        default_factory=list
    )

    achievements: List[ResumeAchievement] = Field(
        default_factory=list
    )


# ============================================================
# RESUME QUALITY
# ============================================================

class ResumeQualityFinding(BaseModel):
    category: str
    severity: str
    message: str


class ResumeQualityResult(BaseModel):
    overall_score: int

    contact_score: int
    structure_score: int
    experience_score: int
    projects_score: int
    skills_score: int
    content_score: int

    strengths: List[str] = Field(
        default_factory=list
    )

    weaknesses: List[str] = Field(
        default_factory=list
    )

    recommendations: List[str] = Field(
        default_factory=list
    )

    findings: List[ResumeQualityFinding] = Field(
        default_factory=list
    )

    metrics_count: int = 0

    bullet_count: int = 0

    quantified_bullet_count: int = 0


# ============================================================
# ATS KEYWORD ANALYSIS
# ============================================================

class ATSKeywordAnalysis(BaseModel):
    required_keywords: List[str] = Field(
        default_factory=list
    )

    matched_keywords: List[str] = Field(
        default_factory=list
    )

    missing_keywords: List[str] = Field(
        default_factory=list
    )

    total_keywords: int = 0

    match_percentage: int = 0


# ============================================================
# ATS SCORE BREAKDOWN
# ============================================================

class ATSScoreBreakdown(BaseModel):
    keyword_match: int = 0
    semantic_match: int = 0
    skills_match: int = 0
    experience_match: int = 0
    project_match: int = 0
    resume_quality: int = 0


# ============================================================
# ADVANCED ATS RESULT
# ============================================================

class AdvancedATSResult(BaseModel):
    ats_score: int

    jd_match: int

    score_breakdown: ATSScoreBreakdown

    keyword_analysis: ATSKeywordAnalysis

    matched_skills: List[str] = Field(
        default_factory=list
    )

    missing_skills: List[str] = Field(
        default_factory=list
    )

    matched_experience_terms: List[str] = Field(
        default_factory=list
    )

    matched_project_terms: List[str] = Field(
        default_factory=list
    )

    explanation: List[str] = Field(
        default_factory=list
    )


# ============================================================
# JD REQUIREMENTS
# ============================================================

class JDRequirement(BaseModel):
    requirement: str
    category: str
    priority: str
    evidence: Optional[str] = None


class JDExperienceRequirement(BaseModel):
    minimum_years: Optional[float] = None
    maximum_years: Optional[float] = None
    raw_text: Optional[str] = None


# ============================================================
# JD INTELLIGENCE
# ============================================================

class JDIntelligenceResult(BaseModel):
    job_title: Optional[str] = None

    seniority: Optional[str] = None

    domain: Optional[str] = None

    required_skills: List[str] = Field(
        default_factory=list
    )

    preferred_skills: List[str] = Field(
        default_factory=list
    )

    responsibilities: List[str] = Field(
        default_factory=list
    )

    experience_requirement: JDExperienceRequirement = Field(
        default_factory=JDExperienceRequirement
    )

    education_requirements: List[str] = Field(
        default_factory=list
    )

    technical_requirements: List[JDRequirement] = Field(
        default_factory=list
    )

    soft_skill_requirements: List[JDRequirement] = Field(
        default_factory=list
    )

    keywords: List[str] = Field(
        default_factory=list
    )

    must_have_count: int = 0

    preferred_count: int = 0

    jd_quality_score: int = 0

    strengths: List[str] = Field(
        default_factory=list
    )

    weaknesses: List[str] = Field(
        default_factory=list
    )

class AnalysisResponse(BaseModel):

    # ========================================================
    # Existing response fields
    # ========================================================

    ATS_score: float

    component_scores: ComponentScores

    issues_summary: List[str]

    detailed_feedback: List[IssueDetail]

    jd_match_analysis: Optional[JDComparison] = None

    skill_validation_details: Optional[
        SkillValidationDetails
    ] = None


    # ========================================================
    # Backward compatibility
    # ========================================================

    ats_score: float

    keyword_match: float = 0.0

    missing_keywords: List[str] = Field(
        default_factory=list
    )

    matched_keywords: List[str] = Field(
        default_factory=list
    )

    suggestions: List[str] = Field(
        default_factory=list
    )

    strengths: List[str] = Field(
        default_factory=list
    )

    critical_issues: List[str] = Field(
        default_factory=list
    )

    skills: List[str] = Field(
        default_factory=list
    )

    jd_comparison: Optional[JDComparison] = None

    warnings: List[str] = Field(
        default_factory=list
    )

    interpretation: str = ""

    # ========================================================
    # Phase 3D — Advanced ATS
    # ========================================================

    advanced_ats: Optional[AdvancedATSResult] = None

    resume_quality: Optional[ResumeQualityResult] = None

    resume_profile: Optional[ResumeProfile] = None

    jd_intelligence: Optional[
        JDIntelligenceResult
    ] = None


# ============================================================
# CAREER PROFILE
# ============================================================

class CareerProfile(BaseModel):
    username: str

    career_interests: List[str] = Field(
        default_factory=list
    )

    specializations: List[str] = Field(
        default_factory=list
    )

    skills: List[str] = Field(
        default_factory=list
    )

    target_roles: List[str] = Field(
        default_factory=list
    )

    experience: str = ""

    graduation_year: Optional[int] = None

    resume_filename: Optional[str] = None

    onboarding_step: int = 1

    onboarding_completed: bool = False


# ============================================================
# CAREER PROFILE UPDATE
# ============================================================

class CareerProfileUpdate(BaseModel):
    username: str

    career_interests: List[str] = Field(
        default_factory=list
    )

    specializations: List[str] = Field(
        default_factory=list
    )

    skills: List[str] = Field(
        default_factory=list
    )

    target_roles: List[str] = Field(
        default_factory=list
    )

    experience: str = ""

    graduation_year: Optional[int] = None


# ============================================================
# ONBOARDING PROGRESS
# ============================================================

class OnboardingProgressUpdate(BaseModel):
    step: int

    username: Optional[str] = None

    career_interests: Optional[List[str]] = None

    specializations: Optional[List[str]] = None

    skills: Optional[List[str]] = None

    target_roles: Optional[List[str]] = None

    experience: Optional[str] = None

    graduation_year: Optional[int] = None


# ============================================================
# CAREER PROFILE RESPONSE
# ============================================================

class CareerProfileResponse(BaseModel):
    user_id: str

    username: str

    career_interests: List[str] = Field(
        default_factory=list
    )

    specializations: List[str] = Field(
        default_factory=list
    )

    skills: List[str] = Field(
        default_factory=list
    )

    target_roles: List[str] = Field(
        default_factory=list
    )

    experience: str = ""

    graduation_year: Optional[int] = None

    resume_filename: Optional[str] = None

    onboarding_step: int = 1

    onboarding_completed: bool = False


# ============================================================
# PHASE 3 JD EXPERIENCE REQUIREMENT
# ============================================================

class JDExperienceRequirement(BaseModel):
    required: bool = False

    minimum_years: Optional[float] = None

    maximum_years: Optional[float] = None

    raw_text: Optional[str] = None


# ============================================================
# PHASE 3 JD EDUCATION REQUIREMENT
# ============================================================

class JDEducationRequirement(BaseModel):
    required: bool = False

    degrees: List[str] = Field(
        default_factory=list
    )

    fields: List[str] = Field(
        default_factory=list
    )

    raw_text: Optional[str] = None


# ============================================================
# PHASE 3 JD INTELLIGENCE
# ============================================================

class JDIntelligenceResult(BaseModel):
    role_title: Optional[str] = None

    required_skills: List[str] = Field(
        default_factory=list
    )

    preferred_skills: List[str] = Field(
        default_factory=list
    )

    technical_concepts: List[str] = Field(
        default_factory=list
    )

    experience: JDExperienceRequirement = Field(
        default_factory=JDExperienceRequirement
    )

    education: JDEducationRequirement = Field(
        default_factory=JDEducationRequirement
    )

    responsibilities: List[str] = Field(
        default_factory=list
    )

    role_signals: List[str] = Field(
        default_factory=list
    )

    required_keywords: List[str] = Field(
        default_factory=list
    )

    preferred_keywords: List[str] = Field(
        default_factory=list
    )

    total_required_items: int = 0

    total_preferred_items: int = 0


# ============================================================
# RECOMMENDATION ITEM
# ============================================================

class RecommendationItem(BaseModel):
    priority: str

    category: str

    title: str

    recommendation: str

    reason: str

    evidence: List[str] = Field(
        default_factory=list
    )

    action: str

    estimated_impact: str


# ============================================================
# AI RECOMMENDATIONS
# ============================================================

class AIRecommendationResult(BaseModel):
    summary: str

    recommendations: List[RecommendationItem] = Field(
        default_factory=list
    )

    strengths: List[str] = Field(
        default_factory=list
    )

    top_missing_skills: List[str] = Field(
        default_factory=list
    )

    total_recommendations: int = 0