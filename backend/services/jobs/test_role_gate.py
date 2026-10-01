from backend.services.jobs.role_gate import evaluate_job
from backend.services.jobs.role_taxonomy import (
    AI_ML,
    BACKEND,
    DATA,
    DEVOPS_CLOUD,
    FRONTEND,
    FULL_STACK,
    SOFTWARE_ENGINEERING,
    TECHNOLOGY,
    UNKNOWN,
    classify_role,
    classify_resume,
)


# ============================================================
# ROLE CLASSIFICATION TESTS
# ============================================================


def test_backend_engineer_is_backend():
    result = classify_role(
        "Backend Engineer",
        "Build REST APIs using Python, FastAPI, PostgreSQL and Docker.",
    )

    assert result.domain == TECHNOLOGY
    assert result.family == BACKEND
    assert result.is_technical is True


def test_frontend_engineer_is_frontend():
    result = classify_role(
        "Frontend Developer",
        "Build React applications using JavaScript, HTML and CSS.",
    )

    assert result.domain == TECHNOLOGY
    assert result.family == FRONTEND
    assert result.is_technical is True


def test_full_stack_engineer():
    result = classify_role(
        "Full Stack Developer",
        "Develop React frontend and Node.js backend applications.",
    )

    assert result.domain == TECHNOLOGY
    assert result.family == FULL_STACK
    assert result.is_technical is True


def test_data_scientist_is_ai_ml():
    result = classify_role(
        "Data Scientist",
        "Build machine learning models using Python, pandas and scikit-learn.",
    )

    assert result.domain == TECHNOLOGY
    assert result.family == AI_ML
    assert result.is_technical is True


def test_machine_learning_engineer():
    result = classify_role(
        "Machine Learning Engineer",
        "Develop machine learning and deep learning systems using Python.",
    )

    assert result.domain == TECHNOLOGY
    assert result.family == AI_ML
    assert result.is_technical is True


def test_devops_engineer():
    result = classify_role(
        "DevOps Engineer",
        "Work with AWS, Docker, Kubernetes and CI/CD pipelines.",
    )

    assert result.domain == TECHNOLOGY
    assert result.family == DEVOPS_CLOUD
    assert result.is_technical is True


# ============================================================
# NON-TECHNICAL ROLE TESTS
# ============================================================


def test_content_marketer_is_non_technical():
    result = classify_role(
        "Content Marketer",
        "Create content campaigns, blogs and social media marketing strategies.",
    )

    assert result.is_technical is False


def test_visual_designer_is_non_technical():
    result = classify_role(
        "Visual Designer",
        "Create visual designs, branding and marketing assets.",
    )

    assert result.is_technical is False


# ============================================================
# RESUME CLASSIFICATION
# ============================================================


def test_resume_classification_for_technical_resume():
    resume_text = """
    Software Engineer with experience in Python, JavaScript, React,
    Node.js, FastAPI, MongoDB, SQL and machine learning.
    """

    result = classify_resume(resume_text)

    assert result.is_technical is True
    assert result.domain == TECHNOLOGY


# ============================================================
# ROLE GATE TESTS
# ============================================================


def test_backend_job_matches_technical_resume():

    resume_text = """
    Computer Science graduate with skills in Python, FastAPI,
    Node.js, React, MongoDB, SQL and REST APIs.
    """

    resume_classification = classify_resume(
        resume_text=resume_text,
        resume_skills=[
            "Python",
            "FastAPI",
            "Node.js",
            "React",
            "MongoDB",
            "SQL",
        ],
        target_roles=[
            "Backend Engineer",
        ],
    )

    result = evaluate_job(
        resume_classification=resume_classification,
        job_title="Backend Engineer",
        job_description="""
            Build backend APIs using Python, FastAPI, PostgreSQL
            and cloud services.
        """,
        job_skills=[
            "Python",
            "FastAPI",
            "PostgreSQL",
        ],
    )

    assert result.allowed is True


def test_content_marketer_rejected_for_technical_resume():

    resume_text = """
    Computer Science graduate with skills in Python, FastAPI,
    React, Node.js, MongoDB and machine learning.
    """

    resume_classification = classify_resume(
        resume_text=resume_text,
        resume_skills=[
            "Python",
            "FastAPI",
            "React",
            "Node.js",
            "MongoDB",
        ],
        target_roles=[
            "Software Engineer",
        ],
    )

    result = evaluate_job(
        resume_classification=resume_classification,
        job_title="Content Marketer",
        job_description="""
            Create blog content, marketing campaigns and social
            media strategies.
        """,
        job_skills=[
            "Content Writing",
            "SEO",
            "Social Media",
        ],
    )

    assert result.allowed is False


def test_visual_designer_rejected_for_technical_resume():

    resume_text = """
    Software Engineer with Python, React, Node.js and FastAPI experience.
    """

    resume_classification = classify_resume(
        resume_text=resume_text,
        resume_skills=[
            "Python",
            "React",
            "Node.js",
            "FastAPI",
        ],
        target_roles=[
            "Software Engineer",
        ],
    )

    result = evaluate_job(
        resume_classification=resume_classification,
        job_title="Visual Designer",
        job_description="""
            Design visual assets, branding materials and marketing graphics.
        """,
        job_skills=[
            "Figma",
            "Adobe Illustrator",
            "Photoshop",
        ],
    )

    assert result.allowed is False


# ============================================================
# ROLE FAMILY COMPATIBILITY
# ============================================================


def test_backend_resume_can_match_full_stack():

    resume_classification = classify_resume(
        resume_text="""
        Backend developer experienced with Python, FastAPI,
        REST APIs, PostgreSQL and Docker.
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

    result = evaluate_job(
        resume_classification=resume_classification,
        job_title="Full Stack Developer",
        job_description="""
            Build React frontend applications and Node.js backend APIs.
        """,
        job_skills=[
            "React",
            "Node.js",
            "REST APIs",
        ],
    )

    assert result.allowed is True


def test_unknown_job_is_rejected():

    resume_classification = classify_resume(
        resume_text="""
        Software engineer experienced with Python and React.
        """,
        resume_skills=[
            "Python",
            "React",
        ],
        target_roles=[
            "Software Engineer",
        ],
    )

    result = evaluate_job(
        resume_classification=resume_classification,
        job_title="Mystery Position",
        job_description="Something interesting at our company.",
        job_skills=[],
    )

    assert result.allowed is False
    assert "could not be classified" in result.reason.lower()