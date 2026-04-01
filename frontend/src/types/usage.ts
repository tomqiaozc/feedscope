export interface UsageSummary {
  date: string;
  endpoint: string;
  count: number;
}

export interface CreditsInfo {
  remaining: number;
  used: number;
  period_start: string;
  period_end: string;
}
