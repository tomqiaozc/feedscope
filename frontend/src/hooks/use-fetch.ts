"use client";

import { useState, useEffect, useRef, useCallback } from "react";
import { fetchApi } from "@/lib/api";

interface UseFetchResult<T> {
  data: T | null;
  loading: boolean;
  error: string | null;
  refetch: () => void;
}

export function useFetch<T = unknown>(
  endpoint: string,
  options?: { skip?: boolean }
): UseFetchResult<T> {
  const [data, setData] = useState<T | null>(null);
  const [loading, setLoading] = useState(!options?.skip);
  const [error, setError] = useState<string | null>(null);
  const didMount = useRef(false);
  const prevEndpoint = useRef(endpoint);

  const doFetch = useCallback(async () => {
    setLoading(true);
    setError(null);
    try {
      const result = await fetchApi<T>(endpoint);
      setData(result);
    } catch (err) {
      setError(err instanceof Error ? err.message : "Unknown error");
    } finally {
      setLoading(false);
    }
  }, [endpoint]);

  useEffect(() => {
    if (options?.skip) return;
    if (prevEndpoint.current !== endpoint) {
      prevEndpoint.current = endpoint;
      didMount.current = false;
    }
    if (didMount.current) return;
    didMount.current = true;
    doFetch();
  }, [doFetch, options?.skip, endpoint]);

  const refetch = useCallback(() => {
    didMount.current = false;
    doFetch();
  }, [doFetch]);

  return { data, loading, error, refetch };
}
