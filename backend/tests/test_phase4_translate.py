#!/usr/bin/env python3
"""Phase 4 integration test — AI Translation (backend-only checks).

Checks:
  1. parse_translation() correctly splits structured AI output
  2. parse_translation() fallback when no markers present
  3. render_prompt() with content only (no quoted)
  4. render_prompt() with quoted content
  5. POST /api/v1/translate with empty text → 400
  6. POST /api/v1/translate without AI config → 503
  7. POST /api/v1/watchlists/{id}/translate without AI config → 503
  8. AI provider registry has expected providers
  9. AiConfig model validates correctly
 10. TranslateRequest/TranslateResponse schemas validate
 11. PostRepo.list_untranslated method exists
 12. batch_translate SSE helper format
 13. API contract updated with translate endpoints
"""

import asyncio
import json
import sys

PASS = 0
FAIL = 0


def check(name: str, ok: bool, detail: str = ""):
    global PASS, FAIL
    if ok:
        PASS += 1
        print(f"  [PASS] {name}")
    else:
        FAIL += 1
        print(f"  [FAIL] {name} — {detail}")


async def run_http_checks():
    """Run all HTTP-based checks in a single event loop."""
    from httpx import ASGITransport, AsyncClient

    from app.main import app

    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        # Check 5: POST /translate empty text → 400
        print("\n5. POST /api/v1/translate — empty text → 400")
        resp = await client.post(
            "/api/v1/translate",
            json={"text": "   "},
            headers={"X-User-Id": "test-user"},
        )
        check("status 400", resp.status_code == 400, f"got {resp.status_code}")
        check("error detail", "required" in resp.json().get("detail", "").lower(), str(resp.json()))

        # Check 6: POST /translate without AI config → 503
        print("\n6. POST /api/v1/translate — no AI config → 503")
        resp2 = await client.post(
            "/api/v1/translate",
            json={"text": "Hello world"},
            headers={"X-User-Id": "nonexistent-user-no-ai-config"},
        )
        check("status 503", resp2.status_code == 503, f"got {resp2.status_code}")

        # Check 7: POST /watchlists/{id}/translate without AI config → 503 or 404
        print("\n7. POST /watchlists/{id}/translate — no AI config → 404 or 503")
        resp3 = await client.post(
            "/api/v1/watchlists/999/translate",
            headers={"X-User-Id": "nonexistent-user-no-ai-config"},
        )
        check("status 404 or 503", resp3.status_code in (404, 503), f"got {resp3.status_code}")


def main():
    global PASS, FAIL

    print("=" * 60)
    print("Phase 4 Integration Test — AI Translation")
    print("=" * 60)

    # --- Check 1: parse_translation structured ---
    print("\n1. parse_translation() — structured output")
    from app.services.translation import parse_translation

    raw = "[翻译]\nHello world\n[锐评]\nGreat post\n[引用翻译]\nQuoted text"
    result = parse_translation(raw)
    check("translation extracted", result.translation == "Hello world")
    check("editorial extracted", result.editorial == "Great post")
    check("quoted_translation extracted", result.quoted_translation == "Quoted text")

    # --- Check 2: parse_translation fallback ---
    print("\n2. parse_translation() — fallback (no markers)")
    result2 = parse_translation("Just plain text response")
    check("fallback uses raw text", result2.translation == "Just plain text response")
    check("fallback editorial is None", result2.editorial is None)

    # --- Check 3: render_prompt without quoted ---
    print("\n3. render_prompt() — content only")
    from app.services.prompt import render_prompt

    prompt = render_prompt("Test post content")
    check("contains content", "Test post content" in prompt)
    check("no quoted block", "引用推文" not in prompt)

    # --- Check 4: render_prompt with quoted ---
    print("\n4. render_prompt() — with quoted content")
    prompt2 = render_prompt("Main post", quoted_content="Quoted post")
    check("contains main content", "Main post" in prompt2)
    check("contains quoted content", "Quoted post" in prompt2)
    check("contains quoted label", "引用推文" in prompt2)

    # --- Checks 5-7: HTTP-based (single event loop) ---
    asyncio.run(run_http_checks())

    # --- Check 8: AI provider registry ---
    print("\n8. AI provider registry")
    from app.services.ai_registry import AI_PROVIDERS

    check("has anthropic", "anthropic" in AI_PROVIDERS)
    check("has openai", "openai" in AI_PROVIDERS)
    check("has custom", "custom" in AI_PROVIDERS)
    check("anthropic sdk_type", AI_PROVIDERS["anthropic"]["sdk_type"] == "anthropic")
    check("openai sdk_type", AI_PROVIDERS["openai"]["sdk_type"] == "openai")

    # --- Check 9: AiConfig model ---
    print("\n9. AiConfig model validation")
    from app.services.translation import AiConfig

    config = AiConfig(
        provider_id="openai",
        api_key="sk-test",
        model="gpt-4o-mini",
    )
    check("AiConfig created", config.provider_id == "openai")
    check("AiConfig defaults", config.sdk_type == "openai")
    check("AiConfig base_url default", config.base_url is None)

    # --- Check 10: Schemas ---
    print("\n10. Pydantic schemas")
    from app.schemas.translate import TranslateRequest, TranslateResponse

    req = TranslateRequest(text="Hello")
    check("TranslateRequest", req.text == "Hello" and req.quoted_text is None)
    resp_model = TranslateResponse(translation="你好", editorial="Good", quoted_translation=None)
    check("TranslateResponse", resp_model.translation == "你好")

    # --- Check 11: PostRepo methods ---
    print("\n11. PostRepo methods exist")
    from app.db.repos.post_repo import PostRepo

    check("list_untranslated method exists", hasattr(PostRepo, "list_untranslated"))
    check("update method exists", hasattr(PostRepo, "update"))

    # --- Check 12: batch_translate SSE helper ---
    print("\n12. batch_translate SSE service")
    from app.services.batch_translate import _sse

    sse_out = _sse("test", {"key": "value"})
    check("SSE format correct", sse_out.startswith("event: test\n"))
    check("SSE data parseable", json.loads(sse_out.split("data: ")[1].strip()) == {"key": "value"})

    # --- Check 13: API contract ---
    print("\n13. API contract updated")
    with open("../shared/api-contract.md") as f:
        contract = f.read()
    check("contract has /translate", "POST | `/api/v1/translate`" in contract)
    check("contract has batch translate", "POST | `/api/v1/watchlists/{id}/translate`" in contract)
    check("contract has SSE events", "event: translating" in contract)
    check("contract has start event", "event: start" in contract)

    # --- Summary ---
    print("\n" + "=" * 60)
    total = PASS + FAIL
    print(f"Results: {PASS}/{total} passed, {FAIL} failed")
    if FAIL > 0:
        print("SOME CHECKS FAILED")
        sys.exit(1)
    else:
        print("ALL CHECKS PASSED")


if __name__ == "__main__":
    main()
