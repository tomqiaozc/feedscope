import { NextRequest, NextResponse } from "next/server";
import { auth } from "@/lib/auth";

export const dynamic = "force-dynamic";

const BACKEND_URL = process.env.BACKEND_URL || "http://localhost:8000";

async function proxyRequest(
  request: NextRequest,
  { params }: { params: Promise<{ path: string[] }> }
) {
  // Read the body early, before any async ops that might consume it
  let body: string | undefined;
  if (request.method !== "GET" && request.method !== "HEAD") {
    body = await request.text();
  }

  const { path } = await params;
  const joinedPath = path.join("/");

  // Health endpoint: no auth required
  const isHealth = joinedPath === "health";

  // Validate session for non-health routes
  if (!isHealth) {
    const session = await auth();
    if (!session?.user?.id) {
      return NextResponse.json(
        { success: false, data: null, error: "Unauthorized" },
        { status: 401 }
      );
    }

    // Build headers with authenticated user ID
    const headers = new Headers();
    const forwardHeaders = ["content-type", "accept"];
    for (const key of forwardHeaders) {
      const value = request.headers.get(key);
      if (value) headers.set(key, value);
    }
    headers.set("x-user-id", session.user.id);

    return doProxy(request, joinedPath, headers, body);
  }

  // Health endpoint — proxy without auth
  const headers = new Headers();
  const forwardHeaders = ["content-type", "accept"];
  for (const key of forwardHeaders) {
    const value = request.headers.get(key);
    if (value) headers.set(key, value);
  }

  return doProxy(request, joinedPath, headers, body);
}

async function doProxy(
  request: NextRequest,
  joinedPath: string,
  headers: Headers,
  body?: string
) {
  const targetPath =
    joinedPath === "health" ? "/health" : `/api/v1/${joinedPath}`;
  const url = new URL(targetPath, BACKEND_URL);

  // Forward query params
  request.nextUrl.searchParams.forEach((value, key) => {
    url.searchParams.set(key, value);
  });

  const fetchInit: RequestInit = {
    method: request.method,
    headers,
  };

  // Forward body for non-GET/HEAD requests
  if (body !== undefined) {
    fetchInit.body = body;
  }

  try {
    const response = await fetch(url.toString(), fetchInit);

    // SSE streaming passthrough
    const contentType = response.headers.get("content-type") || "";
    if (contentType.includes("text/event-stream")) {
      return new Response(response.body, {
        status: response.status,
        headers: {
          "Content-Type": "text/event-stream",
          "Cache-Control": "no-cache",
          Connection: "keep-alive",
          "X-Accel-Buffering": "no",
        },
      });
    }

    // Regular response
    const responseHeaders = new Headers();
    response.headers.forEach((value, key) => {
      if (key.toLowerCase() !== "transfer-encoding") {
        responseHeaders.set(key, value);
      }
    });

    const responseBody = await response.text();
    return new NextResponse(responseBody, {
      status: response.status,
      headers: responseHeaders,
    });
  } catch (error) {
    console.error("Proxy error:", error);
    return NextResponse.json(
      { success: false, data: null, error: "Backend unavailable" },
      { status: 502 }
    );
  }
}

export const GET = proxyRequest;
export const POST = proxyRequest;
export const PUT = proxyRequest;
export const DELETE = proxyRequest;
export const PATCH = proxyRequest;
