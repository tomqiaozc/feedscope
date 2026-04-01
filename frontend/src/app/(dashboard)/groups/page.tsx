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
import { GroupCard } from "@/components/domain/group-card";
import type { Group } from "@/types/group";

const crumbs = [{ label: "Groups" }];

export default function GroupsPage() {
  return (
    <Suspense>
      <GroupsPageInner />
    </Suspense>
  );
}

function GroupsPageInner() {
  useBreadcrumbs(crumbs);
  const searchParams = useSearchParams();

  const { data: groups, loading, error, refetch } = useFetch<Group[]>("groups");

  const [formOpen, setFormOpen] = useState(false);
  const [editTarget, setEditTarget] = useState<Group | null>(null);
  const [formName, setFormName] = useState("");
  const [formDesc, setFormDesc] = useState("");
  const [formSaving, setFormSaving] = useState(false);
  const [status, setStatus] = useState<{ type: "success" | "error"; message: string } | null>(null);
  const [deleteTarget, setDeleteTarget] = useState<Group | null>(null);

  useEffect(() => {
    if (searchParams.get("new") === "1") openCreate();
  }, [searchParams]);

  function openCreate() {
    setEditTarget(null);
    setFormName("");
    setFormDesc("");
    setFormOpen(true);
    setStatus(null);
  }

  function openEdit(g: Group) {
    setEditTarget(g);
    setFormName(g.name);
    setFormDesc(g.description ?? "");
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
        await fetchApi(`groups/${editTarget.id}`, {
          method: "PUT",
          body: JSON.stringify({ name: formName, description: formDesc || null }),
        });
        setStatus({ type: "success", message: "Group updated." });
      } else {
        await fetchApi("groups", {
          method: "POST",
          body: JSON.stringify({ name: formName, description: formDesc || null }),
        });
        setStatus({ type: "success", message: "Group created." });
      }
      closeForm();
      refetch();
    } catch (err) {
      setStatus({
        type: "error",
        message: err instanceof Error ? err.message : "Failed to save group",
      });
    } finally {
      setFormSaving(false);
    }
  }

  async function handleDelete() {
    if (!deleteTarget) return;
    try {
      await fetchApi(`groups/${deleteTarget.id}`, { method: "DELETE" });
      setDeleteTarget(null);
      setStatus({ type: "success", message: "Group deleted." });
      refetch();
    } catch (err) {
      setDeleteTarget(null);
      setStatus({
        type: "error",
        message: err instanceof Error ? err.message : "Failed to delete group",
      });
    }
  }

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between fade-up-stagger-1">
        <h1 className="text-2xl font-bold">Groups</h1>
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
      ) : groups && groups.length > 0 ? (
        <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-3 fade-up-stagger-2">
          {groups.map((g) => (
            <GroupCard
              key={g.id}
              group={g}
              onEdit={openEdit}
              onDelete={setDeleteTarget}
            />
          ))}
        </div>
      ) : (
        <EmptyState
          title="No groups yet"
          message="Create a group to organize Twitter/X accounts."
        />
      )}

      <Dialog open={formOpen} onOpenChange={(open) => { if (!open) closeForm(); }}>
        <DialogContent>
          <DialogHeader>
            <DialogTitle>{editTarget ? "Edit Group" : "Create Group"}</DialogTitle>
            <DialogDescription>
              {editTarget
                ? "Update the name and description of your group."
                : "Give your group a name to get started."}
            </DialogDescription>
          </DialogHeader>
          <div className="mt-4 space-y-4">
            <div className="space-y-1.5">
              <label htmlFor="g-name" className="text-xs font-medium text-muted-foreground">
                Name *
              </label>
              <input
                id="g-name"
                type="text"
                value={formName}
                onChange={(e) => setFormName(e.target.value)}
                placeholder="e.g. Crypto Analysts"
                className="w-full rounded-lg border border-border bg-background px-3 py-2 text-sm outline-none focus:border-ring focus:ring-2 focus:ring-ring/50"
                autoFocus
              />
            </div>
            <div className="space-y-1.5">
              <label htmlFor="g-desc" className="text-xs font-medium text-muted-foreground">
                Description
              </label>
              <textarea
                id="g-desc"
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

      <ConfirmDialog
        open={!!deleteTarget}
        onOpenChange={(open) => { if (!open) setDeleteTarget(null); }}
        title="Delete Group"
        description={`Are you sure you want to delete "${deleteTarget?.name}"? This will also remove all members.`}
        confirmLabel="Delete"
        variant="destructive"
        onConfirm={handleDelete}
      />
    </div>
  );
}
