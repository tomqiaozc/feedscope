"use client";

import { useState, useEffect } from "react";
import { useBreadcrumbs } from "@/hooks/use-breadcrumbs";
import { useFetch } from "@/hooks/use-fetch";
import { fetchApi } from "@/lib/api";
import { Button } from "@/components/ui/button";
import { LoadingSpinner } from "@/components/ui/loading-spinner";
import { StatusMessage } from "@/components/ui/status-message";

const crumbs = [
  { label: "Settings", href: "/settings" },
  { label: "AI" },
];

interface AiSettings {
  provider_id?: string;
  has_api_key?: boolean;
  model?: string;
  base_url?: string;
  sdk_type?: string;
}

const PRESETS: Record<string, { sdk_type: string; model: string; base_url?: string }> = {
  anthropic: { sdk_type: "anthropic", model: "claude-sonnet-4-20250514" },
  openai: { sdk_type: "openai", model: "gpt-4o-mini" },
  custom: { sdk_type: "openai", model: "" },
};

export default function AiSettingsPage() {
  useBreadcrumbs(crumbs);

  const { data: existing, loading: fetching } = useFetch<AiSettings>("settings/ai");

  const [provider, setProvider] = useState("anthropic");
  const [apiKey, setApiKey] = useState("");
  const [model, setModel] = useState(PRESETS.anthropic.model);
  const [baseUrl, setBaseUrl] = useState("");
  const [sdkType, setSdkType] = useState(PRESETS.anthropic.sdk_type);
  const [showKey, setShowKey] = useState(false);

  const [testing, setTesting] = useState(false);
  const [saving, setSaving] = useState(false);
  const [status, setStatus] = useState<{ type: "success" | "error"; message: string } | null>(null);

  useEffect(() => {
    if (!existing) return;
    if (existing.provider_id) setProvider(existing.provider_id);
    // api_key is not returned by GET (only has_api_key boolean) — keep form field empty
    if (existing.model) setModel(existing.model);
    if (existing.base_url) setBaseUrl(existing.base_url);
    if (existing.sdk_type) setSdkType(existing.sdk_type);
  }, [existing]);

  function handleProviderChange(p: string) {
    setProvider(p);
    const preset = PRESETS[p];
    if (preset) {
      setSdkType(preset.sdk_type);
      setModel(preset.model);
      if (p !== "custom") setBaseUrl("");
    }
    setStatus(null);
  }

  async function handleTest() {
    setTesting(true);
    setStatus(null);
    try {
      const result = await fetchApi<{ provider: string; model: string; response_preview: string }>(
        "settings/ai/test",
        {
          method: "POST",
          body: JSON.stringify({ provider_id: provider, api_key: apiKey, model, base_url: baseUrl || undefined, sdk_type: sdkType }),
        }
      );
      setStatus({ type: "success", message: `${result.provider} / ${result.model}: ${result.response_preview}` });
    } catch (err) {
      setStatus({ type: "error", message: err instanceof Error ? err.message : "Test failed" });
    } finally {
      setTesting(false);
    }
  }

  async function handleSave() {
    setSaving(true);
    setStatus(null);
    try {
      await fetchApi("settings/ai", {
        method: "PUT",
        body: JSON.stringify({ provider_id: provider, ...(apiKey ? { api_key: apiKey } : {}), model, base_url: baseUrl || undefined, sdk_type: sdkType }),
      });
      setStatus({ type: "success", message: "AI settings saved" });
    } catch (err) {
      setStatus({ type: "error", message: err instanceof Error ? err.message : "Save failed" });
    } finally {
      setSaving(false);
    }
  }

  if (fetching) {
    return (
      <main className="p-6">
        <div className="flex items-center gap-2">
          <LoadingSpinner /> Loading AI settings...
        </div>
      </main>
    );
  }

  return (
    <main className="p-6 max-w-2xl space-y-6">
      <h1 className="text-2xl font-bold">AI Settings</h1>

      <div className="space-y-4">
        {/* Provider selector */}
        <div className="space-y-1.5">
          <label className="text-sm font-medium">Provider</label>
          <select
            value={provider}
            onChange={(e) => handleProviderChange(e.target.value)}
            className="w-full rounded-md border border-input bg-background px-3 py-2 text-sm"
          >
            <option value="anthropic">Anthropic</option>
            <option value="openai">OpenAI</option>
            <option value="custom">Custom</option>
          </select>
        </div>

        {/* API Key */}
        <div className="space-y-1.5">
          <label className="text-sm font-medium">API Key</label>
          <div className="flex gap-2">
            <input
              type={showKey ? "text" : "password"}
              value={apiKey}
              onChange={(e) => setApiKey(e.target.value)}
              placeholder={existing?.has_api_key ? "Leave blank to keep current" : "sk-..."}
              className="flex-1 rounded-md border border-input bg-background px-3 py-2 text-sm"
            />
            <Button variant="outline" size="sm" onClick={() => setShowKey(!showKey)}>
              {showKey ? "Hide" : "Show"}
            </Button>
          </div>
        </div>

        {/* Model */}
        <div className="space-y-1.5">
          <label className="text-sm font-medium">Model</label>
          <input
            type="text"
            value={model}
            onChange={(e) => setModel(e.target.value)}
            placeholder="Model name"
            className="w-full rounded-md border border-input bg-background px-3 py-2 text-sm"
          />
        </div>

        {/* Base URL (custom only) */}
        {provider === "custom" && (
          <div className="space-y-1.5">
            <label className="text-sm font-medium">Base URL</label>
            <input
              type="text"
              value={baseUrl}
              onChange={(e) => setBaseUrl(e.target.value)}
              placeholder="https://api.example.com/v1"
              className="w-full rounded-md border border-input bg-background px-3 py-2 text-sm"
            />
          </div>
        )}

        {/* SDK Type (read-only) */}
        <div className="space-y-1.5">
          <label className="text-sm font-medium">SDK Type</label>
          <input
            type="text"
            value={sdkType}
            readOnly
            className="w-full rounded-md border border-input bg-muted px-3 py-2 text-sm text-muted-foreground"
          />
        </div>
      </div>

      {/* Status */}
      {status && <StatusMessage type={status.type} message={status.message} />}

      {/* Actions */}
      <div className="flex gap-3">
        <Button variant="outline" onClick={handleTest} disabled={testing || (!apiKey && !existing?.has_api_key)}>
          {testing && <LoadingSpinner className="mr-2" />}
          Test Connection
        </Button>
        <Button onClick={handleSave} disabled={saving || (!apiKey && !existing?.has_api_key)}>
          {saving && <LoadingSpinner className="mr-2" />}
          Save
        </Button>
      </div>
    </main>
  );
}
