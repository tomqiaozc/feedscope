"use client";

import { cn } from "@/lib/utils";

interface StatusMessageProps {
  type: "success" | "error";
  message: string;
  className?: string;
}

export function StatusMessage({ type, message, className }: StatusMessageProps) {
  return (
    <div
      className={cn(
        "rounded-md px-3 py-2 text-sm",
        type === "success"
          ? "bg-green-50 text-green-800 dark:bg-green-950 dark:text-green-200"
          : "bg-red-50 text-red-800 dark:bg-red-950 dark:text-red-200",
        className
      )}
    >
      {message}
    </div>
  );
}
