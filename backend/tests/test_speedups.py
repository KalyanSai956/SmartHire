import asyncio, sys, time, types, json
import pathlib; sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[2]))
import pytest

# --------------------------------------------------------------
# 1. Groq provider: reasoning_effort + client reuse
# --------------------------------------------------------------
def test_groq_reasoning_effort_and_client_reuse(monkeypatch):
    from backend.services.llm import groq_provider as gp

    seen = {}

    class FakeCompletions:
        async def create(self, **kw):
            seen.update(kw)
            msg = types.SimpleNamespace(content='{"a": 1}')
            return types.SimpleNamespace(
                choices=[types.SimpleNamespace(message=msg)],
                usage=types.SimpleNamespace(prompt_tokens=1, completion_tokens=1, total_tokens=2),
            )

    p1 = gp.GroqProvider(api_key="k-test")
    p2 = gp.GroqProvider(api_key="k-test")
    assert p1.client is p2.client, "AsyncGroq client should be shared per key"

    p1.client = types.SimpleNamespace(chat=types.SimpleNamespace(completions=FakeCompletions()))
    r = asyncio.run(p1.generate_json([{"role": "user", "content": "x"}]))
    assert r.parsed_json == {"a": 1}
    assert seen["reasoning_effort"] == "low"
    assert seen["response_format"] == {"type": "json_object"}

    # non-reasoning model must NOT receive the parameter
    seen.clear()
    p3 = gp.GroqProvider(api_key="k-test", default_model="llama-3.3-70b-versatile")
    p3.client = p1.client
    asyncio.run(p3.generate_json([{"role": "user", "content": "x"}]))
    assert "reasoning_effort" not in seen


def test_groq_reasoning_effort_can_be_disabled(monkeypatch):
    from backend.services.llm import groq_provider as gp
    monkeypatch.setattr(gp, "GROQ_REASONING_EFFORT", "off")
    seen = {}
    class C:
        async def create(self, **kw):
            seen.update(kw)
            msg = types.SimpleNamespace(content="{}")
            return types.SimpleNamespace(choices=[types.SimpleNamespace(message=msg)],
                                         usage=None)
    p = gp.GroqProvider(api_key="k2")
    p.client = types.SimpleNamespace(chat=types.SimpleNamespace(completions=C()))
    asyncio.run(p.generate_json([{"role": "user", "content": "x"}]))
    assert "reasoning_effort" not in seen


# --------------------------------------------------------------
# 2. user_gateway: concurrent lookup, priority order preserved
# --------------------------------------------------------------
def test_user_gateway_parallel_lookup_keeps_priority(monkeypatch):
    from backend.services.llm import user_gateway as ug

    delay = 0.3
    calls = []

    async def fake_cred(*, user_id, provider):
        calls.append(provider)
        await asyncio.sleep(delay)
        # user has openai + anthropic; priority says openai wins over anthropic
        if provider in ("openai", "anthropic"):
            return f"key-{provider}", {"model": f"m-{provider}"}
        return None, None

    monkeypatch.setattr(ug, "_get_user_credential", fake_cred)

    t = time.perf_counter()
    gw = asyncio.run(ug.create_user_llm_gateway(user_id="u", feature="f"))
    elapsed = time.perf_counter() - t

    assert gw.provider.provider_name == "openai"
    assert sorted(calls) == sorted(ug.DEFAULT_PROVIDER_PRIORITY)
    # sequential would be >= 0.6s (groq miss + openai hit stops early) — in the OLD code
    # worst case (no BYOK) was 4*delay = 1.2s; now ~1*delay
    assert elapsed < delay * 2


def test_user_gateway_no_byok_falls_back_to_platform_and_is_fast(monkeypatch):
    from backend.services.llm import user_gateway as ug
    async def fake_cred(*, user_id, provider):
        await asyncio.sleep(0.25)
        return None, None
    monkeypatch.setattr(ug, "_get_user_credential", fake_cred)
    t = time.perf_counter()
    gw = asyncio.run(ug.create_user_llm_gateway(user_id="u", feature="f"))
    assert time.perf_counter() - t < 0.6          # was ~1.0s (4 x 0.25)
    assert gw.usage_source == "platform"


