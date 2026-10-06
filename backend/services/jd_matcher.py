from typing import Dict, List

import numpy as np
import spacy
from sentence_transformers import SentenceTransformer
from rapidfuzz import fuzz

from backend.utils.matching import (
    fuzzy_match_keywords,
    normalize_skill,
)


MAX_TEXT_LENGTH = 5000
SEMANTIC_BATCH_SIZE = 16


def calculate_semantic_similarity(
    resume_text: str,
    jd_text: str,
    embedder: SentenceTransformer,
) -> float:

    if not resume_text or not jd_text:
        return 0.0

    try:
        embeddings = embedder.encode(
            [
                resume_text[:MAX_TEXT_LENGTH],
                jd_text[:MAX_TEXT_LENGTH],
            ],
            batch_size=SEMANTIC_BATCH_SIZE,
            convert_to_tensor=False,
            normalize_embeddings=True,
            show_progress_bar=False,
        )

        similarity = float(
            np.dot(
                embeddings[0],
                embeddings[1],
            )
        )

        return float(
            np.clip(
                similarity,
                0.0,
                1.0,
            )
        )

    except Exception:
        return 0.0


def identify_matched_keywords(
    resume_keywords: List[str],
    jd_keywords: List[str],
) -> List[str]:

    result = fuzzy_match_keywords(
        resume_keywords,
        jd_keywords,
        threshold=80,
    )

    return result["matched"]


def identify_missing_keywords(
    resume_keywords: List[str],
    jd_keywords: List[str],
    top_n: int = 15,
) -> List[str]:

    result = fuzzy_match_keywords(
        resume_keywords,
        jd_keywords,
        threshold=80,
    )

    return result["missing"][:top_n]


def analyze_skills_gap(
    resume_skills: List[str],
    jd_text: str,
    nlp: spacy.Language,
) -> List[str]:

    doc = nlp(jd_text[:MAX_TEXT_LENGTH])

    jd_skills = set()

    for ent in doc.ents:
        if ent.label_ in ["PRODUCT", "ORG", "LANGUAGE"]:
            jd_skills.add(ent.text.lower())

    for chunk in doc.noun_chunks:
        chunk_text = chunk.text.lower().strip()

        if 1 <= len(chunk_text.split()) <= 4:
            jd_skills.add(chunk_text)

    resume_normalized = {
        normalize_skill(skill)
        for skill in resume_skills
    }

    gap = []

    for jd_skill in jd_skills:
        jd_normalized = normalize_skill(jd_skill)

        if jd_normalized in resume_normalized:
            continue

        best_score = max(
            (
                fuzz.token_sort_ratio(
                    jd_normalized,
                    resume_skill,
                )
                for resume_skill in resume_normalized
            ),
            default=0,
        )

        if best_score < 75:
            gap.append(jd_skill)

    return sorted(gap)[:20]


def calculate_match_percentage(
    resume_keywords: List[str],
    jd_keywords: List[str],
    semantic_similarity: float,
) -> float:

    if not jd_keywords:
        return 0.0

    matched = identify_matched_keywords(
        resume_keywords,
        jd_keywords,
    )

    keyword_overlap = len(matched) / len(jd_keywords)

    match_pct = (
        keyword_overlap * 0.6
        + semantic_similarity * 0.4
    ) * 100

    return float(
        np.clip(
            match_pct,
            0.0,
            100.0,
        )
    )


def compare_resume_with_jd(
    resume_text: str,
    resume_keywords: List[str],
    resume_skills: List[str],
    jd_text: str,
    jd_keywords: List[str],
    embedder: SentenceTransformer,
    nlp: spacy.Language,
) -> Dict:

    semantic_similarity = calculate_semantic_similarity(
        resume_text,
        jd_text,
        embedder,
    )

    matched_keywords = identify_matched_keywords(
        resume_keywords,
        jd_keywords,
    )

    missing_keywords = identify_missing_keywords(
        resume_keywords,
        jd_keywords,
    )

    skills_gap = analyze_skills_gap(
        resume_skills,
        jd_text,
        nlp,
    )

    match_percentage = calculate_match_percentage(
        resume_keywords,
        jd_keywords,
        semantic_similarity,
    )

    return {
        "match_percentage": match_percentage,
        "semantic_similarity": semantic_similarity,
        "matched_keywords": matched_keywords,
        "missing_keywords": missing_keywords,
        "skills_gap": skills_gap,
    }