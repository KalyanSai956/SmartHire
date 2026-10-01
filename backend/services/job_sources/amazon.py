from __future__ import annotations

import re
from datetime import datetime
from typing import Any
from urllib.parse import urljoin

import httpx

from backend.services.job_sources.base import JobSourceAdapter, JobSourceJob


class AmazonAdapter(JobSourceAdapter):
    provider = "amazon"
    SEARCH_URL = "https://www.amazon.jobs/en/search.json"
    BASE_URL = "https://www.amazon.jobs"
    DEFAULT_RESULT_LIMIT = 100
    MAX_PAGES = 10
    SKILL_PATTERNS = ("python", "java", "javascript", "typescript", "c++", "c#", "go", "golang", "rust", "sql", "nosql", "mongodb", "postgresql", "mysql", "redis", "docker", "kubernetes", "aws", "azure", "gcp", "terraform", "linux", "git", "github", "jenkins", "ci/cd", "react", "node.js", "nodejs", "angular", "vue", "fastapi", "django", "flask", "spring", "spring boot", "machine learning", "deep learning", "artificial intelligence", "data science", "data engineering", "pandas", "numpy", "pytorch", "tensorflow", "spark", "hadoop", "kafka", "elasticsearch", "graphql", "rest api", "microservices", "devops", "security", "cybersecurity", "computer vision", "nlp", "natural language processing", "llm", "generative ai")

    def _clean_text(self, value: Any) -> str:
        text = str(value or "")
        text = re.sub(r"<[^>]+>", " ", text)
        text = re.sub(r"&nbsp;", " ", text, flags=re.I)
        text = re.sub(r"&amp;", "&", text, flags=re.I)
        return re.sub(r"\s+", " ", text).strip()

    def _join_text(self, *values: Any) -> str:
        parts = [self._clean_text(v) for v in values]
        return "\n\n".join(v for v in parts if v)

    def _absolute_url(self, value: Any) -> str:
        raw = str(value or "").strip()
        return urljoin(self.BASE_URL, raw) if raw else ""

    def _extract_job_id(self, item: dict[str, Any]) -> str:
        for key in ("id", "job_id", "jobId", "source_job_id"):
            value = item.get(key)
            if value is not None and str(value).strip():
                return str(value).strip()
        for key in ("job_path", "job_url", "url", "detail_url"):
            value = item.get(key)
            match = re.search(r"/([0-9]{5,})/?$", str(value or ""))
            if match:
                return match.group(1)
        return ""

    def _extract_title(self, item: dict[str, Any]) -> str:
        for key in ("job_title", "title", "jobTitle", "name"):
            value = self._clean_text(item.get(key))
            if value:
                return value
        return ""

    def _extract_location(self, item: dict[str, Any]) -> str:
        value = item.get("location")
        if isinstance(value, dict):
            return ", ".join(str(v).strip() for v in (value.get("city"), value.get("state"), value.get("state_code"), value.get("country")) if v and str(v).strip())
        if isinstance(value, list):
            return ", ".join(self._clean_text(v) for v in value if self._clean_text(v))
        for key in ("location_display", "location_string", "normalized_location", "loc_display"):
            text = self._clean_text(item.get(key))
            if text:
                return text
        return self._clean_text(value)

    def _extract_description(self, item: dict[str, Any]) -> str:
        return self._join_text(item.get("description"), item.get("job_description"), item.get("basic_qualifications"), item.get("preferred_qualifications"), item.get("responsibilities"), item.get("requirements"))

    def _extract_url(self, item: dict[str, Any], job_id: str) -> str:
        for key in ("job_url", "jobUrl", "application_url", "url", "detail_url"):
            value = self._absolute_url(item.get(key))
            if value:
                return value
        path = item.get("job_path")
        if path:
            return self._absolute_url(path)
        return f"{self.BASE_URL}/en/jobs/{job_id}" if job_id else self.BASE_URL

    def _extract_posted_at(self, item: dict[str, Any]) -> datetime | None:
        for key in ("posted_date", "posted_at", "publication_date", "date_posted", "created_at"):
            value = item.get(key)
            if not value:
                continue
            raw = str(value).strip()
            try:
                return datetime.fromisoformat(raw.replace("Z", "+00:00"))
            except ValueError:
                pass
            for fmt in ("%B %d, %Y", "%b %d, %Y", "%Y-%m-%d", "%m/%d/%Y"):
                try:
                    return datetime.strptime(raw, fmt)
                except ValueError:
                    pass
        return None

    def _extract_skills(self, item: dict[str, Any], description: str) -> list[str]:
        values: list[str] = []
        for key in ("skills", "required_skills", "preferred_skills"):
            value = item.get(key)
            if isinstance(value, list):
                values.extend(self._clean_text(v) for v in value if self._clean_text(v))
            elif isinstance(value, str):
                values.extend(self._clean_text(v) for v in re.split(r"[,;|]", value) if self._clean_text(v))
        haystack = description.lower()
        for skill in self.SKILL_PATTERNS:
            if re.search(rf"(?<![a-z0-9+#]){re.escape(skill)}(?![a-z0-9+#])", haystack, flags=re.I):
                values.append(skill)
        result = []
        seen = set()
        for value in values:
            normalized = re.sub(r"\s+", " ", value).strip()
            key = normalized.lower()
            if normalized and key not in seen:
                seen.add(key)
                result.append(normalized)
        return result[:100]

    def _extract_remote_type(self, item: dict[str, Any], location: str, description: str) -> str:
        explicit = str(item.get("remote_type") or item.get("workplace_type") or "").strip().lower()
        if explicit in {"remote", "hybrid", "onsite"}:
            return explicit
        text = f"{location} {description}".lower()
        if "hybrid" in text:
            return "hybrid"
        if "remote" in text:
            return "remote"
        return "onsite"

    def _extract_employment_type(self, item: dict[str, Any]) -> str:
        raw = self._clean_text(item.get("employment_type") or item.get("job_type") or item.get("employmentType")).lower()
        if "part" in raw:
            return "part_time"
        if "contract" in raw:
            return "contract"
        if "intern" in raw:
            return "internship"
        if "temporary" in raw:
            return "temporary"
        return "full_time"

    def _extract_experience_level(self, item: dict[str, Any], description: str) -> str | None:
        raw = self._clean_text(item.get("experience_level") or item.get("level") or item.get("seniority")).lower()
        text = f"{raw} {description}".lower()
        if re.search(r"\bintern(ship)?\b", text):
            return "internship"
        if re.search(r"\b(entry[- ]level|graduate|new grad|fresher)\b", text):
            return "entry"
        if re.search(r"\b(0\s*[-–]?\s*2|0\s+to\s+2|1\s*[-–]?\s*2)\s+years?\b", text):
            return "entry"
        if re.search(r"\b(senior|sr\.?|lead|principal|staff|manager|director)\b", text):
            return "senior"
        if re.search(r"\b(3\s*[-–]?\s*5|4\s*[-–]?\s*6|5\s*[-–]?\s*7)\s+years?\b", text):
            return "mid"
        return raw or None

    async def _fetch_page(self, client: httpx.AsyncClient, *, location: str, country: str, result_limit: int, offset: int) -> list[dict[str, Any]]:
        response = await client.get(self.SEARCH_URL, params={"normalized_country_code[]": country, "loc_query": location, "result_limit": result_limit, "offset": offset}, headers={"Accept": "application/json", "User-Agent": "SmartHireATS/1.0"})
        response.raise_for_status()
        payload = response.json()
        if isinstance(payload, dict):
            for key in ("jobs", "results", "job_results", "data"):
                value = payload.get(key)
                if isinstance(value, list):
                    return [item for item in value if isinstance(item, dict)]
        if isinstance(payload, list):
            return [item for item in payload if isinstance(item, dict)]
        return []

    def _normalize(self, item: dict[str, Any], *, company_id: str, source_id: str, source_url: str) -> JobSourceJob | None:
        job_id = self._extract_job_id(item)
        title = self._extract_title(item)
        location = self._extract_location(item)
        description = self._extract_description(item)
        if not job_id or not title:
            return None
        return JobSourceJob(company_id=str(company_id), source_id=str(source_id), provider=self.provider, source_job_id=job_id, title=title, description=description, location=location, remote_type=self._extract_remote_type(item, location, description), employment_type=self._extract_employment_type(item), experience_level=self._extract_experience_level(item, description), skills=self._extract_skills(item, description), application_url=self._extract_url(item, job_id), source_url=source_url or self.SEARCH_URL, posted_at=self._extract_posted_at(item))

    async def fetch_jobs(self, *, company_id: str, source_id: str, config: dict[str, Any]) -> list[JobSourceJob]:
        provider_config = config.get("provider_config") or {}
        country = str(provider_config.get("country") or "IND").strip()
        location = str(provider_config.get("location") or "India").strip()
        result_limit = max(1, min(int(provider_config.get("result_limit") or self.DEFAULT_RESULT_LIMIT), 100))
        source_url = str(config.get("source_url") or f"{self.BASE_URL}/en/search?country={country}&loc_query={location}").strip()
        jobs: list[JobSourceJob] = []
        seen_ids: set[str] = set()
        async with httpx.AsyncClient(timeout=60.0, follow_redirects=True) as client:
            for page in range(self.MAX_PAGES):
                items = await self._fetch_page(client, location=location, country=country, result_limit=result_limit, offset=page * result_limit)
                if not items:
                    break
                for item in items:
                    normalized = self._normalize(item, company_id=company_id, source_id=source_id, source_url=source_url)
                    if normalized is None or normalized.source_job_id in seen_ids:
                        continue
                    seen_ids.add(normalized.source_job_id)
                    jobs.append(normalized)
                if len(items) < result_limit:
                    break
        return jobs
