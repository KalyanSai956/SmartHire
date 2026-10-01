from backend.services.jobs.job_classifier import (
    AI_CATEGORY,
    DATA_CATEGORY,
    ENGINEERING_CATEGORY,
    INFRASTRUCTURE_CATEGORY,
    classify_experience,
    classify_job,
    extract_preferred_skills,
    extract_required_skills,
)


# ============================================================
# BACKEND
# ============================================================


def test_backend_engineer():

    result = classify_job(
        title="Backend Engineer",
        description="""
            Build REST APIs using Python, FastAPI,
            PostgreSQL and Docker.
        """,
        skills=[
            "Python",
            "FastAPI",
            "PostgreSQL",
            "Docker",
        ],
    )

    assert result.domain == "technology"
    assert result.family == "backend"
    assert result.category == ENGINEERING_CATEGORY

    assert "Python" in result.required_skills
    assert "FastAPI" in result.required_skills


# ============================================================
# AI / ML
# ============================================================


def test_ai_engineer():

    result = classify_job(
        title="AI Engineer",
        description="""
            Build machine learning systems using Python,
            PyTorch, NLP and LLM technologies.
        """,
        skills=[
            "Python",
            "PyTorch",
            "NLP",
        ],
    )

    assert result.domain == "technology"
    assert result.family == "ai_ml"
    assert result.category == AI_CATEGORY

    assert "Python" in result.required_skills
    assert "PyTorch" in result.required_skills


# ============================================================
# DATA
# ============================================================


def test_data_engineer():

    result = classify_job(
        title="Data Engineer",
        description="""
            Build data pipelines using Python, SQL,
            PostgreSQL and AWS.
        """,
        skills=[
            "Python",
            "SQL",
            "PostgreSQL",
            "AWS",
        ],
    )

    assert result.domain == "technology"
    assert result.family == "data"
    assert result.category == DATA_CATEGORY


# ============================================================
# DEVOPS
# ============================================================


def test_devops_engineer():

    result = classify_job(
        title="DevOps Engineer",
        description="""
            Manage AWS infrastructure using Docker,
            Kubernetes and Terraform.
        """,
        skills=[
            "AWS",
            "Docker",
            "Kubernetes",
            "Terraform",
        ],
    )

    assert result.domain == "technology"
    assert result.family == "devops_cloud"
    assert result.category == INFRASTRUCTURE_CATEGORY


# ============================================================
# EXPERIENCE
# ============================================================


def test_intern_experience():

    result = classify_job(
        title="Software Engineering Intern",
        description="Work with our engineering team.",
    )

    assert result.experience_level == "intern"


def test_fresher_experience():

    result = classify_job(
        title="Junior Software Engineer",
        description="Entry-level software engineering role.",
    )

    assert result.experience_level == "entry"


def test_senior_experience():

    result = classify_job(
        title="Senior Backend Engineer",
        description="Lead backend architecture.",
    )

    assert result.experience_level == "senior"


def test_numeric_experience():

    result = classify_experience(
        "Software Engineer",
        "Candidates should have 3 years of experience.",
    )

    assert result == "mid"


# ============================================================
# REQUIRED SKILLS
# ============================================================


def test_required_skills():

    result = extract_required_skills(
        title="Backend Engineer",
        description="""
            Requirements:
            Python
            FastAPI
            PostgreSQL
            Docker
        """,
    )

    assert "Python" in result
    assert "FastAPI" in result
    assert "PostgreSQL" in result


# ============================================================
# PREFERRED SKILLS
# ============================================================


def test_preferred_skills():

    result = extract_preferred_skills(
        title="Backend Engineer",
        description="""
            Required:
            Python
            FastAPI

            Nice to have:
            Docker
            AWS
        """,
    )

    assert "Docker" in result
    assert "AWS" in result


# ============================================================
# REQUIRED VS PREFERRED
# ============================================================


def test_required_skill_is_not_preferred():

    result = classify_job(
        title="Backend Engineer",
        description="""
            Requirements:
            Python
            FastAPI

            Nice to have:
            Docker
            AWS
        """,
    )

    required = {
        skill.lower()
        for skill in result.required_skills
    }

    preferred = {
        skill.lower()
        for skill in result.preferred_skills
    }

    assert not (
        required & preferred
    )


# ============================================================
# UNKNOWN
# ============================================================


def test_unknown_job():

    result = classify_job(
        title="Mystery Position",
        description="Something interesting.",
    )

    assert result.domain == "unknown"
    assert result.family == "unknown"
    assert result.confidence == 0.0


# ============================================================
# SERIALIZATION
# ============================================================


def test_classification_to_dict():

    result = classify_job(
        title="Backend Engineer",
        description="Python backend development.",
    )

    data = result.to_dict()

    assert data["domain"] == result.domain
    assert data["family"] == result.family
    assert data["category"] == result.category
    assert data["required_skills"] == result.required_skills
    assert data["preferred_skills"] == result.preferred_skills