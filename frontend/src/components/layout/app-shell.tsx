"use client";

import { useState, useEffect } from "react";
import { Menu } from "lucide-react";
import { cn } from "@/lib/utils";
import { useMobile } from "@/hooks/use-mobile";
import { Button } from "@/components/ui/button";
import { Breadcrumbs } from "./breadcrumbs";
import { ThemeToggle } from "./theme-toggle";
import { Sidebar, useSidebarCollapsed } from "./sidebar";

export function AppShell({ children }: { children: React.ReactNode }) {
  const mobile = useMobile();
  const { collapsed, toggle } = useSidebarCollapsed();
  const [mobileOpen, setMobileOpen] = useState(false);

  useEffect(() => {
    if (!mobileOpen) return;
    function onKeyDown(e: KeyboardEvent) {
      if (e.key === "Escape") setMobileOpen(false);
    }
    document.addEventListener("keydown", onKeyDown);
    return () => document.removeEventListener("keydown", onKeyDown);
  }, [mobileOpen]);

  return (
    <div className="flex h-screen overflow-hidden bg-background">
      {/* Desktop sidebar */}
      {!mobile && (
        <Sidebar collapsed={collapsed} onToggle={toggle} />
      )}

      {/* Mobile overlay sidebar */}
      {mobile && mobileOpen && (
        <>
          <div
            className="fixed inset-0 z-40 bg-black/50"
            onClick={() => setMobileOpen(false)}
          />
          <div className="fixed inset-y-0 left-0 z-50">
            <Sidebar
              collapsed={false}
              onToggle={toggle}
              mobile
              onClose={() => setMobileOpen(false)}
            />
          </div>
        </>
      )}

      {/* Main content */}
      <div className="flex flex-1 flex-col overflow-hidden">
        {/* Header */}
        <header className="flex h-14 shrink-0 items-center justify-between border-b border-border px-4">
          <div className="flex items-center gap-3">
            {mobile && (
              <Button
                variant="ghost"
                size="icon"
                onClick={() => setMobileOpen(true)}
              >
                <Menu className="h-4 w-4" />
              </Button>
            )}
            <Breadcrumbs />
          </div>
          <div className="flex items-center gap-2">
            <ThemeToggle />
            <div className="h-7 w-7 rounded-full bg-muted" title="User" />
          </div>
        </header>

        {/* Content area */}
        <main
          className={cn(
            "flex-1 overflow-y-auto p-4",
            !mobile && "p-6"
          )}
        >
          <div
            className={cn(
              "mx-auto rounded-card bg-card shadow-sm",
              !mobile && "p-6",
              mobile && "p-4"
            )}
          >
            {children}
          </div>
        </main>
      </div>
    </div>
  );
}
