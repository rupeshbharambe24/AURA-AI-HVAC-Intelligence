import { useState } from "react";
import { motion } from "framer-motion";
import { FlaskConical, GitCompare } from "lucide-react";
import { PageHeader } from "@/components/common/PageHeader";
import { StatusBadge } from "@/components/common/StatusBadge";
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from "@/components/ui/select";
import { Button } from "@/components/ui/button";
import { useExperiments } from "@/hooks/useModels";

export default function Experiments() {
  const [filter, setFilter] = useState("all");
  const { data } = useExperiments(filter);
  const experiments = data?.experiments || [];
  const filtered = filter === "all" ? experiments : experiments.filter(e => e.model === filter);

  return (
    <div className="page-container">
      <PageHeader icon={FlaskConical} title="Experiments" description="Compare runs, track metrics, and browse artifacts">
        <Button variant="outline" size="sm" className="gap-2">
          <GitCompare className="w-4 h-4" /> Compare Selected
        </Button>
      </PageHeader>

      {data?.warnings?.length ? (
        <div className="text-xs text-amber-500 mb-3">{data.warnings.join(" | ")}</div>
      ) : null}

      <div className="flex items-center gap-4">
        <Select value={filter} onValueChange={setFilter}>
          <SelectTrigger className="w-40 bg-card border-border">
            <SelectValue />
          </SelectTrigger>
          <SelectContent>
            <SelectItem value="all">All Models</SelectItem>
            <SelectItem value="forecast">Forecast</SelectItem>
            <SelectItem value="anomaly">Anomaly</SelectItem>
            <SelectItem value="market_share">Market Share</SelectItem>
          </SelectContent>
        </Select>
      </div>

      <motion.div initial={{ opacity: 0 }} animate={{ opacity: 1 }} className="glass-card overflow-hidden">
        <table className="w-full text-sm">
          <thead>
            <tr className="border-b border-border text-left text-xs text-muted-foreground uppercase tracking-wider">
              <th className="px-5 py-3">Run</th>
              <th className="px-5 py-3">Model</th>
              <th className="px-5 py-3">Experiment Name</th>
              <th className="px-5 py-3">Owner</th>
              <th className="px-5 py-3">Date</th>
              <th className="px-5 py-3">MAPE</th>
              <th className="px-5 py-3">Status</th>
            </tr>
          </thead>
          <tbody>
            {filtered.map((exp, i) => (
              <motion.tr
                key={exp.id}
                initial={{ opacity: 0 }}
                animate={{ opacity: 1 }}
                transition={{ delay: i * 0.03 }}
                className="border-b border-border/50 hover:bg-muted/30 transition-colors cursor-pointer"
              >
                <td className="px-5 py-3.5 font-mono text-xs">{exp.id}</td>
                <td className="px-5 py-3.5 text-muted-foreground capitalize">{exp.model}</td>
                <td className="px-5 py-3.5 font-medium">{exp.name}</td>
                <td className="px-5 py-3.5 text-muted-foreground">{exp.owner}</td>
                <td className="px-5 py-3.5 text-muted-foreground">{exp.date}</td>
                <td className="px-5 py-3.5">{exp.mape != null ? `${exp.mape}%` : "—"}</td>
                <td className="px-5 py-3.5"><StatusBadge status={exp.status} /></td>
              </motion.tr>
            ))}
            {filtered.length === 0 && (
              <tr>
                <td className="px-5 py-6 text-center text-muted-foreground" colSpan={7}>
                  No experiments found.
                </td>
              </tr>
            )}
          </tbody>
        </table>
      </motion.div>
    </div>
  );
}
