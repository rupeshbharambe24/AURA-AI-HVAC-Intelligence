import { Badge } from "@/components/ui/badge";
import { cn } from "@/lib/utils";

const statusStyles: Record<string, string> = {
  active: "bg-accent/15 text-accent border-accent/30",
  experimental: "bg-warning/15 text-warning border-warning/30",
  completed: "bg-accent/15 text-accent border-accent/30",
  running: "bg-primary/15 text-primary border-primary/30",
  failed: "bg-destructive/15 text-destructive border-destructive/30",
  prod: "bg-accent/15 text-accent border-accent/30",
  staging: "bg-warning/15 text-warning border-warning/30",
  dev: "bg-primary/15 text-primary border-primary/30",
};

export function StatusBadge({ status }: { status: string }) {
  return (
    <Badge variant="outline" className={cn("text-xs font-medium capitalize", statusStyles[status] || "")}>
      {status}
    </Badge>
  );
}
