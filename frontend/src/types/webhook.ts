export interface WebhookKey {
  id: number;
  name: string;
  description: string | null;
  key_prefix: string;
  created_at: string;
  last_used_at: string | null;
}

export interface WebhookKeyCreated extends WebhookKey {
  key: string; // full key, shown once
}
