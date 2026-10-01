from __future__ import annotations

from typing import Any, Dict, List
import re


MAX_CHUNK_CHARS = 1400
MIN_CHUNK_CHARS = 20


def _to_dict(value: Any) -> Any:
    """
    Convert Pydantic models / nested objects into dictionaries.
    """
    if value is None:
        return None

    if hasattr(value, "model_dump"):
        return value.model_dump()

    if isinstance(value, dict):
        return {
            key: _to_dict(item)
            for key, item in value.items()
        }

    if isinstance(value, list):
        return [
            _to_dict(item)
            for item in value
        ]

    return value


def _clean_text(value: Any) -> str:
    """
    Normalize whitespace while preserving readable text.
    """
    if value is None:
        return ""

    text = str(value)

    text = text.replace("\r\n", "\n")
    text = text.replace("\r", "\n")

    # Collapse spaces/tabs
    text = re.sub(r"[ \t]+", " ", text)

    # Collapse excessive blank lines
    text = re.sub(r"\n{3,}", "\n\n", text)

    return text.strip()


def _join_non_empty(parts: List[str]) -> str:
    """
    Join meaningful text fragments.
    """
    cleaned = []

    for part in parts:
        part = _clean_text(part)

        if part:
            cleaned.append(part)

    return "\n".join(cleaned)


def _split_long_text(
    text: str,
    max_chars: int = MAX_CHUNK_CHARS,
) -> List[str]:
    """
    Split unusually long sections without cutting blindly
    in the middle of a sentence whenever possible.
    """

    text = _clean_text(text)

    if not text:
        return []

    if len(text) <= max_chars:
        return [text]

    paragraphs = [
        p.strip()
        for p in text.split("\n")
        if p.strip()
    ]

    chunks: List[str] = []
    current = ""

    for paragraph in paragraphs:

        if len(paragraph) > max_chars:

            sentences = re.split(
                r"(?<=[.!?])\s+",
                paragraph,
            )

            for sentence in sentences:

                sentence = sentence.strip()

                if not sentence:
                    continue

                if len(sentence) > max_chars:

                    if current:
                        chunks.append(current.strip())
                        current = ""

                    for start in range(
                        0,
                        len(sentence),
                        max_chars,
                    ):
                        piece = sentence[
                            start:start + max_chars
                        ].strip()

                        if piece:
                            chunks.append(piece)

                    continue

                proposed = (
                    f"{current}\n{sentence}"
                    if current
                    else sentence
                )

                if len(proposed) <= max_chars:
                    current = proposed
                else:
                    if current:
                        chunks.append(current.strip())

                    current = sentence

            continue

        proposed = (
            f"{current}\n{paragraph}"
            if current
            else paragraph
        )

        if len(proposed) <= max_chars:
            current = proposed
        else:

            if current:
                chunks.append(current.strip())

            current = paragraph

    if current:
        chunks.append(current.strip())

    return [
        chunk
        for chunk in chunks
        if len(chunk.strip()) >= MIN_CHUNK_CHARS
    ]


def _add_chunk(
    chunks: List[Dict[str, Any]],
    *,
    section_type: str,
    title: str,
    content: str,
    metadata: Dict[str, Any] | None = None,
) -> None:

    content = _clean_text(content)

    if len(content) < MIN_CHUNK_CHARS:
        return

    pieces = _split_long_text(content)

    for piece_number, piece in enumerate(pieces):

        chunks.append(
            {
                "section_type": section_type,
                "title": title,
                "content": piece,
                "metadata": {
                    **(metadata or {}),
                    "piece": piece_number,
                },
            }
        )


def _chunk_summary(
    resume: Dict[str, Any],
    chunks: List[Dict[str, Any]],
) -> None:

    summary = _clean_text(
        resume.get("summary")
        or resume.get("professional_summary")
        or ""
    )

    if not summary:
        return

    _add_chunk(
        chunks,
        section_type="summary",
        title="Professional Summary",
        content=summary,
        metadata={
            "source": "resume_summary",
        },
    )


