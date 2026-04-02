"use client";

import useSWR, { type SWRConfiguration } from "swr";
import { fetchApi } from "@/lib/api";

export function useSwrFetch<T = unknown>(
  endpoint: string | null,
  options?: SWRConfiguration,
) {
  const { data, error, isLoading, mutate } = useSWR<T>(
    endpoint,
    (ep: string) => fetchApi<T>(ep),
    {
      revalidateOnFocus: false,
      dedupingInterval: 10_000,
      ...options,
    },
  );

  return {
    data: data ?? null,
    loading: isLoading,
    error: error
      ? error instanceof Error
        ? error.message
        : "Unknown error"
      : null,
    refetch: () => mutate(),
  };
}
