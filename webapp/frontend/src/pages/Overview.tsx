import { motion } from "framer-motion";
import { Link } from "react-router-dom";
import {
  LayoutDashboard, TrendingUp, AlertTriangle, Target, PieChart,
  Activity, Clock, Shield, Zap, Brain,
} from "lucide-react";
import { PageHeader } from "@/components/common/PageHeader";
import { StatCard } from "@/components/common/StatCard";
import { StatusBadge } from "@/components/common/StatusBadge";
import { useHealthMetrics } from "@/hooks/useHealth";
import { useModels } from "@/hooks/useModels";

const quickLinks = [
  { icon: TrendingUp, label: "Forecasting", desc: "Demand prediction", path: "/forecasting", color: "text-chart-1" },
  { icon: AlertTriangle, label: "Anomalies", desc: "Detect outliers", path: "/anomalies", color: "text-chart-4" },
  { icon: Target, label: "Optimization", desc: "Promo optimizer", path: "/optimization", color: "text-chart-2" },
  { icon: PieChart, label: "Market Share", desc: "Intelligence", path: "/market-share", color: "text-chart-3" },
];

const container = { hidden: {}, show: { transition: { staggerChildren: 0.06 } } };
const item = { hidden: { opacity: 0, y: 20 }, show: { opacity: 1, y: 0 } };

export default function Overview() {
  const { data: health } = useHealthMetrics();
  const { data: modelData } = useModels();

  const prodModels = (modelData?.models || []).filter(m => m.alias === "prod");

  return (
    <div className="page-container">
      <PageHeader icon={LayoutDashboard} title="Overview" description="System health & quick access to AI capabilities" />

      {/* Quick Access Cards */}
      <motion.div variants={container} initial="hidden" animate="show" className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">
        {quickLinks.map(q => (
          <motion.div key={q.label} variants={item}>
            <Link to={q.path} className="glass-card-hover p-5 flex items-center gap-4 block group">
              <div className="w-11 h-11 rounded-xl bg-muted flex items-center justify-center group-hover:bg-primary/10 transition-colors">
                <q.icon className={`w-5 h-5 ${q.color} transition-transform group-hover:scale-110`} />
              </div>
              <div>
                <p className="text-sm font-semibold">{q.label}</p>
                <p className="text-xs text-muted-foreground">{q.desc}</p>
              </div>
            </Link>
          </motion.div>
        ))}
      </motion.div>

      {/* Health Stats */}
      <div>
        <h2 className="section-title mb-4">System Health</h2>
        <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">
          <StatCard icon={Zap} label="API Latency" value={`${health?.api_latency_ms ?? 0}ms`} change="Live" trend="up" delay={0.1} />
          <StatCard icon={Shield} label="Error Rate" value={`${health?.error_rate_pct ?? 0}%`} change="Within SLA" trend="up" delay={0.15} />
          <StatCard icon={Activity} label="Uptime" value={`${health?.uptime_pct ?? 0}%`} change="30-day rolling" trend="neutral" delay={0.2} />
          <StatCard icon={Clock} label="Last Drift Check" value="N/A" change={health?.drift_detected ? "Drift detected" : "No drift"} trend={health?.drift_detected ? "down" : "up"} delay={0.25} />
        </div>
      </div>

      {/* Production Models */}
      <div>
        <h2 className="section-title mb-4">Production Models</h2>
        <motion.div initial={{ opacity: 0 }} animate={{ opacity: 1 }} transition={{ delay: 0.3 }} className="glass-card overflow-hidden">
          <table className="w-full text-sm">
            <thead>
              <tr className="border-b border-border text-left text-xs text-muted-foreground uppercase tracking-wider">
                <th className="px-5 py-3">Model</th>
                <th className="px-5 py-3">Version</th>
                <th className="px-5 py-3">Alias</th>
                <th className="px-5 py-3">Key Metric</th>
                <th className="px-5 py-3">Owner</th>
                <th className="px-5 py-3">Status</th>
              </tr>
            </thead>
            <tbody>
              {prodModels.map(m => (
                <tr key={m.id} className="border-b border-border/50 hover:bg-muted/30 transition-colors cursor-pointer">
                  <td className="px-5 py-3.5 font-medium flex items-center gap-2">
                    <Brain className="w-4 h-4 text-primary" />
                    {m.name}
                  </td>
                  <td className="px-5 py-3.5 font-mono text-xs">{m.version}</td>
                  <td className="px-5 py-3.5"><StatusBadge status={m.alias} /></td>
                  <td className="px-5 py-3.5 text-muted-foreground">{m.key_metric || "—"}</td>
                  <td className="px-5 py-3.5 text-muted-foreground">{m.owner || "—"}</td>
                  <td className="px-5 py-3.5"><StatusBadge status={m.status} /></td>
                </tr>
              ))}
              {prodModels.length === 0 && (
                <tr>
                  <td className="px-5 py-6 text-center text-muted-foreground" colSpan={6}>No production models found.</td>
                </tr>
              )}
            </tbody>
          </table>
        </motion.div>
      </div>
    </div>
  );
}
