import { motion } from "framer-motion";
import { Brain } from "lucide-react";
import { Link } from "react-router-dom";
import { PageHeader } from "@/components/common/PageHeader";
import { StatusBadge } from "@/components/common/StatusBadge";
import { useModels } from "@/hooks/useModels";

export default function Models() {
  const { data, isLoading } = useModels();
  const models = data?.models || [];

  return (
    <div className="page-container">
      <PageHeader icon={Brain} title="Model Registry" description="Track, version, and manage all production & experimental models" />

      <motion.div initial={{ opacity: 0 }} animate={{ opacity: 1 }} className="glass-card overflow-hidden">
        <table className="w-full text-sm">
          <thead>
            <tr className="border-b border-border text-left text-xs text-muted-foreground uppercase tracking-wider">
              <th className="px-5 py-3">Model</th>
              <th className="px-5 py-3">Version</th>
              <th className="px-5 py-3">Alias</th>
              <th className="px-5 py-3">Training Period</th>
              <th className="px-5 py-3">Dataset Hash</th>
              <th className="px-5 py-3">Owner</th>
              <th className="px-5 py-3">Key Metric</th>
              <th className="px-5 py-3">Status</th>
            </tr>
          </thead>
          <tbody>
            {isLoading && (
              <tr>
                <td className="px-5 py-6 text-center text-muted-foreground" colSpan={8}>Loading models...</td>
              </tr>
            )}
            {models.map((m, i) => (
              <motion.tr
                key={m.id}
                initial={{ opacity: 0, x: -10 }}
                animate={{ opacity: 1, x: 0 }}
                transition={{ delay: i * 0.05 }}
                className="border-b border-border/50 hover:bg-muted/30 transition-colors cursor-pointer"
              >
                <td className="px-5 py-3.5">
                  <Link to={`/models/${m.id}`} className="font-medium hover:text-primary transition-colors flex items-center gap-2">
                    <Brain className="w-4 h-4 text-primary" />
                    {m.name}
                  </Link>
                </td>
                <td className="px-5 py-3.5 font-mono text-xs">{m.version}</td>
                <td className="px-5 py-3.5"><StatusBadge status={m.alias} /></td>
                <td className="px-5 py-3.5 text-muted-foreground text-xs">{m.training_period || "—"}</td>
                <td className="px-5 py-3.5 font-mono text-xs text-muted-foreground">{m.dataset_hash || "—"}</td>
                <td className="px-5 py-3.5 text-muted-foreground">{m.owner || "—"}</td>
                <td className="px-5 py-3.5 text-muted-foreground">{m.key_metric || "—"}</td>
                <td className="px-5 py-3.5"><StatusBadge status={m.status} /></td>
              </motion.tr>
            ))}
            {!isLoading && models.length === 0 && (
              <tr>
                <td className="px-5 py-6 text-center text-muted-foreground" colSpan={8}>No models found.</td>
              </tr>
            )}
          </tbody>
        </table>
      </motion.div>
    </div>
  );
}
