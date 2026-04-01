"use client";

import { useState, useMemo } from "react";
import { Activity, Webhook, CreditCard, ArrowUpDown } from "lucide-react";
import { useBreadcrumbs } from "@/hooks/use-breadcrumbs";
import { useFetch } from "@/hooks/use-fetch";
import { SectionSkeleton } from "@/components/ui/section-skeleton";
import { ErrorBanner } from "@/components/ui/error-banner";
import { EmptyState } from "@/components/ui/empty-state";
import type { UsageSummary, CreditsInfo } from "@/types/usage";

const crumbs = [{ label: "Usage" }];

function formatDate(d: Date): string {
  return d.toISOString().slice(0, 10);
}

function defaultRange(): { from: string; to: string } {
  const to = new Date();
  const from = new Date();
  from.setDate(from.getDate() - 30);
  return { from: formatDate(from), to: formatDate(to) };
}

type SortKey = "date" | "count";
type SortDir = "asc" | "desc";

export default function UsagePage() {
  useBreadcrumbs(crumbs);

  const [range, setRange] = useState(defaultRange);
  const [sortKey, setSortKey] = useState<SortKey>("date");
  const [sortDir, setSortDir] = useState<SortDir>("desc");

  const usageEndpoint = `usage?date_from=${range.from}&date_to=${range.to}`;

  const { data: usage, loading: usageLoading, error: usageError } =
    useFetch<UsageSummary[]>(usageEndpoint);

  const { data: credits, loading: creditsLoading, error: creditsError } =
    useFetch<CreditsInfo>("credits");

  // Compute summary from usage data
  const summary = useMemo(() => {
    if (!usage) return { total: 0, webhook: 0 };
    let total = 0;
    let webhook = 0;
    for (const row of usage) {
      total += row.count;
      if (row.endpoint.startsWith("/webhook") || row.endpoint.startsWith("webhook")) {
        webhook += row.count;
      }
    }
    return { total, webhook };
  }, [usage]);

  // Group by date with subtotals
  const grouped = useMemo(() => {
    if (!usage || usage.length === 0) return [];

    const sorted = [...usage].sort((a, b) => {
      if (sortKey === "date") {
        const cmp = a.date.localeCompare(b.date);
        return sortDir === "desc" ? -cmp : cmp;
      }
      const cmp = a.count - b.count;
      return sortDir === "desc" ? -cmp : cmp;
    });

    // Group by date
    const groups: { date: string; rows: UsageSummary[]; subtotal: number }[] = [];
    let current: (typeof groups)[number] | null = null;

    for (const row of sorted) {
      if (!current || current.date !== row.date) {
        current = { date: row.date, rows: [], subtotal: 0 };
        groups.push(current);
      }
      current.rows.push(row);
      current.subtotal += row.count;
    }

    return groups;
  }, [usage, sortKey, sortDir]);

  function toggleSort(key: SortKey) {
    if (sortKey === key) {
      setSortDir((d) => (d === "desc" ? "asc" : "desc"));
    } else {
      setSortKey(key);
      setSortDir("desc");
    }
  }

  return (
    <div className="space-y-6">
      <h1 className="text-2xl font-bold fade-up-stagger-1">Usage</h1>

      {/* Date range */}
      <div className="flex flex-wrap items-center gap-3 fade-up-stagger-1">
        <label className="text-sm text-muted-foreground">From</label>
        <input
          type="date"
          value={range.from}
          onChange={(e) => setRange((r) => ({ ...r, from: e.target.value }))}
          className="rounded-lg border border-border bg-background px-3 py-1.5 text-sm outline-none focus:border-ring focus:ring-2 focus:ring-ring/50"
        />
        <label className="text-sm text-muted-foreground">To</label>
        <input
          type="date"
          value={range.to}
          onChange={(e) => setRange((r) => ({ ...r, to: e.target.value }))}
          className="rounded-lg border border-border bg-background px-3 py-1.5 text-sm outline-none focus:border-ring focus:ring-2 focus:ring-ring/50"
        />
      </div>

      {/* Summary cards */}
      <div className="grid gap-4 sm:grid-cols-3 fade-up-stagger-2">
        <SummaryCard
          icon={<Activity className="h-5 w-5 text-blue-500" />}
          label="Total API Calls"
          value={usageLoading ? "..." : summary.total.toLocaleString()}
        />
        <SummaryCard
          icon={<Webhook className="h-5 w-5 text-purple-500" />}
          label="Webhook Calls"
          value={usageLoading ? "..." : summary.webhook.toLocaleString()}
        />
        <SummaryCard
          icon={<CreditCard className="h-5 w-5 text-green-500" />}
          label="Credits Remaining"
          value={creditsLoading ? "..." : credits ? credits.remaining.toLocaleString() : "—"}
        />
      </div>

      {/* Credits detail */}
      {creditsError && <ErrorBanner message={creditsError} />}
      {credits && (
        <div className="rounded-widget bg-secondary/50 p-4 fade-up-stagger-2">
          <h2 className="text-sm font-medium mb-2">TweAPI Credits</h2>
          <div className="flex flex-wrap gap-6 text-sm">
            <div>
              <span className="text-muted-foreground">Used this period:</span>{" "}
              <span className="font-medium">{credits.used.toLocaleString()}</span>
            </div>
            <div>
              <span className="text-muted-foreground">Remaining:</span>{" "}
              <span className="font-medium">{credits.remaining.toLocaleString()}</span>
            </div>
            <div>
              <span className="text-muted-foreground">Period:</span>{" "}
              <span className="font-medium">{credits.period_start} — {credits.period_end}</span>
            </div>
          </div>
          {/* Usage bar */}
          {(credits.used + credits.remaining) > 0 && (
            <div className="mt-3 h-2 rounded-full bg-muted overflow-hidden">
              <div
                className="h-full rounded-full bg-green-500 transition-all"
                style={{
                  width: `${Math.round(
                    (credits.remaining / (credits.used + credits.remaining)) * 100,
                  )}%`,
                }}
              />
            </div>
          )}
        </div>
      )}

      {/* Usage table */}
      {usageError && <ErrorBanner message={usageError} />}

      {usageLoading ? (
        <SectionSkeleton />
      ) : grouped.length > 0 ? (
        <div className="overflow-x-auto fade-up-stagger-2">
          <table className="w-full text-sm">
            <thead>
              <tr className="border-b border-border text-left text-xs text-muted-foreground">
                <th className="pb-2 pr-4 font-medium">
                  <button
                    className="inline-flex items-center gap-1 hover:text-foreground transition-colors"
                    onClick={() => toggleSort("date")}
                  >
                    Date
                    <ArrowUpDown className="h-3 w-3" />
                  </button>
                </th>
                <th className="pb-2 pr-4 font-medium">Endpoint</th>
                <th className="pb-2 font-medium text-right">
                  <button
                    className="inline-flex items-center gap-1 hover:text-foreground transition-colors ml-auto"
                    onClick={() => toggleSort("count")}
                  >
                    Count
                    <ArrowUpDown className="h-3 w-3" />
                  </button>
                </th>
              </tr>
            </thead>
            <tbody className="divide-y divide-border">
              {grouped.map((group) => (
                <GroupRows key={group.date} group={group} />
              ))}
            </tbody>
          </table>
        </div>
      ) : (
        <EmptyState
          title="No usage data"
          message="No API calls recorded for this date range."
        />
      )}
    </div>
  );
}

