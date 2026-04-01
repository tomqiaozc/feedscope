import { BreadcrumbsProvider } from "@/components/layout/breadcrumbs-context";
import { AppShell } from "@/components/layout/app-shell";

export default function DashboardLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  return (
    <BreadcrumbsProvider>
      <AppShell>{children}</AppShell>
    </BreadcrumbsProvider>
  );
}
