from backend.services.jobs.career_profile_builder import (
    build_career_profile,
)


# ============================================================
# TECHNICAL PROFILE
# ============================================================


def test_backend_engineer_profile():

    profile = build_career_profile(
        resume_text="""
        Computer Science graduate.

        Backend Engineer Intern.

        Built REST APIs using Python, FastAPI, PostgreSQL and Docker.

        Projects:
        SmartHire ATS
        CodeGuardian AI

        Education:
        B.Tech in Computer Science and Engineering.
        """,
        resume_skills=[
            "Python",
            "FastAPI",
            "PostgreSQL",
            "Docker",
        ],
        target_roles=[
            "Backend Engineer",
        ],
    )

    assert profile.domain == "technology"
    assert profile.role_family == "backend"
    assert profile.primary_role == "Backend Engineer"

    assert profile.experience_level == "intern"

    assert "Python" in profile.skills
    assert "FastAPI" in profile.skills
    assert "PostgreSQL" in profile.skills
    assert "Docker" in profile.skills

    assert "Backend Engineer" in profile.target_roles
    assert "Software Engineer" in profile.compatible_roles

    assert profile.confidence > 0


# ============================================================
# AI/ML PROFILE
# ============================================================


def test_ai_ml_profile():

    profile = build_career_profile(
        resume_text="""
        Machine Learning Engineer.

        Developed machine learning and NLP applications
        using Python, TensorFlow, pandas and scikit-learn.

        B.Tech Computer Science.
        """,
        resume_skills=[
            "Python",
            "Machine Learning",
            "TensorFlow",
            "Pandas",
            "Scikit-learn",
        ],
        target_roles=[
            "AI Engineer",
        ],
    )

    assert profile.domain == "technology"
    assert profile.role_family == "ai_ml"

    assert profile.primary_role == "AI/ML Engineer"

    assert "Python" in profile.skills
    assert "Machine Learning" in profile.skills
    assert "TensorFlow" in profile.skills


# ============================================================
# SKILL NORMALIZATION
# ============================================================


def test_skill_normalization():

    profile = build_career_profile(
        resume_text="""
        Full Stack Developer with experience in
        Node.js, React.js, MongoDB and JavaScript.
        """,
        resume_skills=[
            "nodejs",
            "react",
            "mongodb",
        ],
        target_roles=[
            "Full Stack Developer",
        ],
    )

    assert "Node.js" in profile.skills
    assert "React" in profile.skills
    assert "MongoDB" in profile.skills
    assert "JavaScript" in profile.skills


# ============================================================
# EXPERIENCE LEVEL
# ============================================================


def test_fresher_profile():

    profile = build_career_profile(
        resume_text="""
        Recent graduate looking for an entry-level
        software engineering position.

        B.Tech in Computer Science.
        """,
        target_roles=[
            "Software Engineer",
        ],
    )

    assert profile.experience_level == "fresher"


def test_mid_level_profile():

    profile = build_career_profile(
        resume_text="""
        Software Engineer with 3 years of experience
        building backend applications.
        """,
        target_roles=[
            "Backend Engineer",
        ],
    )

    assert profile.experience_level == "mid"


def test_senior_profile():

    profile = build_career_profile(
        resume_text="""
        Senior Software Engineer with 7 years of experience
        building distributed backend systems.
        """,
        target_roles=[
            "Software Engineer",
        ],
    )

    assert profile.experience_level == "senior"


# ============================================================
# TARGET ROLES
# ============================================================


def test_target_roles_are_prioritized():

    profile = build_career_profile(
        resume_text="""
        Software Engineer with Python and React experience.
        """,
        target_roles=[
            "AI Engineer",
            "Backend Engineer",
        ],
    )

    assert profile.target_roles == [
        "AI Engineer",
        "Backend Engineer",
    ]

    assert profile.compatible_roles[0] == "AI Engineer"
    assert profile.compatible_roles[1] == "Backend Engineer"


# ============================================================
# PROJECT EXTRACTION
# ============================================================


def test_project_extraction():

    profile = build_career_profile(
        resume_text="""
        Computer Science graduate.

        Projects

        SmartHire ATS
        AI Resume Screening System

        CodeGuardian AI
        AI powered GitHub code review platform

        Education

        B.Tech Computer Science
        """,
        target_roles=[
            "AI Engineer",
        ],
    )

    assert len(profile.projects) >= 2

    assert any(
        "SmartHire ATS" in project
        for project in profile.projects
    )


# ============================================================
# SERIALIZATION
# ============================================================


def test_profile_to_dict():

    profile = build_career_profile(
        resume_text="""
        Backend Developer using Python and FastAPI.
        """,
        target_roles=[
            "Backend Engineer",
        ],
    )

    data = profile.to_dict()

    assert isinstance(data, dict)

    assert data["domain"] == profile.domain
    assert data["primary_role"] == profile.primary_role
    assert data["role_family"] == profile.role_family
    assert data["skills"] == profile.skills
    assert data["target_roles"] == profile.target_roles