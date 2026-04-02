"""Dashboard aggregation endpoint tests."""

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
    from httpx import ASGITransport, AsyncClient

    from app.main import app

    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        headers = {"X-User-Id": TEST_USER_ID}

        # Check 1: GET /api/v1/dashboard returns 200
        print("\n1. GET /api/v1/dashboard — status 200")
        resp = await client.get("/api/v1/dashboard", headers=headers)
        check("status 200", resp.status_code == 200, f"got {resp.status_code}")

        # Check 2: Response has all expected keys
        print("\n2. Response structure")
        body = resp.json()
        check("success is true", body.get("success") is True)
        data = body.get("data", {})
        for key in ["credentials", "ai", "watchlists", "groups", "usage", "credits"]:
            check(f"has '{key}' key", key in data, f"missing '{key}'")

        # Check 3: Credentials is a list
        print("\n3. Credentials shape")
        check("credentials is list", isinstance(data.get("credentials"), list))

        # Check 4: AI is a dict with expected keys
        print("\n4. AI shape")
        ai = data.get("ai", {})
        check("ai is dict", isinstance(ai, dict))
        check("ai has provider_id", "provider_id" in ai)
        check("ai has model", "model" in ai)

        # Check 5: Watchlists is a list
        print("\n5. Watchlists shape")
        check("watchlists is list", isinstance(data.get("watchlists"), list))

        # Check 6: Groups is a list
        print("\n6. Groups shape")
        check("groups is list", isinstance(data.get("groups"), list))

        # Check 7: Usage is a list
        print("\n7. Usage shape")
        check("usage is list", isinstance(data.get("usage"), list))

        # Check 8: Credits is a dict with remaining/total
        print("\n8. Credits shape")
        credits = data.get("credits")
        check("credits is dict", isinstance(credits, dict))
        if isinstance(credits, dict):
            check("has remaining", "remaining" in credits)
            check("has total", "total" in credits)

        # Check 9: Unauthenticated returns 401/422
        print("\n9. Unauthenticated → 401/422")
        resp = await client.get("/api/v1/dashboard")
        check("not 200", resp.status_code in (401, 422), f"got {resp.status_code}")


def main():
    global PASS, FAIL

    print("=" * 60)
    print("Dashboard Aggregation Endpoint Test")
    print("=" * 60)

    # Check 0: Route is registered
    print("\n0. Dashboard route registered")
    from app.routes.dashboard import router as dashboard_router

    routes = [r for r in dashboard_router.routes if hasattr(r, "methods")]
    check("1 dashboard endpoint", len(routes) == 1, f"got {len(routes)}")

    asyncio.run(run_http_checks())

    # Summary
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
