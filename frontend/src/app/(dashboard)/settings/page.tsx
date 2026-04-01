"use client";

import { useState } from "react";
import { KeyRound, Eye, EyeOff, Pencil, Trash2 } from "lucide-react";
import { useBreadcrumbs } from "@/hooks/use-breadcrumbs";
import { useFetch } from "@/hooks/use-fetch";
import { fetchApi } from "@/lib/api";
import { SectionSkeleton } from "@/components/ui/section-skeleton";
import { ErrorBanner } from "@/components/ui/error-banner";
import { StatusMessage } from "@/components/ui/status-message";
import { Button } from "@/components/ui/button";

const crumbs = [{ label: "Settings" }];

interface CredentialOut {
  id: number;
  provider: string;
  has_api_key: boolean;
  has_cookie: boolean;
  created_at: string;
  updated_at: string;
}

export default function SettingsPage() {
  useBreadcrumbs(crumbs);

  const {
    data: credentials,
    loading,
    error,
    refetch,
  } = useFetch<CredentialOut[]>("settings/credentials");

  const [editing, setEditing] = useState(false);
  const [apiKey, setApiKey] = useState("");
  const [cookie, setCookie] = useState("");
  const [showApiKey, setShowApiKey] = useState(false);
  const [showCookie, setShowCookie] = useState(false);
  const [saving, setSaving] = useState(false);
  const [deleting, setDeleting] = useState(false);
  const [confirmDelete, setConfirmDelete] = useState(false);
  const [status, setStatus] = useState<{
    type: "success" | "error";
    message: string;
  } | null>(null);

  const tweapiCred = credentials?.find((c) => c.provider === "tweapi");

  async function handleSave() {
    setSaving(true);
    setStatus(null);
    try {
      await fetchApi("settings/credentials", {
        method: "PUT",
        body: JSON.stringify({
          provider: "tweapi",
          ...(apiKey ? { api_key: apiKey } : {}),
          ...(cookie ? { cookie } : {}),
        }),
      });
      setStatus({ type: "success", message: "Credentials saved successfully." });
      setEditing(false);
      setApiKey("");
      setCookie("");
      setShowApiKey(false);
      setShowCookie(false);
      refetch();
    } catch (err) {
      setStatus({
        type: "error",
        message: err instanceof Error ? err.message : "Failed to save credentials",
      });
    } finally {
      setSaving(false);
    }
  }

  async function handleDelete() {
    setDeleting(true);
    setStatus(null);
    try {
      await fetchApi("settings/credentials/tweapi", { method: "DELETE" });
      setStatus({ type: "success", message: "Credentials deleted." });
      setConfirmDelete(false);
      setEditing(false);
      refetch();
    } catch (err) {
      setStatus({
        type: "error",
        message: err instanceof Error ? err.message : "Failed to delete credentials",
      });
    } finally {
      setDeleting(false);
    }
  }

  function startEdit() {
    setEditing(true);
    setStatus(null);
    setApiKey("");
    setCookie("");
    setShowApiKey(false);
    setShowCookie(false);
  }

  function cancelEdit() {
    setEditing(false);
    setApiKey("");
    setCookie("");
    setShowApiKey(false);
    setShowCookie(false);
    setConfirmDelete(false);
  }

  return (
    <div className="space-y-6">
      <h1 className="text-2xl font-bold fade-up-stagger-1">Settings</h1>

      {error && <ErrorBanner message={error} />}

      {/* Credentials section */}
      <div className="rounded-widget bg-secondary/50 p-5 fade-up-stagger-2">
        <div className="flex items-center justify-between">
          <div className="flex items-center gap-2">
            <KeyRound className="h-4 w-4 text-muted-foreground" />
            <h2 className="text-sm font-medium">TweAPI Credentials</h2>
          </div>
          {!editing && tweapiCred && (
            <Button variant="ghost" size="icon-sm" onClick={startEdit}>
              <Pencil className="h-3.5 w-3.5" />
            </Button>
          )}
        </div>

        {loading ? (
          <div className="mt-3">
            <SectionSkeleton />
          </div>
        ) : editing ? (
          /* Edit mode */
          <div className="mt-4 space-y-4">
            {/* API Key field */}
            <div className="space-y-1.5">
              <label htmlFor="api-key" className="text-xs font-medium text-muted-foreground">
                API Key
              </label>
              <div className="relative">
                <input
                  id="api-key"
                  type={showApiKey ? "text" : "password"}
                  value={apiKey}
                  onChange={(e) => setApiKey(e.target.value)}
                  placeholder={tweapiCred?.has_api_key ? "Leave blank to keep current" : "Enter API key"}
                  className="w-full rounded-lg border border-border bg-background px-3 py-2 pr-9 text-sm outline-none focus:border-ring focus:ring-2 focus:ring-ring/50"
                />
                <button
                  type="button"
                  onClick={() => setShowApiKey(!showApiKey)}
                  className="absolute right-2.5 top-1/2 -translate-y-1/2 text-muted-foreground hover:text-foreground"
                >
                  {showApiKey ? <EyeOff className="h-3.5 w-3.5" /> : <Eye className="h-3.5 w-3.5" />}
                </button>
              </div>
            </div>

            {/* Cookie field */}
            <div className="space-y-1.5">
              <label htmlFor="cookie" className="text-xs font-medium text-muted-foreground">
                Cookie
              </label>
              <div className="relative">
                {showCookie ? (
                  <textarea
                    id="cookie"
                    value={cookie}
                    onChange={(e) => setCookie(e.target.value)}
                    placeholder={tweapiCred?.has_cookie ? "Leave blank to keep current" : "Enter cookie string"}
                    rows={3}
                    className="w-full rounded-lg border border-border bg-background px-3 py-2 pr-9 text-sm outline-none focus:border-ring focus:ring-2 focus:ring-ring/50 resize-none"
                  />
                ) : (
                  <div
                    className="w-full rounded-lg border border-border bg-background px-3 py-2 pr-9 text-sm min-h-[5rem] cursor-text"
                    onClick={() => setShowCookie(true)}
                  >
                    {cookie
                      ? "•".repeat(Math.min(cookie.length, 60))
                      : <span className="text-muted-foreground">{tweapiCred?.has_cookie ? "Leave blank to keep current" : "Enter cookie string"}</span>}
                  </div>
                )}
                <button
                  type="button"
                  onClick={() => setShowCookie(!showCookie)}
                  className="absolute right-2.5 top-3 text-muted-foreground hover:text-foreground"
                >
                  {showCookie ? <EyeOff className="h-3.5 w-3.5" /> : <Eye className="h-3.5 w-3.5" />}
                </button>
              </div>
            </div>

            {/* Action buttons */}
            <div className="flex items-center gap-2 pt-1">
              <Button
                variant="default"
                size="sm"
                onClick={handleSave}
                disabled={saving || (!apiKey && !cookie)}
              >
                {saving ? "Saving..." : "Save"}
              </Button>
              <Button variant="ghost" size="sm" onClick={cancelEdit} disabled={saving}>
                Cancel
              </Button>
              {tweapiCred && (
                <div className="ml-auto">
                  {confirmDelete ? (
                    <div className="flex items-center gap-2">
                      <span className="text-xs text-destructive">Delete credentials?</span>
                      <Button
                        variant="destructive"
                        size="sm"
                        onClick={handleDelete}
                        disabled={deleting}
                      >
                        {deleting ? "Deleting..." : "Confirm"}
                      </Button>
                      <Button
                        variant="ghost"
                        size="sm"
                        onClick={() => setConfirmDelete(false)}
                        disabled={deleting}
                      >
                        No
                      </Button>
                    </div>
                  ) : (
                    <Button
                      variant="destructive"
                      size="sm"
                      onClick={() => setConfirmDelete(true)}
                    >
                      <Trash2 className="h-3.5 w-3.5" />
                      Delete
                    </Button>
                  )}
                </div>
              )}
            </div>
          </div>
        ) : tweapiCred ? (
          /* Display mode — credentials exist */
          <div className="mt-3 space-y-3">
            <div className="space-y-1">
              <span className="text-xs text-muted-foreground">API Key</span>
              <p className="text-sm font-mono">
                {tweapiCred.has_api_key ? "••••••••••••" : <span className="text-muted-foreground italic">Not set</span>}
              </p>
            </div>
            <div className="space-y-1">
              <span className="text-xs text-muted-foreground">Cookie</span>
              <p className="text-sm font-mono">
                {tweapiCred.has_cookie ? "••••••••••••" : <span className="text-muted-foreground italic">Not set</span>}
              </p>
            </div>
            <p className="text-xs text-muted-foreground">
              Last updated {new Date(tweapiCred.updated_at).toLocaleDateString()}
            </p>
          </div>
        ) : (
          /* No credentials yet */
          <div className="mt-3 space-y-3">
            <p className="text-sm text-muted-foreground">
              No TweAPI credentials configured. Add your API key or cookie to get started.
            </p>
            <Button variant="outline" size="sm" onClick={startEdit}>
              Add Credentials
            </Button>
          </div>
        )}
      </div>

      {status && (
        <StatusMessage type={status.type} message={status.message} />
      )}

      {/* Provider info */}
      <div className="rounded-widget bg-secondary/50 p-5 fade-up-stagger-3">
        <h2 className="text-sm font-medium text-muted-foreground">Provider</h2>
        <p className="mt-2 text-sm font-medium">TweAPI</p>
        <p className="mt-1 text-xs text-muted-foreground">
          Twitter/X data access via TweAPI. This is the only supported provider in v1.
        </p>
      </div>
    </div>
  );
}
