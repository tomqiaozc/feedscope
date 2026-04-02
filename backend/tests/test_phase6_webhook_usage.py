#!/usr/bin/env python3
"""Phase 6 Integration Test — Webhook + Usage.

Checks:
  1. Crypto utils: generate, hash, verify
  2. WebhookRepo methods exist
  3. WebhookUsageRepo methods exist
  4. UsageDailyRepo methods exist
  5. Webhook routes registered (6 endpoints)
  6. External routes registered (5 endpoints)
  7. Usage routes registered (2 endpoints)
  8. Webhook schemas validate
  9. POST /webhooks → create key (returns full key)
 10. GET /webhooks → list keys (no full key)
 11. POST /webhooks/{id}/rotate → new key returned
 12. DELETE /webhooks/{id} → revoked
 13. External API without key → 401
 14. API contract updated with webhook + external + usage endpoints
 15. Total endpoint count
"""

import asyncio
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

        # Check 9: POST /webhooks → create key
        print("\n9. POST /webhooks — create key")
        resp = await client.post("/api/v1/webhooks", json={"name": "Test Key"}, headers=headers)
        check("status 201", resp.status_code == 201, f"got {resp.status_code}")
        body = resp.json()
        key_data = body.get("data", {})
        check("has id", key_data.get("id") is not None)
        check(
            "has full key", key_data.get("key") is not None and key_data["key"].startswith("fsk_")
        )
        check("has prefix", key_data.get("key_prefix") is not None)
        webhook_id = key_data.get("id")
        full_key = key_data.get("key")

        # Check 10: GET /webhooks → list (no full key)
        print("\n10. GET /webhooks — list keys")
        resp = await client.get("/api/v1/webhooks", headers=headers)
        check("status 200", resp.status_code == 200, f"got {resp.status_code}")
        keys = resp.json().get("data", [])
        check("has 1 key", len(keys) == 1, f"got {len(keys)}")
        if keys:
            check("no full key in list", "key" not in keys[0] or keys[0].get("key") is None)

        # Check 11: POST /webhooks/{id}/rotate → new key
        print("\n11. POST /webhooks/{id}/rotate — rotate key")
        resp = await client.post(f"/api/v1/webhooks/{webhook_id}/rotate", headers=headers)
        check("status 200", resp.status_code == 200, f"got {resp.status_code}")
        new_key = resp.json().get("data", {}).get("key")
        check("new key returned", new_key is not None and new_key.startswith("fsk_"))
        check("different from old", new_key != full_key)

        # Check 12: DELETE /webhooks/{id} → revoked
        print("\n12. DELETE /webhooks/{id} — delete key")
        resp = await client.delete(f"/api/v1/webhooks/{webhook_id}", headers=headers)
        check("status 200", resp.status_code == 200, f"got {resp.status_code}")
        # Verify it's gone
        resp = await client.get("/api/v1/webhooks", headers=headers)
        check("empty after delete", len(resp.json().get("data", [])) == 0)

        # Check 13: External API without key → 401
        print("\n13. External API — no key → 401")
        resp = await client.get("/api/v1/external/search", params={"q": "test"})
        check("status 401", resp.status_code == 401, f"got {resp.status_code}")


def main():
    global PASS, FAIL

    print("=" * 60)
    print("Phase 6 Integration Test — Webhook + Usage")
    print("=" * 60)

    # --- Check 1: Crypto utils ---
    print("\n1. Crypto utils")
    from app.utils.crypto import generate_webhook_key, hash_key, key_prefix, verify_key

    key = generate_webhook_key()
    check("key starts with fsk_", key.startswith("fsk_"))
    check("key length > 20", len(key) > 20)
    hashed = hash_key(key)
    check("hash is 64 chars", len(hashed) == 64)
    check("verify correct key", verify_key(key, hashed))
    check("reject wrong key", not verify_key("wrong-key", hashed))
    check("prefix is 8 chars", len(key_prefix(key)) == 8)

    # --- Check 2: WebhookRepo methods ---
    print("\n2. WebhookRepo methods")
    from app.db.repos.webhook_repo import WebhookRepo

    for method in ["list", "get", "create", "delete", "rotate", "verify"]:
        check(f"WebhookRepo.{method}", hasattr(WebhookRepo, method))

    # --- Check 3: WebhookUsageRepo methods ---
    print("\n3. WebhookUsageRepo methods")
    from app.db.repos.webhook_usage_repo import WebhookUsageRepo

    for method in ["record", "get_by_webhook", "get_daily_summary"]:
        check(f"WebhookUsageRepo.{method}", hasattr(WebhookUsageRepo, method))

    # --- Check 4: UsageDailyRepo methods ---
    print("\n4. UsageDailyRepo methods")
    from app.db.repos.usage_daily_repo import UsageDailyRepo

    for method in ["increment", "get_summary"]:
        check(f"UsageDailyRepo.{method}", hasattr(UsageDailyRepo, method))

    # --- Check 5: Webhook routes ---
    print("\n5. Webhook routes registered")
    from app.routes.webhooks import router as webhooks_router

    wh_routes = [r for r in webhooks_router.routes if hasattr(r, "methods")]
    check("6 webhook endpoints", len(wh_routes) == 6, f"got {len(wh_routes)}")

    # --- Check 6: External routes ---
    print("\n6. External routes registered")
    from app.routes.external import router as external_router

    ext_routes = [r for r in external_router.routes if hasattr(r, "methods")]
    check("5 external endpoints", len(ext_routes) == 5, f"got {len(ext_routes)}")

    # --- Check 7: Usage routes ---
    print("\n7. Usage routes registered")
    from app.routes.usage import router as usage_router

    usage_routes = [r for r in usage_router.routes if hasattr(r, "methods")]
    check("2 usage endpoints", len(usage_routes) == 2, f"got {len(usage_routes)}")

    # --- Check 8: Webhook schemas ---
    print("\n8. Webhook schemas")
    from app.schemas.webhooks import (
        UsageSummary,
        WebhookKeyCreate,
    )

    check("WebhookKeyCreate", WebhookKeyCreate(name="test").name == "test")
    check("UsageSummary", UsageSummary(date="2025-01-01", endpoint="/test", count=5).count == 5)

    # --- HTTP checks (9-13) ---
    asyncio.run(run_http_checks())

    # --- Check 14: API contract ---
    print("\n14. API contract updated")
    with open("../shared/api-contract.md") as f:
        contract = f.read()
    check("has /webhooks", "GET | `/api/v1/webhooks`" in contract)
    check("has webhook create", "POST | `/api/v1/webhooks`" in contract)
    check("has webhook rotate", "POST | `/api/v1/webhooks/{id}/rotate`" in contract)
    check("has external search", "GET | `/api/v1/external/search`" in contract)
    check("has external user", "GET | `/api/v1/external/user/{username}`" in contract)
    check("has /usage", "GET | `/api/v1/usage`" in contract)
    check("has /credits", "GET | `/api/v1/credits`" in contract)
    check("has X-Webhook-Key note", "X-Webhook-Key" in contract)

    # --- Check 15: Total endpoint count ---
    print("\n15. Total endpoint count")
    from app.main import app

    total = sum(1 for r in app.routes if hasattr(r, "methods"))
    check("65 endpoints", total == 65, f"got {total}")

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
