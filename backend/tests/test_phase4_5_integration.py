#!/usr/bin/env python3
"""Phase 4+5 Integration Test — Translation + Explore + Groups.

Checks:
  1. parse_translation() structured output
  2. parse_translation() fallback
  3. render_prompt() content only
  4. render_prompt() with quoted content
  5. POST /translate empty text → 400
  6. POST /translate no AI config → 503
  7. AI provider registry entries
  8. AiConfig + TranslateRequest/TranslateResponse schemas
  9. API contract has translate endpoints
 10. API contract has explore endpoints (12)
 11. API contract has group endpoints (9)
 12. API contract has profile refresh endpoint
 13. Explore routes registered (12 endpoints)
 14. Group routes registered (9 endpoints)
 15. Profile route registered (1 endpoint)
 16. GroupRepo methods exist
 17. GroupMemberRepo methods exist
 18. ProfileRepo methods exist
 19. PostRepo.list_untranslated + update methods exist
 20. Explore schemas (PostOut, UserInfoOut) validate
 21. Group schemas validate
 22. batch_translate SSE format
 23. GET /explore/search without creds → 503
 24. GET /groups → empty list for new user
 25. POST /groups → create group
 26. Total endpoint count matches expected
"""

import asyncio
import json
import sys
import uuid

PASS = 0
FAIL = 0
TEST_USER_ID = str(uuid.uuid4())


def check(name: str, ok: bool, detail: str = ""):
    global PASS, FAIL
    if ok:
        PASS += 1
        print(f"  [PASS] {name}")
    else:
        FAIL += 1
        print(f"  [FAIL] {name} — {detail}")


async def run_http_checks():
    """Run HTTP-based checks in a single event loop."""
    from httpx import ASGITransport, AsyncClient

    from app.main import app

    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        headers = {"X-User-Id": TEST_USER_ID}

        # Check 5: POST /translate empty text → 400
        print("\n5. POST /translate — empty text → 400")
        resp = await client.post("/api/v1/translate", json={"text": "   "}, headers=headers)
        check("status 400", resp.status_code == 400, f"got {resp.status_code}")

        # Check 6: POST /translate no AI config → 503
        print("\n6. POST /translate — no AI config → 503")
        resp = await client.post("/api/v1/translate", json={"text": "Hello"}, headers=headers)
        check("status 503", resp.status_code == 503, f"got {resp.status_code}")

        # Check 23: GET /explore/search without creds → 503
        print("\n23. GET /explore/search — no creds → 503")
        resp = await client.get("/api/v1/explore/search", params={"q": "test"}, headers=headers)
        check("status 503", resp.status_code == 503, f"got {resp.status_code}")

        # Check 24: GET /groups → empty list
        print("\n24. GET /groups — empty list for new user")
        resp = await client.get("/api/v1/groups", headers=headers)
        check("status 200", resp.status_code == 200, f"got {resp.status_code}")
        body = resp.json()
        check("success true", body.get("success") is True)
        check("data is list", isinstance(body.get("data"), list))

        # Check 25: POST /groups → create group
        print("\n25. POST /groups — create group")
        resp = await client.post(
            "/api/v1/groups",
            json={"name": "Test Group", "description": "Integration test"},
            headers=headers,
        )
        check("status 201", resp.status_code == 201, f"got {resp.status_code}")
        body = resp.json()
        check("group has id", body.get("data", {}).get("id") is not None)
        check("group name matches", body.get("data", {}).get("name") == "Test Group")


