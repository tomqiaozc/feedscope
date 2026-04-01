"use client";

import { useEffect, useRef } from "react";
import {
  useBreadcrumbsContext,
  type BreadcrumbItem,
} from "@/components/layout/breadcrumbs-context";

export function useBreadcrumbs(items: BreadcrumbItem[]) {
  const { setBreadcrumbs } = useBreadcrumbsContext();
  const prevKey = useRef("");

  useEffect(() => {
    const key = JSON.stringify(items);
    if (key === prevKey.current) return;
    prevKey.current = key;
    setBreadcrumbs(items);
    return () => setBreadcrumbs([]);
  }, [setBreadcrumbs, items]);
}
