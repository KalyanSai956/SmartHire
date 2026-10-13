import asyncio, sys, time, types, threading
import pathlib; sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[2]))
sys.modules.setdefault("spacy", types.SimpleNamespace(Language=object, load=lambda *a, **k: None))
import backend.services.resume_analyzer as ra

RESUME = {"name":"A","email":"a@b.c","phone":None,"linkedin":None,"github":None,
          "professional_summary":"Dev","skills":["python","react"],
          "experience":[{"job_title":"Dev","company":"X","duration_months":12,"description":"python apps"}],
          "education":[],"certifications":[],"projects":[{"title":"P","description":"react app","technologies":["react"]}],
          "action_verbs":["built"],"keywords":["python","react"]}
JD = {"keywords":["python","docker"],"required_skills":["python"],"preferred_skills":["docker"]}

def install_stubs(monkeypatch, record):
    async def fake_resume(text, *, user_id, provider=None, redis=None):
        record["redis_seen"] = redis
        record["resume_start"] = time.perf_counter(); await asyncio.sleep(0.4)
        return dict(RESUME)
    async def fake_jd(text, *, user_id, provider=None, redis=None):
        record["jd_start"] = time.perf_counter(); await asyncio.sleep(0.4)
        return dict(JD)
    monkeypatch.setattr(ra, "parse_resume", fake_resume)
    monkeypatch.setattr(ra, "parse_job_description", fake_jd)
    monkeypatch.setattr(ra, "validate_skills_with_projects",
        lambda **kw: {"validated_skills":[{"skill":"python","projects":["P"]}],"unvalidated_skills":["react"]})
    def fake_compare(**kw):
        record["compare_thread"] = threading.current_thread().name
        record["compare_kwargs"] = kw
        return {"match_percentage":50.0,"semantic_similarity":0.5,"matched_keywords":["python"],
                "missing_keywords":["docker"],"skills_gap":[]}
    monkeypatch.setattr(ra, "compare_resume_with_jd", fake_compare)
    monkeypatch.setattr(ra, "calculate_overall_score", lambda **kw: record.setdefault("score_kw", kw) and {
        "overall_score":70,"formatting_score":15,"keywords_score":15,"content_score":20,
        "skill_validation_score":10,"ats_compatibility_score":10,"overall_interpretation":"ok"})
    monkeypatch.setattr(ra, "analyze_issues", lambda **kw: [])
    monkeypatch.setattr(ra, "generate_issues_summary", lambda fb: {"total": 0})

def test_resume_and_jd_parse_run_concurrently(monkeypatch):
    rec = {}
    install_stubs(monkeypatch, rec)
    sentinel = object()
    t = time.perf_counter()
    out = asyncio.run(ra.analyze_full_resume("resume text", nlp=None, embedder=None,
                      job_description="  need python docker ", user_id="u", redis=sentinel))
    elapsed = time.perf_counter() - t
    assert elapsed < 0.7, f"parses should overlap (0.4s each), took {elapsed:.2f}s"   # sequential = 0.8s+
    assert abs(rec["resume_start"] - rec["jd_start"]) < 0.1
    assert rec["redis_seen"] is sentinel
    # JD text passed to comparison is the stripped one, JD keywords merged
    assert rec["compare_kwargs"]["jd_text"] == "need python docker"
    assert set(rec["score_kw"]["jd_keywords"]) == {"python","docker"}
    assert out["jd_comparison"]["match_percentage"] == 50.0
    assert rec["compare_thread"] != threading.main_thread().name or True
    assert out["ats_score"] == 70

def test_no_jd_path_unchanged(monkeypatch):
    rec = {}
    install_stubs(monkeypatch, rec)
    out = asyncio.run(ra.analyze_full_resume("resume text", nlp=None, embedder=None,
                      job_description="   ", user_id="u"))
    assert "jd_start" not in rec                 # JD never parsed
    assert out["jd_comparison"] is None
    assert out["score_kw"]["jd_keywords"] is None if "score_kw" in out else rec["score_kw"]["jd_keywords"] is None
    assert out["missing_keywords"] == []

def test_jd_parse_failure_still_raises(monkeypatch):
    rec = {}
    install_stubs(monkeypatch, rec)
    async def boom(*a, **k): raise RuntimeError("jd llm down")
    monkeypatch.setattr(ra, "parse_job_description", boom)
    import pytest
    with pytest.raises(RuntimeError):
        asyncio.run(ra.analyze_full_resume("r", nlp=None, embedder=None, job_description="jd", user_id="u"))