def _chunk_skills(
    resume: Dict[str, Any],
    chunks: List[Dict[str, Any]],
) -> None:

    skills = resume.get("skills") or []

    if not isinstance(skills, list):
        skills = [skills]

    skills = [
        _clean_text(skill)
        for skill in skills
        if _clean_text(skill)
    ]

    if not skills:
        return

    # Keep the whole skills section together.
    content = "Skills: " + ", ".join(skills)

    _add_chunk(
        chunks,
        section_type="skills",
        title="Skills",
        content=content,
        metadata={
            "skills": skills,
            "count": len(skills),
        },
    )


def _chunk_experience(
    resume: Dict[str, Any],
    chunks: List[Dict[str, Any]],
) -> None:

    experience = resume.get("experience") or []

    if not isinstance(experience, list):
        return

    for index, item in enumerate(experience):

        if not isinstance(item, dict):
            continue

        company = _clean_text(
            item.get("company")
        )

        role = _clean_text(
            item.get("role")
            or item.get("job_title")
        )

        location = _clean_text(
            item.get("location")
        )

        start_date = _clean_text(
            item.get("start_date")
        )

        end_date = _clean_text(
            item.get("end_date")
        )

        bullets = item.get("bullets") or []

        if not isinstance(bullets, list):
            bullets = [bullets]

        bullets = [
            _clean_text(bullet)
            for bullet in bullets
            if _clean_text(bullet)
        ]

        description = _clean_text(
            item.get("description")
        )

        heading_parts = []

        if role:
            heading_parts.append(role)

        if company:
            heading_parts.append(
                f"at {company}"
            )

        heading = " ".join(heading_parts)

        if not heading:
            heading = f"Experience {index + 1}"

        date_text = ""

        if start_date or end_date:
            date_text = (
                f"{start_date} - "
                f"{end_date}"
            ).strip(" -")

        content_parts = []

        if heading:
            content_parts.append(heading)

        if date_text:
            content_parts.append(date_text)

        if location:
            content_parts.append(location)

        if description:
            content_parts.append(description)

        for bullet in bullets:
            content_parts.append(
                f"- {bullet}"
            )

        content = _join_non_empty(
            content_parts
        )

        _add_chunk(
            chunks,
            section_type="experience",
            title=heading,
            content=content,
            metadata={
                "experience_index": index,
                "company": company,
                "role": role,
                "start_date": start_date,
                "end_date": end_date,
            },
        )


def _chunk_projects(
    resume: Dict[str, Any],
    chunks: List[Dict[str, Any]],
) -> None:

    projects = resume.get("projects") or []

    if not isinstance(projects, list):
        return

    for index, item in enumerate(projects):

        if not isinstance(item, dict):
            continue

        name = _clean_text(
            item.get("name")
            or item.get("title")
        )

        description = _clean_text(
            item.get("description")
        )

        technologies = item.get(
            "technologies"
        ) or []

        if not isinstance(technologies, list):
            technologies = [technologies]

        technologies = [
            _clean_text(technology)
            for technology in technologies
            if _clean_text(technology)
        ]

        bullets = item.get("bullets") or []

        if not isinstance(bullets, list):
            bullets = [bullets]

        bullets = [
            _clean_text(bullet)
            for bullet in bullets
            if _clean_text(bullet)
        ]

        url = _clean_text(
            item.get("url")
        )

        title = name or f"Project {index + 1}"

        content_parts = [
            title
        ]

        if description:
            content_parts.append(
                description
            )

        if technologies:
            content_parts.append(
                "Technologies: "
                + ", ".join(technologies)
            )

        for bullet in bullets:
            content_parts.append(
                f"- {bullet}"
            )

        if url:
            content_parts.append(
                f"URL: {url}"
            )

        content = _join_non_empty(
            content_parts
        )

        _add_chunk(
            chunks,
            section_type="project",
            title=title,
            content=content,
            metadata={
                "project_index": index,
                "technologies": technologies,
            },
        )