function SummaryCard({
  icon,
  label,
  value,
}: {
  icon: React.ReactNode;
  label: string;
  value: string;
}) {
  return (
    <div className="rounded-widget bg-secondary/50 p-4">
      <div className="flex items-center gap-3">
        {icon}
        <div>
          <p className="text-xs text-muted-foreground">{label}</p>
          <p className="text-xl font-bold">{value}</p>
        </div>
      </div>
    </div>
  );
}

function GroupRows({
  group,
}: {
  group: { date: string; rows: UsageSummary[]; subtotal: number };
}) {
  return (
    <>
      {group.rows.map((row, i) => (
        <tr key={`${row.date}-${row.endpoint}`} className="group">
          <td className="py-2.5 pr-4 text-muted-foreground">
            {i === 0 ? row.date : ""}
          </td>
          <td className="py-2.5 pr-4">
            <code className="text-xs">{row.endpoint}</code>
          </td>
          <td className="py-2.5 text-right font-medium tabular-nums">
            {row.count.toLocaleString()}
          </td>
        </tr>
      ))}
      {group.rows.length > 1 && (
        <tr className="bg-secondary/30">
          <td className="py-1.5 pr-4 text-xs text-muted-foreground font-medium">
            {group.date} total
          </td>
          <td />
          <td className="py-1.5 text-right text-xs font-bold tabular-nums">
            {group.subtotal.toLocaleString()}
          </td>
        </tr>
      )}
    </>
  );
}
