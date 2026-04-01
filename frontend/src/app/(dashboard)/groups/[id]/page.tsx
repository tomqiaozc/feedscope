"use client";

import { useState, useMemo, useRef, use } from "react";
import { Plus, Upload, User, Trash2 } from "lucide-react";
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
import type { Group, GroupMember } from "@/types/group";

export default function GroupDetailPage({
  params,
}: {
  params: Promise<{ id: string }>;
}) {
  const { id } = use(params);

  const { data: group } = useFetch<Group>(`groups/${id}`);
  const {
    data: members,
    loading,
    error,
    refetch,
  } = useFetch<GroupMember[]>(`groups/${id}/members`);

  const crumbs = useMemo(
    () => [
      { label: "Groups", href: "/groups" },
      { label: group?.name ?? "..." },
    ],
    [group?.name],
  );
  useBreadcrumbs(crumbs);

  // Add member dialog
  const [addOpen, setAddOpen] = useState(false);
  const [username, setUsername] = useState("");
  const [saving, setSaving] = useState(false);
  const [status, setStatus] = useState<{ type: "success" | "error"; message: string } | null>(null);

  // Delete member
  const [deleteTarget, setDeleteTarget] = useState<GroupMember | null>(null);

  // Bulk import
  const fileRef = useRef<HTMLInputElement>(null);
  const [importing, setImporting] = useState(false);

  async function handleAddMember() {
    setSaving(true);
    setStatus(null);
    try {
      await fetchApi(`groups/${id}/members`, {
        method: "POST",
        body: JSON.stringify({ username }),
      });
      setUsername("");
      setAddOpen(false);
      setStatus({ type: "success", message: "Member added." });
      refetch();
    } catch (err) {
      setStatus({
        type: "error",
        message: err instanceof Error ? err.message : "Failed to add member",
      });
    } finally {
      setSaving(false);
    }
  }

  async function handleDeleteMember() {
    if (!deleteTarget) return;
    try {
      await fetchApi(`groups/${id}/members/${deleteTarget.id}`, { method: "DELETE" });
      setDeleteTarget(null);
      setStatus({ type: "success", message: "Member removed." });
      refetch();
    } catch (err) {
      setDeleteTarget(null);
      setStatus({
        type: "error",
        message: err instanceof Error ? err.message : "Failed to remove member",
      });
    }
  }

  async function handleFileImport(e: React.ChangeEvent<HTMLInputElement>) {
    const file = e.target.files?.[0];
    if (!file) return;

    if (file.size > 1_000_000) {
      setStatus({ type: "error", message: "File too large. Maximum size is 1 MB." });
      if (fileRef.current) fileRef.current.value = "";
      return;
    }

    setImporting(true);
    setStatus(null);

    try {
      const text = await file.text();
      const usernames = text
        .split(/[,\n\r]+/)
        .map((s) => s.trim().replace(/^@/, ""))
        .filter(Boolean);

      if (usernames.length === 0) {
        setStatus({ type: "error", message: "No usernames found in file." });
        return;
      }

      const result = await fetchApi<{ added: number; failed: number }>(
        `groups/${id}/members/batch`,
        {
          method: "POST",
          body: JSON.stringify({ usernames }),
        },
      );
      setStatus({
        type: "success",
        message: `Import complete: ${result.added} added, ${result.failed} failed.`,
      });
      refetch();
    } catch (err) {
      setStatus({
        type: "error",
        message: err instanceof Error ? err.message : "Import failed",
      });
    } finally {
      setImporting(false);
      if (fileRef.current) fileRef.current.value = "";
    }
  }

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between fade-up-stagger-1">
        <h1 className="text-2xl font-bold">{group?.name ?? "..."}</h1>
        <div className="flex gap-2">
          <Button variant="outline" size="sm" onClick={() => fileRef.current?.click()} disabled={importing}>
            <Upload className="h-4 w-4" />
            {importing ? "Importing..." : "Import"}
          </Button>
          <input
            ref={fileRef}
            type="file"
            accept=".txt,.csv"
            className="hidden"
            onChange={handleFileImport}
          />
          <Button size="sm" onClick={() => { setAddOpen(true); setStatus(null); }}>
            <Plus className="h-4 w-4" />
            Add Member
          </Button>
        </div>
      </div>

      {error && <ErrorBanner message={error} />}
      {status && <StatusMessage type={status.type} message={status.message} />}

      {loading ? (
        <SectionSkeleton />
      ) : members && members.length > 0 ? (
        <div className="space-y-1 fade-up-stagger-2">
          {members.map((m) => (
            <div
              key={m.id}
              className="flex items-center gap-3 rounded-widget px-3 py-2.5 transition-colors hover:bg-secondary/50"
            >
              {m.profile_image_url ? (
                <img
                  src={m.profile_image_url}
                  alt={m.username}
                  className="h-8 w-8 shrink-0 rounded-full object-cover"
                />
              ) : (
                <div className="flex h-8 w-8 shrink-0 items-center justify-center rounded-full bg-muted">
                  <User className="h-4 w-4 text-muted-foreground" />
                </div>
              )}
              <div className="min-w-0 flex-1">
                <div className="flex items-baseline gap-1.5">
                  <span className="text-sm font-medium truncate">@{m.username}</span>
                  {m.display_name && (
                    <span className="text-xs text-muted-foreground truncate">{m.display_name}</span>
                  )}
                </div>
                {m.notes && <p className="text-xs text-muted-foreground truncate">{m.notes}</p>}
              </div>
              <Button variant="ghost" size="icon-xs" onClick={() => setDeleteTarget(m)}>
                <Trash2 className="h-3 w-3" />
              </Button>
            </div>
          ))}
        </div>
      ) : (
        <EmptyState
          title="No members yet"
          message="Add members individually or import from a file."
        />
      )}

      {/* Add member dialog */}
      <Dialog open={addOpen} onOpenChange={(open) => { if (!open) setAddOpen(false); }}>
        <DialogContent>
          <DialogHeader>
            <DialogTitle>Add Member</DialogTitle>
            <DialogDescription>Add a Twitter/X account to this group.</DialogDescription>
          </DialogHeader>
          <div className="mt-4 space-y-1.5">
            <label htmlFor="gm-username" className="text-xs font-medium text-muted-foreground">
              Username *
            </label>
            <input
              id="gm-username"
              type="text"
              value={username}
              onChange={(e) => setUsername(e.target.value)}
              placeholder="e.g. elonmusk"
              className="w-full rounded-lg border border-border bg-background px-3 py-2 text-sm outline-none focus:border-ring focus:ring-2 focus:ring-ring/50"
              autoFocus
            />
          </div>
          <DialogFooter>
            <Button variant="ghost" size="sm" onClick={() => setAddOpen(false)} disabled={saving}>
              Cancel
            </Button>
            <Button size="sm" onClick={handleAddMember} disabled={saving || !username.trim()}>
              {saving ? "Adding..." : "Add"}
            </Button>
          </DialogFooter>
        </DialogContent>
      </Dialog>

      {/* Delete confirm */}
      <ConfirmDialog
        open={!!deleteTarget}
        onOpenChange={(open) => { if (!open) setDeleteTarget(null); }}
        title="Remove Member"
        description={`Remove @${deleteTarget?.username} from this group?`}
        confirmLabel="Remove"
        variant="destructive"
        onConfirm={handleDeleteMember}
      />
    </div>
  );
}
