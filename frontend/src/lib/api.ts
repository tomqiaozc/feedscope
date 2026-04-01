interface ApiResponse<T = unknown> {
  success: boolean;
  data: T;
  error: string | null;
}

export class ApiError extends Error {
  constructor(
    message: string,
    public status: number,
    public data: unknown = null
  ) {
    super(message);
    this.name = "ApiError";
  }
}

export async function fetchApi<T = unknown>(
  path: string,
  options?: RequestInit
): Promise<T> {
  const res = await fetch(`/api/proxy/${path}`, {
    credentials: "include",
    ...options,
    headers: {
      "Content-Type": "application/json",
      ...options?.headers,
    },
  });

  if (!res.ok) {
    const body = await res.json().catch(() => null);
    throw new ApiError(
      body?.error ?? `Request failed with status ${res.status}`,
      res.status,
      body?.data
    );
  }

  const body: ApiResponse<T> = await res.json();

  if (!body.success) {
    throw new ApiError(body.error ?? "Unknown error", res.status, body.data);
  }

  return body.data;
}