def test_user_gateway_survives_one_failed_lookup(monkeypatch):
    from backend.services.llm import user_gateway as ug
    async def fake_cred(*, user_id, provider):
        if provider == "groq":
            raise RuntimeError("db hiccup")
        if provider == "google":
            return "gk", {"model": None}
        return None, None
    monkeypatch.setattr(ug, "_get_user_credential", fake_cred)
    gw = asyncio.run(ug.create_user_llm_gateway(user_id="u", feature="f"))
    assert gw.provider.provider_name == "google"


# --------------------------------------------------------------
# 3. Gateway: usage recording no longer blocks the response
# --------------------------------------------------------------
def test_usage_recording_is_off_critical_path(monkeypatch):
    from backend.services.llm import gateway as gw_mod
    from backend.services.llm.base import LLMResponse, LLMUsage

    async def slow_record(**kw):
        await asyncio.sleep(0.5)
        slow_record.done = True
    slow_record.done = False
    monkeypatch.setattr(gw_mod, "record_llm_usage", slow_record)

    async def run():
        g = gw_mod.LLMGateway(provider="groq", api_key="k", user_id="u")
        resp = LLMResponse(content="{}", usage=LLMUsage(), provider="groq", model="m")
        async def fake_generate_json(*a, **k): return resp
        g.provider.generate_json = fake_generate_json
        t = time.perf_counter()
        await g.generate_json([{"role": "user", "content": "x"}])
        returned_after = time.perf_counter() - t
        assert returned_after < 0.2           # did not wait for the 0.5s write
        assert slow_record.done is False
        await asyncio.sleep(0.7)              # task still completes in the background
        assert slow_record.done is True
    asyncio.run(run())


# --------------------------------------------------------------
# 4. Parse cache (fakeredis): 2nd call must not hit the LLM
# --------------------------------------------------------------
def test_resume_parse_cache_hit_and_isolation(monkeypatch):
    import fakeredis.aioredis as fr
    from backend.services import groq_parser as gp

    n = {"resume": 0, "jd": 0}
    async def fake_resume(raw_text, *, user_id, provider=None):
        n["resume"] += 1
        await asyncio.sleep(0.2)
        return {"name": "X", "skills": ["python"], "marker": raw_text[:5]}
    async def fake_jd(raw_text, *, user_id, provider=None):
        n["jd"] += 1
        return {"keywords": ["k"]}
    monkeypatch.setattr(gp, "_parse_resume_llm", fake_resume)
    monkeypatch.setattr(gp, "_parse_job_description_llm", fake_jd)

    async def run():
        r = fr.FakeRedis(decode_responses=True)
        a = await gp.parse_resume("hello resume", user_id="u1", redis=r)
        t = time.perf_counter()
        b = await gp.parse_resume("hello resume", user_id="u1", redis=r)
        hit_time = time.perf_counter() - t
        assert a == b and n["resume"] == 1 and hit_time < 0.1

        # different user -> separate entry (no cross-user sharing)
        await gp.parse_resume("hello resume", user_id="u2", redis=r)
        assert n["resume"] == 2
        # different text -> miss
        await gp.parse_resume("other resume", user_id="u1", redis=r)
        assert n["resume"] == 3

        await gp.parse_job_description("jd text", user_id="u1", redis=r)
        await gp.parse_job_description("jd text", user_id="u1", redis=r)
        assert n["jd"] == 1

        # redis=None must behave exactly like before (always calls LLM)
        await gp.parse_resume("hello resume", user_id="u1", redis=None)
        await gp.parse_resume("hello resume", user_id="u1", redis=None)
        assert n["resume"] == 5
    asyncio.run(run())
