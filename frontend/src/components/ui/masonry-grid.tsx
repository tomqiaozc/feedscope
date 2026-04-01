"use client";

import { useColumns } from "@/hooks/use-columns";
import { cn } from "@/lib/utils";

interface MasonryGridProps {
  children: React.ReactNode;
  gap?: number;
  className?: string;
}

export function MasonryGrid({ children, gap = 16, className }: MasonryGridProps) {
  const columns = useColumns();

  return (
    <div
      className={cn("w-full", className)}
      style={{
        columns,
        columnGap: `${gap}px`,
      }}
    >
      {Array.isArray(children)
        ? children.map((child, i) => (
            <div
              key={i}
              style={{
                breakInside: "avoid",
                marginBottom: `${gap}px`,
              }}
            >
              {child}
            </div>
          ))
        : children}
    </div>
  );
}
