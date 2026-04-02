"use client";

import { useMemo } from "react";
import Link from "next/link";
import {
  CheckCircle2,
  XCircle,
  Sparkles,
  List,
  Users,
  Activity,
  CreditCard,
} from "lucide-react";
import { useBreadcrumbs } from "@/hooks/use-breadcrumbs";
import { useSwrFetch } from "@/hooks/use-swr-fetch";
import { SectionSkeleton } from "@/components/ui/section-skeleton";
import { ErrorBanner } from "@/components/ui/error-banner";
import { Button } from "@/components/ui/button";

const crumbs = [{ label: "Dashboard" }];

interface DashboardData {
  credentials: {
    provider: string;
    has_api_key: boolean;
    has_cookie: boolean;
  }[];
  ai: { provider_id?: string; model?: string };
  watchlists: { id: number; name: string }[];
  groups: { id: number; name: string }[];
  usage: { date: string; endpoint: string; count: number }[];
  credits: { remaining: number; total: number; reset_at: string | null };
}

function StatusCard({
  title,
  children,
  stagger,
  href,
}: {
  title: string;
  children: React.ReactNode;
  stagger: number;
  href?: string;
}) {
  const inner = (
    <div
      className={`rounded-widget bg-secondary/50 p-5 fade-up-stagger-${stagger}`}
    >
      <h3 className="text-sm font-medium text-muted-foreground">{title}</h3>
      <div className="mt-2">{children}</div>
    </div>
  );

  if (href) {
    return (
      <Link
        href={href}
        className="block transition-transform hover:scale-[1.01]"
      >
        {inner}
      </Link>
    );
  }
  return inner;
}

export default function DashboardPage() {
  useBreadcrumbs(crumbs);

  const { data, loading, error } = useSwrFetch<DashboardData>("dashboard");

  const creds = data?.credentials;
  const ai = data?.ai;
  const watchlists = data?.watchlists;
  const groups = data?.groups;
  const credits = data?.credits;

  const hasCredentials = !!creds?.some((c) => c.has_api_key || c.has_cookie);
  const hasAi = !!(ai?.provider_id && ai?.model);

  const usage = data?.usage;
  const totalApiCalls = useMemo(() => {
    if (!usage) return 0;
    return usage.reduce((sum, row) => sum + row.count, 0);
  }, [usage]);

  return (
    <div className="space-y-6">
      <h1 className="text-2xl font-bold fade-up-stagger-1">Dashboard</h1>

      {error && <ErrorBanner message={error || "Failed to load status"} />}

      <div className="grid gap-4 sm:grid-cols-2">
        {/* Credentials card */}
        <StatusCard title="Credentials" stagger={2} href="/settings">
          {loading ? (
            <SectionSkeleton />
          ) : hasCredentials ? (
            <div className="flex items-center gap-2 text-green-600 dark:text-green-400">
              <CheckCircle2 className="h-4 w-4" />
              <span className="text-sm font-medium">
                Twitter API configured
              </span>
            </div>
          ) : (
            <div className="space-y-2">
              <div className="flex items-center gap-2 text-red-600 dark:text-red-400">
                <XCircle className="h-4 w-4" />
                <span className="text-sm">Not configured</span>
              </div>
              <Link href="/settings">
                <Button variant="outline" size="sm">
                  Configure Credentials
                </Button>
              </Link>
            </div>
          )}
        </StatusCard>

        {/* AI Provider card */}
        <StatusCard title="AI Provider" stagger={3} href="/ai-settings">
          {loading ? (
            <SectionSkeleton />
          ) : hasAi ? (
            <div className="flex items-center gap-2">
              <Sparkles className="h-4 w-4 text-muted-foreground" />
              <span className="text-sm font-medium">
                {ai!.provider_id} / {ai!.model}
              </span>
            </div>
          ) : (
            <div className="flex items-center gap-2 text-muted-foreground">
              <XCircle className="h-4 w-4" />
              <span className="text-sm">Not configured</span>
            </div>
          )}
        </StatusCard>

        {/* Watchlists card */}
        <StatusCard title="Watchlists" stagger={4} href="/watchlist">
          {loading ? (
            <SectionSkeleton />
          ) : (
            <div className="flex items-center gap-2">
              <List className="h-4 w-4 text-muted-foreground" />
              <span className="text-xl font-bold">
                {watchlists?.length ?? 0}
              </span>
              <span className="text-sm text-muted-foreground">watchlists</span>
            </div>
          )}
        </StatusCard>

        {/* Groups card */}
        <StatusCard title="Groups" stagger={5} href="/groups">
          {loading ? (
            <SectionSkeleton />
          ) : (
            <div className="flex items-center gap-2">
              <Users className="h-4 w-4 text-muted-foreground" />
              <span className="text-xl font-bold">
                {groups?.length ?? 0}
              </span>
              <span className="text-sm text-muted-foreground">groups</span>
            </div>
          )}
        </StatusCard>

        {/* API Calls (7d) card */}
        <StatusCard title="API Calls (7d)" stagger={6} href="/usage">
          {loading ? (
            <SectionSkeleton />
          ) : (
            <div className="flex items-center gap-2">
              <Activity className="h-4 w-4 text-muted-foreground" />
              <span className="text-xl font-bold">
                {totalApiCalls.toLocaleString()}
              </span>
              <span className="text-sm text-muted-foreground">calls</span>
            </div>
          )}
        </StatusCard>

        {/* Credits card */}
        <StatusCard title="Credits Remaining" stagger={7} href="/usage">
          {loading ? (
            <SectionSkeleton />
          ) : credits ? (
            <div className="flex items-center gap-2">
              <CreditCard className="h-4 w-4 text-muted-foreground" />
              <span className="text-xl font-bold">
                {credits.remaining.toLocaleString()}
              </span>
              <span className="text-sm text-muted-foreground">remaining</span>
            </div>
          ) : (
            <div className="flex items-center gap-2 text-muted-foreground">
              <CreditCard className="h-4 w-4" />
              <span className="text-sm">No credit data</span>
            </div>
          )}
        </StatusCard>
      </div>
    </div>
  );
}
