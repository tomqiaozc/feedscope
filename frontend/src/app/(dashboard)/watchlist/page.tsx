"use client";

import { Suspense, useState, useEffect } from "react";
import { useSearchParams } from "next/navigation";
import { Plus } from "lucide-react";
import { useBreadcrumbs } from "@/hooks/use-breadcrumbs";
import { useFetch } from "@/hooks/use-fetch";
import { fetchApi } from "@/lib/api";
import { Button } from "@/components/ui/button";
import { EmptyState } from "@/components/ui/empty-state";
import { SectionSkeleton } from "@/components/ui/section-skeleton";
import { ErrorBanner } from "@/components/ui/error-banner";
import { StatusMessage } from "@/components/ui/status-message";
import {
  Dialog,
  DialogContent,
  DialogHeader,
  DialogFooter,
  DialogTitle,
  DialogDescription,
} from "@/components/ui/dialog";
import { ConfirmDialog } from "@/components/ui/confirm-dialog";
import { WatchlistCard } from "@/components/domain/watchlist-card";
import type { Watchlist } from "@/types/watchlist";

const crumbs = [{ label: "Watchlists" }];

export default function WatchlistPage() {
  return (
    <Suspense>
      <WatchlistPageInner />
    </Suspense>
  );
}

function WatchlistPageInner() {
  useBreadcrumbs(crumbs);
  const searchParams = useSearchParams();

  const { data: watchlists, loading, error, refetch } = useFetch<Watchlist[]>("watchlists");

  // Create / Edit dialog
  const [formOpen, setFormOpen] = useState(false);
  const [editTarget, setEditTarget] = useState<Watchlist | null>(null);
  const [formName, setFormName] = useState("");
  const [formDesc, setFormDesc] = useState("");
  const [formSaving, setFormSaving] = useState(false);
  const [status, setStatus] = useState<{ type: "success" | "error"; message: string } | null>(null);

  // Delete dialog
  const [deleteTarget, setDeleteTarget] = useState<Watchlist | null>(null);

  // Auto-open create dialog via ?new=1
  useEffect(() => {
    if (searchParams.get("new") === "1") {
      openCreate();
    }
  }, [searchParams]);

  function openCreate() {
    setEditTarget(null);
    setFormName("");
    setFormDesc("");
    setFormOpen(true);
    setStatus(null);
  }

  function openEdit(wl: Watchlist) {
    setEditTarget(wl);
    setFormName(wl.name);
    setFormDesc(wl.description ?? "");
    setFormOpen(true);
    setStatus(null);
  }

  function closeForm() {
    setFormOpen(false);
    setEditTarget(null);
    setFormName("");
    setFormDesc("");
  }

  async function handleFormSubmit() {
    setFormSaving(true);
    setStatus(null);
    try {
      if (editTarget) {
        await fetchApi(`watchlists/${editTarget.id}`, {
          method: "PUT",
          body: JSON.stringify({ name: formName, description: formDesc || null }),
        });
        setStatus({ type: "success", message: "Watchlist updated." });
      } else {
        await fetchApi("watchlists", {
          method: "POST",
          body: JSON.stringify({ name: formName, description: formDesc || null }),
        });
        setStatus({ type: "success", message: "Watchlist created." });
      }
      closeForm();
      refetch();
    } catch (err) {
      setStatus({
        type: "error",
        message: err instanceof Error ? err.message : "Failed to save watchlist",
      });
    } finally {
      setFormSaving(false);
    }
  }

  async function handleDelete() {
    if (!deleteTarget) return;
    try {
      await fetchApi(`watchlists/${deleteTarget.id}`, { method: "DELETE" });
      setDeleteTarget(null);
      setStatus({ type: "success", message: "Watchlist deleted." });
      refetch();
    } catch (err) {
      setDeleteTarget(null);
      setStatus({
        type: "error",
        message: err instanceof Error ? err.message : "Failed to delete watchlist",
      });
    }
  }

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between fade-up-stagger-1">
        <h1 className="text-2xl font-bold">Watchlists</h1>
        <Button size="sm" onClick={openCreate}>
          <Plus className="h-4 w-4" />
          Create
        </Button>
      </div>

      {error && <ErrorBanner message={error} />}
      {status && <StatusMessage type={status.type} message={status.message} />}

      {loading ? (
        <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-3">
          {[1, 2, 3].map((i) => (
            <div key={i} className="rounded-widget bg-secondary/50 p-4">
              <SectionSkeleton />
            </div>
          ))}
        </div>
      ) : watchlists && watchlists.length > 0 ? (
        <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-3 fade-up-stagger-2">
          {watchlists.map((wl) => (
            <WatchlistCard
              key={wl.id}
              watchlist={wl}
              onEdit={openEdit}
              onDelete={setDeleteTarget}
            />
          ))}
        </div>
      ) : (
        <EmptyState
          title="No watchlists yet"
          message="Create a watchlist to start tracking Twitter/X accounts."
        />
      )}

      {/* Create / Edit dialog */}
      <Dialog open={formOpen} onOpenChange={(open) => { if (!open) closeForm(); }}>
        <DialogContent>
          <DialogHeader>
            <DialogTitle>{editTarget ? "Edit Watchlist" : "Create Watchlist"}</DialogTitle>
            <DialogDescription>
              {editTarget
                ? "Update the name and description of your watchlist."
                : "Give your watchlist a name to get started."}
            </DialogDescription>
          </DialogHeader>

          <div className="mt-4 space-y-4">
            <div className="space-y-1.5">
              <label htmlFor="wl-name" className="text-xs font-medium text-muted-foreground">
                Name *
              </label>
              <input
                id="wl-name"
                type="text"
                value={formName}
                onChange={(e) => setFormName(e.target.value)}
                placeholder="e.g. Tech Influencers"
                className="w-full rounded-lg border border-border bg-background px-3 py-2 text-sm outline-none focus:border-ring focus:ring-2 focus:ring-ring/50"
                autoFocus
              />
            </div>
            <div className="space-y-1.5">
              <label htmlFor="wl-desc" className="text-xs font-medium text-muted-foreground">
                Description
              </label>
              <textarea
                id="wl-desc"
                value={formDesc}
                onChange={(e) => setFormDesc(e.target.value)}
                placeholder="Optional description"
                rows={2}
                className="w-full rounded-lg border border-border bg-background px-3 py-2 text-sm outline-none focus:border-ring focus:ring-2 focus:ring-ring/50 resize-none"
              />
            </div>
          </div>

          <DialogFooter>
            <Button variant="ghost" size="sm" onClick={closeForm} disabled={formSaving}>
              Cancel
            </Button>
            <Button size="sm" onClick={handleFormSubmit} disabled={formSaving || !formName.trim()}>
              {formSaving ? "Saving..." : editTarget ? "Update" : "Create"}
            </Button>
          </DialogFooter>
        </DialogContent>
      </Dialog>

      {/* Delete confirmation */}
      <ConfirmDialog
        open={!!deleteTarget}
        onOpenChange={(open) => { if (!open) setDeleteTarget(null); }}
        title="Delete Watchlist"
        description={`Are you sure you want to delete "${deleteTarget?.name}"? This will also remove all members and posts.`}
        confirmLabel="Delete"
        variant="destructive"
        onConfirm={handleDelete}
      />
    </div>
  );
}
