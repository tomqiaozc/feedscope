"use client";

import { createContext, useContext, useState, useCallback } from "react";

export interface BreadcrumbItem {
  label: string;
  href?: string;
}

interface BreadcrumbsContextValue {
  items: BreadcrumbItem[];
  setBreadcrumbs: (items: BreadcrumbItem[]) => void;
}

const BreadcrumbsContext = createContext<BreadcrumbsContextValue>({
  items: [],
  setBreadcrumbs: () => {},
});

export function BreadcrumbsProvider({
  children,
}: {
  children: React.ReactNode;
}) {
  const [items, setItems] = useState<BreadcrumbItem[]>([]);

  const setBreadcrumbs = useCallback((newItems: BreadcrumbItem[]) => {
    setItems(newItems);
  }, []);

  return (
    <BreadcrumbsContext value={{ items, setBreadcrumbs }}>
      {children}
    </BreadcrumbsContext>
  );
}

export function useBreadcrumbsContext() {
  return useContext(BreadcrumbsContext);
}
