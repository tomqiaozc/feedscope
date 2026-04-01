import {
  LayoutDashboard,
  List,
  Users,
  Compass,
  Settings,
  Sparkles,
  Webhook,
  BarChart3,
  type LucideIcon,
} from "lucide-react";

export interface NavItem {
  label: string;
  href: string;
  icon: LucideIcon;
}

export const TOP_GROUPS: NavItem[] = [
  { label: "Dashboard", href: "/", icon: LayoutDashboard },
  { label: "Watchlists", href: "/watchlist", icon: List },
  { label: "Groups", href: "/groups", icon: Users },
  { label: "Explore", href: "/explore", icon: Compass },
];

export const BOTTOM_GROUPS: NavItem[] = [
  { label: "Settings", href: "/settings", icon: Settings },
  { label: "AI Settings", href: "/ai-settings", icon: Sparkles },
  { label: "Webhooks", href: "/webhooks", icon: Webhook },
  { label: "Usage", href: "/usage", icon: BarChart3 },
];
