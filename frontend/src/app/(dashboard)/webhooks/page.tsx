"use client";

import { useState } from "react";
import { Plus, Copy, Check, RotateCw, Trash2, Key } from "lucide-react";
import { useBreadcrumbs } from "@/hooks/use-breadcrumbs";
import { useFetch } from "@/hooks/use-fetch";
import { fetchApi } from "@/lib/api";
import { relativeTime } from "@/lib/utils";
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
import type { WebhookKey, WebhookKeyCreated } from "@/types/webhook";

const crumbs = [{ label: "Webhooks" }];

export default function WebhooksPage() {
  useBreadcrumbs(crumbs);

  const { data: keys, loading, error, refetch } = useFetch<WebhookKey[]>("webhooks");

  // Create dialog
  const [createOpen, setCreateOpen] = useState(false);
  const [formName, setFormName] = useState("");
  const [formDesc, setFormDesc] = useState("");
  const [formSaving, setFormSaving] = useState(false);

  // Key reveal modal (shown after create or rotate)
  const [revealedKey, setRevealedKey] = useState<string | null>(null);
  const [copied, setCopied] = useState(false);

  // Rotate / delete targets
  const [rotateTarget, setRotateTarget] = useState<WebhookKey | null>(null);
  const [deleteTarget, setDeleteTarget] = useState<WebhookKey | null>(null);

  const [status, setStatus] = useState<{ type: "success" | "error"; message: string } | null>(null);

  async function handleCreate() {
    setFormSaving(true);
    setStatus(null);
    try {
      const result = await fetchApi<WebhookKeyCreated>("webhooks", {
        method: "POST",
        body: JSON.stringify({ name: formName, description: formDesc || null }),
      });
      setFormName("");
      setFormDesc("");
      setCreateOpen(false);
      setRevealedKey(result.key);
      setCopied(false);
      setStatus({ type: "success", message: "Webhook key created." });
      refetch();
    } catch (err) {
      setStatus({
        type: "error",
        message: err instanceof Error ? err.message : "Failed to create key",
      });
    } finally {
      setFormSaving(false);
    }
  }

  async function handleRotate() {
    if (!rotateTarget) return;
    try {
      const result = await fetchApi<WebhookKeyCreated>(`webhooks/${rotateTarget.id}/rotate`, {
        method: "POST",
      });
      setRotateTarget(null);
      setRevealedKey(result.key);
      setCopied(false);
      setStatus({ type: "success", message: "Key rotated successfully." });
      refetch();
    } catch (err) {
      setRotateTarget(null);
      setStatus({
        type: "error",
        message: err instanceof Error ? err.message : "Failed to rotate key",
      });
    }
  }

  async function handleDelete() {
    if (!deleteTarget) return;
    try {
      await fetchApi(`webhooks/${deleteTarget.id}`, { method: "DELETE" });
      setDeleteTarget(null);
      setStatus({ type: "success", message: "Webhook key deleted." });
      refetch();
    } catch (err) {
      setDeleteTarget(null);
      setStatus({
        type: "error",
        message: err instanceof Error ? err.message : "Failed to delete key",
      });
    }
  }

  async function handleCopy() {
    if (!revealedKey) return;
    try {
      await navigator.clipboard.writeText(revealedKey);
      setCopied(true);
      setTimeout(() => setCopied(false), 2000);
    } catch {
      // fallback: select text for manual copy
    }
  }

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between fade-up-stagger-1">
        <h1 className="text-2xl font-bold">Webhooks</h1>
        <Button size="sm" onClick={() => { setCreateOpen(true); setStatus(null); }}>
          <Plus className="h-4 w-4" />
          Create Key
        </Button>
      </div>

      {error && <ErrorBanner message={error} />}
      {status && <StatusMessage type={status.type} message={status.message} />}

      {loading ? (
        <SectionSkeleton />
      ) : keys && keys.length > 0 ? (
        <div className="overflow-x-auto fade-up-stagger-2">
          <table className="w-full text-sm">
            <thead>
              <tr className="border-b border-border text-left text-xs text-muted-foreground">
                <th className="pb-2 pr-4 font-medium">Name</th>
                <th className="pb-2 pr-4 font-medium">Key</th>
                <th className="pb-2 pr-4 font-medium">Created</th>
                <th className="pb-2 pr-4 font-medium">Last Used</th>
                <th className="pb-2 font-medium text-right">Actions</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-border">
              {keys.map((k) => (
                <tr key={k.id} className="group">
                  <td className="py-3 pr-4">
                    <div className="font-medium">{k.name}</div>
                    {k.description && (
                      <div className="text-xs text-muted-foreground truncate max-w-[200px]">
                        {k.description}
                      </div>
                    )}
                  </td>
                  <td className="py-3 pr-4">
                    <code className="rounded bg-muted px-1.5 py-0.5 text-xs">
                      {k.key_prefix}...
                    </code>
                  </td>
                  <td className="py-3 pr-4 text-muted-foreground">
                    {relativeTime(k.created_at)}
                  </td>
                  <td className="py-3 pr-4 text-muted-foreground">
                    {k.last_used_at ? relativeTime(k.last_used_at) : "Never"}
                  </td>
                  <td className="py-3 text-right">
                    <div className="flex justify-end gap-1">
                      <Button
                        variant="ghost"
                        size="icon-xs"
                        onClick={() => setRotateTarget(k)}
                        title="Rotate key"
                      >
                        <RotateCw className="h-3 w-3" />
                      </Button>
                      <Button
                        variant="ghost"
                        size="icon-xs"
                        onClick={() => setDeleteTarget(k)}
                        title="Delete key"
                      >
                        <Trash2 className="h-3 w-3" />
                      </Button>
                    </div>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      ) : (
        <EmptyState
          title="No webhook keys"
          message="Create one to enable external API access."
        />
      )}

      {/* Create key dialog */}
      <Dialog open={createOpen} onOpenChange={(open) => { if (!open) setCreateOpen(false); }}>
        <DialogContent>
          <DialogHeader>
            <DialogTitle>Create Webhook Key</DialogTitle>
            <DialogDescription>
              Generate a new API key for external access.
            </DialogDescription>
          </DialogHeader>
          <div className="mt-4 space-y-4">
            <div className="space-y-1.5">
              <label htmlFor="wh-name" className="text-xs font-medium text-muted-foreground">
                Name *
              </label>
              <input
                id="wh-name"
                type="text"
                value={formName}
                onChange={(e) => setFormName(e.target.value)}
                placeholder="e.g. Production API"
                className="w-full rounded-lg border border-border bg-background px-3 py-2 text-sm outline-none focus:border-ring focus:ring-2 focus:ring-ring/50"
                autoFocus
              />
            </div>
            <div className="space-y-1.5">
              <label htmlFor="wh-desc" className="text-xs font-medium text-muted-foreground">
                Description
              </label>
              <input
                id="wh-desc"
                type="text"
                value={formDesc}
                onChange={(e) => setFormDesc(e.target.value)}
                placeholder="Optional description"
                className="w-full rounded-lg border border-border bg-background px-3 py-2 text-sm outline-none focus:border-ring focus:ring-2 focus:ring-ring/50"
              />
            </div>
          </div>
          <DialogFooter>
            <Button variant="ghost" size="sm" onClick={() => setCreateOpen(false)} disabled={formSaving}>
              Cancel
            </Button>
            <Button size="sm" onClick={handleCreate} disabled={formSaving || !formName.trim()}>
              {formSaving ? "Creating..." : "Create"}
            </Button>
          </DialogFooter>
        </DialogContent>
      </Dialog>

      {/* Key reveal modal (one-time copy) */}
      <Dialog open={!!revealedKey} onOpenChange={(open) => { if (!open) setRevealedKey(null); }}>
        <DialogContent hideClose>
          <DialogHeader>
            <DialogTitle className="flex items-center gap-2">
              <Key className="h-5 w-5 text-amber-500" />
              Your API Key
            </DialogTitle>
            <DialogDescription>
              This key will only be shown once. Copy it now.
            </DialogDescription>
          </DialogHeader>
          <div className="mt-4 space-y-3">
            <div className="flex items-center gap-2 rounded-lg border border-border bg-muted p-3">
              <code className="flex-1 break-all text-sm font-mono">{revealedKey}</code>
              <Button variant="ghost" size="icon-xs" onClick={handleCopy} title="Copy to clipboard">
                {copied ? (
                  <Check className="h-4 w-4 text-green-500" />
                ) : (
                  <Copy className="h-4 w-4" />
                )}
              </Button>
            </div>
            <p className="text-xs text-amber-600 dark:text-amber-400">
              Store this key securely. You will not be able to see it again.
            </p>
          </div>
          <DialogFooter>
            <Button size="sm" onClick={() => setRevealedKey(null)}>
              Done
            </Button>
          </DialogFooter>
        </DialogContent>
      </Dialog>

      {/* Rotate confirm */}
      <ConfirmDialog
        open={!!rotateTarget}
        onOpenChange={(open) => { if (!open) setRotateTarget(null); }}
        title="Rotate Key"
        description={`Rotate the key "${rotateTarget?.name}"? The current key will stop working immediately.`}
        confirmLabel="Rotate"
        variant="destructive"
        onConfirm={handleRotate}
      />

      {/* Delete confirm */}
      <ConfirmDialog
        open={!!deleteTarget}
        onOpenChange={(open) => { if (!open) setDeleteTarget(null); }}
        title="Delete Webhook Key"
        description={`Delete "${deleteTarget?.name}"? Any integrations using this key will stop working.`}
        confirmLabel="Delete"
        variant="destructive"
        onConfirm={handleDelete}
      />
    </div>
  );
}
