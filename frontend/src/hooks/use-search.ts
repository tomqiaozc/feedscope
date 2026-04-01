"use client";

import { useState, useCallback, useRef } from "react";
import { fetchApi } from "@/lib/api";

interface UseSearchResult<T> {
  data: T[] | null;
  loading: boolean;
  error: string | null;
  searched: boolean;
  execute: (endpoint: string, params?: Record<string, string>) => void;
  reset: () => void;
}

export function useSearch<T = unknown>(): UseSearchResult<T> {
  const [data, setData] = useState<T[] | null>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [searched, setSearched] = useState(false);
  const abortRef = useRef<AbortController | null>(null);

  const execute = useCallback(
    async (endpoint: string, params?: Record<string, string>) => {
      // Abort any in-flight request to prevent stale results
      abortRef.current?.abort();
      const controller = new AbortController();
      abortRef.current = controller;

      setLoading(true);
      setError(null);
      setSearched(true);
      try {
        const query = params
          ? "?" + new URLSearchParams(params).toString()
          : "";
        const result = await fetchApi<T[]>(`${endpoint}${query}`, {
          signal: controller.signal,
        });
        if (!controller.signal.aborted) {
          setData(result);
        }
      } catch (err) {
        if (controller.signal.aborted) return;
        setError(err instanceof Error ? err.message : "Unknown error");
        setData(null);
      } finally {
        if (!controller.signal.aborted) {
          setLoading(false);
        }
      }
    },
    []
  );

  const reset = useCallback(() => {
    abortRef.current?.abort();
    setData(null);
    setLoading(false);
    setError(null);
    setSearched(false);
  }, []);

  return { data, loading, error, searched, execute, reset };
}