def main():
    global PASS, FAIL

    print("=" * 60)
    print("Phase 4+5 Integration Test")
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
    print("\n2. parse_translation() — fallback")
    result2 = parse_translation("Plain text")
    check("fallback uses raw text", result2.translation == "Plain text")

    # --- Check 3: render_prompt content only ---
    print("\n3. render_prompt() — content only")
    from app.services.prompt import render_prompt

    prompt = render_prompt("Test content")
    check("contains content", "Test content" in prompt)
    check("no quoted block", "引用推文" not in prompt)

    # --- Check 4: render_prompt with quoted ---
    print("\n4. render_prompt() — with quoted")
    prompt2 = render_prompt("Main", quoted_content="Quoted")
    check("contains quoted", "Quoted" in prompt2)

    # --- HTTP checks (5, 6, 23, 24, 25) ---
    asyncio.run(run_http_checks())

    # --- Check 7: AI registry ---
    print("\n7. AI provider registry")
    from app.services.ai_registry import AI_PROVIDERS

    check("3 providers", len(AI_PROVIDERS) == 3, f"got {len(AI_PROVIDERS)}")
    check("anthropic present", "anthropic" in AI_PROVIDERS)
    check("openai present", "openai" in AI_PROVIDERS)

    # --- Check 8: Schemas ---
    print("\n8. Translation schemas")
    from app.schemas.translate import TranslateRequest, TranslateResponse
    from app.services.translation import AiConfig

    config = AiConfig(provider_id="openai", api_key="sk-test", model="gpt-4o-mini")
    check("AiConfig valid", config.sdk_type == "openai")
    check("TranslateRequest valid", TranslateRequest(text="hi").text == "hi")
    check("TranslateResponse valid", TranslateResponse(translation="你好").translation == "你好")

    # --- Check 9: Contract has translate ---
    print("\n9. API contract — translate")
    with open("../shared/api-contract.md") as f:
        contract = f.read()
    check("has /translate", "POST | `/api/v1/translate`" in contract)
    check("has batch translate", "POST | `/api/v1/watchlists/{id}/translate`" in contract)

    # --- Check 10: Contract has explore ---
    print("\n10. API contract — explore (12 endpoints)")
    check("has /explore/search", "`/api/v1/explore/search`" in contract)
    check("has /explore/user/{username}", "`/api/v1/explore/user/{username}`" in contract)
    check(
        "has /explore/user/{username}/tweets",
        "`/api/v1/explore/user/{username}/tweets`" in contract,
    )
    check("has /explore/bookmarks", "`/api/v1/explore/bookmarks`" in contract)
    check("has /explore/tweet/{tweet_id}", "`/api/v1/explore/tweet/{tweet_id}`" in contract)
    check(
        "has /explore/tweet/{tweet_id}/replies",
        "`/api/v1/explore/tweet/{tweet_id}/replies`" in contract,
    )

    # --- Check 11: Contract has groups ---
    print("\n11. API contract — groups (9 endpoints)")
    check("has GET /groups", "GET | `/api/v1/groups`" in contract)
    check("has POST /groups", "POST | `/api/v1/groups`" in contract)
    check("has PUT /groups/{id}", "PUT | `/api/v1/groups/{id}`" in contract)
    check("has DELETE /groups/{id}", "DELETE | `/api/v1/groups/{id}`" in contract)
    check("has POST batch members", "POST | `/api/v1/groups/{id}/members/batch`" in contract)
    check("has DELETE batch members", "DELETE | `/api/v1/groups/{id}/members/batch`" in contract)

    # --- Check 12: Contract has profiles ---
    print("\n12. API contract — profiles")
    check("has /profiles/refresh", "`/api/v1/profiles/refresh`" in contract)

    # --- Check 13: Explore routes count ---
    print("\n13. Explore routes registered")
    from app.routes.explore import router as explore_router

    explore_routes = [r for r in explore_router.routes if hasattr(r, "methods")]
    check("12 explore endpoints", len(explore_routes) == 12, f"got {len(explore_routes)}")

    # --- Check 14: Group routes count ---
    print("\n14. Group routes registered")
    from app.routes.groups import router as groups_router

    group_routes = [r for r in groups_router.routes if hasattr(r, "methods")]
    check("9 group endpoints", len(group_routes) == 9, f"got {len(group_routes)}")

    # --- Check 15: Profile route ---
    print("\n15. Profile route registered")
    from app.routes.profiles import router as profiles_router

    profile_routes = [r for r in profiles_router.routes if hasattr(r, "methods")]
    check("1 profile endpoint", len(profile_routes) == 1, f"got {len(profile_routes)}")

    # --- Check 16: GroupRepo methods ---
    print("\n16. GroupRepo methods")
    from app.db.repos.group_repo import GroupRepo

    for method in ["list", "get", "create", "update", "delete"]:
        check(f"GroupRepo.{method} exists", hasattr(GroupRepo, method))

    # --- Check 17: GroupMemberRepo methods ---
    print("\n17. GroupMemberRepo methods")
    from app.db.repos.group_member_repo import GroupMemberRepo

    for method in ["list", "get", "create", "batch_create", "delete", "batch_delete"]:
        check(f"GroupMemberRepo.{method} exists", hasattr(GroupMemberRepo, method))

    # --- Check 18: ProfileRepo methods ---
    print("\n18. ProfileRepo methods")
    from app.db.repos.profile_repo import ProfileRepo

    for method in ["get_by_username", "upsert", "batch_upsert"]:
        check(f"ProfileRepo.{method} exists", hasattr(ProfileRepo, method))

    # --- Check 19: PostRepo new methods ---
    print("\n19. PostRepo.list_untranslated + update")
    from app.db.repos.post_repo import PostRepo

    check("PostRepo.list_untranslated exists", hasattr(PostRepo, "list_untranslated"))
    check("PostRepo.update exists", hasattr(PostRepo, "update"))

    # --- Check 20: Explore schemas ---
    print("\n20. Explore schemas")
    from app.schemas.explore import PostOut, UserInfoOut

    post = PostOut(platform_post_id="123", content="Test")
    check("PostOut valid", post.platform_post_id == "123")
    user = UserInfoOut(username="testuser")
    check("UserInfoOut valid", user.username == "testuser")

    # --- Check 21: Group schemas ---
    print("\n21. Group schemas")
    from app.schemas.groups import (
        BatchDeleteRequest,
        BatchMemberCreate,
        GroupCreate,
        GroupMemberCreate,
        ProfileRefreshRequest,
    )

    check("GroupCreate valid", GroupCreate(name="Test").name == "Test")
    check(
        "BatchMemberCreate valid",
        len(BatchMemberCreate(members=[GroupMemberCreate(username="u1")]).members) == 1,
    )
    check("BatchDeleteRequest valid", len(BatchDeleteRequest(member_ids=[1, 2]).member_ids) == 2)
    check(
        "ProfileRefreshRequest valid",
        len(ProfileRefreshRequest(usernames=["a", "b"]).usernames) == 2,
    )

    # --- Check 22: batch_translate SSE ---
    print("\n22. batch_translate SSE format")
    from app.services.sse_utils import sse_event

    sse = sse_event("test", {"key": "value"})
    check("SSE format", sse.startswith("event: test\n"))
    check("SSE parseable", json.loads(sse.split("data: ")[1].strip()) == {"key": "value"})

    # --- Check 26: Total endpoint count ---
    print("\n26. Total endpoint count")
    from app.main import app

    total = sum(1 for r in app.routes if hasattr(r, "methods"))
    check("50 endpoints", total == 50, f"got {total}")

    # --- Summary ---
    print("\n" + "=" * 60)
    total_checks = PASS + FAIL
    print(f"Results: {PASS}/{total_checks} passed, {FAIL} failed")
    if FAIL > 0:
        print("SOME CHECKS FAILED")
        sys.exit(1)
    else:
        print("ALL CHECKS PASSED")


if __name__ == "__main__":
    main()