def _chunk_education(
    resume: Dict[str, Any],
    chunks: List[Dict[str, Any]],
) -> None:

    education = resume.get("education") or []

    if not isinstance(education, list):
        return

    for index, item in enumerate(education):

        if not isinstance(item, dict):
            continue

        institution = _clean_text(
            item.get("institution")
        )

        degree = _clean_text(
            item.get("degree")
        )

        field = _clean_text(
            item.get("field_of_study")
        )

        location = _clean_text(
            item.get("location")
        )

        start_date = _clean_text(
            item.get("start_date")
        )

        end_date = _clean_text(
            item.get("end_date")
        )

        grade = _clean_text(
            item.get("grade")
        )

        content = _join_non_empty(
            [
                degree,
                field,
                institution,
                location,
                (
                    f"{start_date} - {end_date}"
                    if start_date or end_date
                    else ""
                ),
                (
                    f"Grade: {grade}"
                    if grade
                    else ""
                ),
            ]
        )

        _add_chunk(
            chunks,
            section_type="education",
            title=institution
            or f"Education {index + 1}",
            content=content,
            metadata={
                "education_index": index,
                "institution": institution,
                "degree": degree,
                "field": field,
            },
        )


def _chunk_certifications(
    resume: Dict[str, Any],
    chunks: List[Dict[str, Any]],
) -> None:

    certifications = resume.get(
        "certifications"
    ) or []

    if not isinstance(certifications, list):
        return

    items = []

    for item in certifications:

        if isinstance(item, str):

            value = _clean_text(item)

            if value:
                items.append(value)

            continue

        if isinstance(item, dict):

            name = _clean_text(
                item.get("name")
            )

            issuer = _clean_text(
                item.get("issuer")
            )

            date = _clean_text(
                item.get("date")
            )

            url = _clean_text(
                item.get("url")
            )

            parts = [
                name,
                issuer,
                date,
                url,
            ]

            value = " — ".join(
                part
                for part in parts
                if part
            )

            if value:
                items.append(value)

    if not items:
        return

    content = "\n".join(
        f"- {item}"
        for item in items
    )

    _add_chunk(
        chunks,
        section_type="certifications",
        title="Certifications",
        content=content,
        metadata={
            "count": len(items),
        },
    )


def _chunk_achievements(
    resume: Dict[str, Any],
    chunks: List[Dict[str, Any]],
) -> None:

    achievements = resume.get(
        "achievements"
    ) or []

    if not isinstance(achievements, list):
        return

    items = []

    for item in achievements:

        if isinstance(item, str):

            value = _clean_text(item)

            if value:
                items.append(value)

            continue

        if isinstance(item, dict):

            title = _clean_text(
                item.get("title")
            )

            description = _clean_text(
                item.get("description")
            )

            date = _clean_text(
                item.get("date")
            )

            value = _join_non_empty(
                [
                    title,
                    description,
                    date,
                ]
            )

            if value:
                items.append(value)

    if not items:
        return

    content = "\n".join(
        f"- {item}"
        for item in items
    )

    _add_chunk(
        chunks,
        section_type="achievements",
        title="Achievements",
        content=content,
        metadata={
            "count": len(items),
        },
    )


def chunk_resume(
    resume_profile: Dict[str, Any] | Any,
) -> List[Dict[str, Any]]:
    """
    Convert a structured SmartHire resume profile into
    semantically meaningful RAG chunks.

    Returns:
        [
            {
                "section_type": "...",
                "title": "...",
                "content": "...",
                "metadata": {...}
            }
        ]
    """

    resume = _to_dict(
        resume_profile
    )

    if not isinstance(resume, dict):
        raise ValueError(
            "resume_profile must be a dictionary or Pydantic model."
        )

    chunks: List[Dict[str, Any]] = []

    _chunk_summary(
        resume,
        chunks,
    )

    _chunk_skills(
        resume,
        chunks,
    )

    _chunk_experience(
        resume,
        chunks,
    )

    _chunk_projects(
        resume,
        chunks,
    )

    _chunk_education(
        resume,
        chunks,
    )

    _chunk_certifications(
        resume,
        chunks,
    )

    _chunk_achievements(
        resume,
        chunks,
    )

    # Assign stable chunk indexes.
    for index, chunk in enumerate(chunks):
        chunk["chunk_index"] = index

    return chunks