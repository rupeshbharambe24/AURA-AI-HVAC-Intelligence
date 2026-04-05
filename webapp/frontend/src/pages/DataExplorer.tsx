import { useEffect, useMemo, useState } from "react";
import { motion } from "framer-motion";
import { Database, Search, ArrowUpDown } from "lucide-react";
import { PageHeader } from "@/components/common/PageHeader";
import { Input } from "@/components/ui/input";
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from "@/components/ui/select";
import { AreaChart, Area, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer } from "recharts";
import { useDatasetTimeseries, useDatasets } from "@/hooks/useDatasets";
import { isMockMode } from "@/lib/api-client";

export default function DataExplorer() {
  const { data, apiUnavailable } = useDatasets();
  const mock = isMockMode();

  const datasets = data?.datasets || [];
  const [selectedDataset, setSelectedDataset] = useState(datasets[0]?.name || "");

  useEffect(() => {
    if (!selectedDataset && datasets.length) {
      setSelectedDataset(datasets[0].name);
    }
  }, [datasets, selectedDataset]);

  const seriesQuery = useDatasetTimeseries(selectedDataset);

  const ds = useMemo(() => datasets.find(d => d.name === selectedDataset), [datasets, selectedDataset]);

  return (
    <div className="page-container">
      <PageHeader icon={Database} title="Data Explorer" description="Browse datasets, inspect quality, and visualize time series" />

      {apiUnavailable && !mock && (
        <div className="text-xs text-amber-500 mb-3">Dataset API not available. Showing mock data.</div>
      )}

      <div className="flex items-center gap-4">
        <Select value={selectedDataset} onValueChange={setSelectedDataset}>
          <SelectTrigger className="w-48 bg-card border-border">
            <SelectValue />
          </SelectTrigger>
          <SelectContent>
            {datasets.map(d => (
              <SelectItem key={d.name} value={d.name}>{d.name}</SelectItem>
            ))}
          </SelectContent>
        </Select>
        <div className="relative flex-1 max-w-sm">
          <Search className="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-muted-foreground" />
          <Input placeholder="Filter columns..." className="pl-9 bg-card border-border" />
        </div>
      </div>

      {/* Quality Cards */}
      <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">
        {[
          { label: "Rows", value: ds?.rows?.toLocaleString() || "—" },
          { label: "Columns", value: ds?.cols ?? "—" },
          { label: "Quality Score", value: ds?.quality != null ? `${ds.quality}%` : "—" },
          { label: "Missingness", value: ds?.missingness != null ? `${ds.missingness}%` : "—" },
        ].map((stat, i) => (
          <motion.div key={stat.label} initial={{ opacity: 0, y: 20 }} animate={{ opacity: 1, y: 0 }} transition={{ delay: i * 0.05 }} className="stat-card">
            <p className="text-xs text-muted-foreground uppercase tracking-wider">{stat.label}</p>
            <p className="text-2xl font-bold">{stat.value}</p>
          </motion.div>
        ))}
      </div>

      {/* Time Series Plot */}
      <motion.div initial={{ opacity: 0 }} animate={{ opacity: 1 }} transition={{ delay: 0.2 }} className="glass-card p-5">
        <h3 className="section-title mb-4">Time Series Preview — {selectedDataset}</h3>
        <div className="h-64">
          <ResponsiveContainer width="100%" height="100%">
            <AreaChart data={seriesQuery.data?.series || []}>
              <defs>
                <linearGradient id="dataGrad" x1="0" y1="0" x2="0" y2="1">
                  <stop offset="0%" stopColor="hsl(199 89% 48%)" stopOpacity={0.3} />
                  <stop offset="100%" stopColor="hsl(199 89% 48%)" stopOpacity={0} />
                </linearGradient>
              </defs>
              <CartesianGrid strokeDasharray="3 3" stroke="hsl(225 20% 14%)" />
              <XAxis dataKey="date" tick={{ fontSize: 11, fill: "hsl(225 10% 50%)" }} axisLine={false} tickLine={false} />
              <YAxis tick={{ fontSize: 11, fill: "hsl(225 10% 50%)" }} axisLine={false} tickLine={false} />
              <Tooltip contentStyle={{ background: "hsl(225 25% 10%)", border: "1px solid hsl(225 20% 14%)", borderRadius: 12, fontSize: 12 }} />
              <Area type="monotone" dataKey="value" stroke="hsl(199 89% 48%)" fill="url(#dataGrad)" strokeWidth={2} />
            </AreaChart>
          </ResponsiveContainer>
        </div>
      </motion.div>

      {/* Dataset Table */}
      <motion.div initial={{ opacity: 0 }} animate={{ opacity: 1 }} transition={{ delay: 0.3 }} className="glass-card overflow-hidden">
        <table className="w-full text-sm">
          <thead>
            <tr className="border-b border-border text-left text-xs text-muted-foreground uppercase tracking-wider">
              <th className="px-5 py-3 cursor-pointer hover:text-foreground transition-colors">
                <span className="flex items-center gap-1">Dataset <ArrowUpDown className="w-3 h-3" /></span>
              </th>
              <th className="px-5 py-3">Rows</th>
              <th className="px-5 py-3">Columns</th>
              <th className="px-5 py-3">Quality</th>
              <th className="px-5 py-3">Missingness</th>
              <th className="px-5 py-3">Last Updated</th>
            </tr>
          </thead>
          <tbody>
            {datasets.map(d => (
              <tr key={d.name} className="border-b border-border/50 hover:bg-muted/30 transition-colors cursor-pointer">
                <td className="px-5 py-3.5 font-medium">{d.name}</td>
                <td className="px-5 py-3.5 text-muted-foreground">{d.rows?.toLocaleString?.() ?? d.rows}</td>
                <td className="px-5 py-3.5 text-muted-foreground">{d.cols}</td>
                <td className="px-5 py-3.5">
                  <div className="flex items-center gap-2">
                    <div className="w-16 h-1.5 rounded-full bg-muted overflow-hidden">
                      <div className="h-full rounded-full bg-accent" style={{ width: `${d.quality ?? 0}%` }} />
                    </div>
                    <span className="text-xs text-muted-foreground">{d.quality ?? 0}%</span>
                  </div>
                </td>
                <td className="px-5 py-3.5 text-muted-foreground">{d.missingness ?? 0}%</td>
                <td className="px-5 py-3.5 text-muted-foreground">{d.lastUpdated || "—"}</td>
              </tr>
            ))}
            {datasets.length === 0 && (
              <tr>
                <td className="px-5 py-6 text-center text-muted-foreground" colSpan={6}>No datasets found.</td>
              </tr>
            )}
          </tbody>
        </table>
      </motion.div>
    </div>
  );
}
