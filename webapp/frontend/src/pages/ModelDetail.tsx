import { useParams, Link } from "react-router-dom";
import { motion } from "framer-motion";
import { Brain, ArrowLeft, FileText, BarChart3, Shield, AlertTriangle, GitBranch } from "lucide-react";
import { PageHeader } from "@/components/common/PageHeader";
import { StatusBadge } from "@/components/common/StatusBadge";
import { Tabs, TabsList, TabsTrigger, TabsContent } from "@/components/ui/tabs";
import { useModelDetail, useModelExplainability, useModelMetrics, useModelVersions } from "@/hooks/useModels";

export default function ModelDetail() {
  const { modelId } = useParams();
  const { data: modelData } = useModelDetail(modelId);
  const { data: metricsData } = useModelMetrics(modelId);
  const { data: explainData } = useModelExplainability(modelId);
  const { data: versionsData } = useModelVersions(modelId);

  const model = modelData?.model;

  return (
    <div className="page-container">
      <Link to="/models" className="inline-flex items-center gap-1 text-sm text-muted-foreground hover:text-foreground transition-colors mb-2">
        <ArrowLeft className="w-4 h-4" /> Back to Registry
      </Link>

      <PageHeader icon={Brain} title={`${model?.name || "Model"} — ${model?.version || ""}`} description={`Owner: ${model?.owner || "N/A"} · Alias: ${model?.alias || "N/A"}`}>
        {model?.status ? <StatusBadge status={model.status} /> : null}
      </PageHeader>

      <Tabs defaultValue="overview" className="w-full">
        <TabsList className="bg-card border border-border">
          <TabsTrigger value="overview">Overview</TabsTrigger>
          <TabsTrigger value="metrics">Metrics</TabsTrigger>
          <TabsTrigger value="explain">Explainability</TabsTrigger>
          <TabsTrigger value="history">Version History</TabsTrigger>
        </TabsList>

        <TabsContent value="overview" className="tab-content">
          <div className="grid grid-cols-1 lg:grid-cols-2 gap-4">
            {[
              { icon: FileText, title: "Notes", content: model?.notes || "No notes available." },
              { icon: BarChart3, title: "Training Data", content: `Training period: ${model?.training_period || "N/A"}. Dataset hash: ${model?.dataset_hash || "N/A"}.` },
              { icon: Shield, title: "Owner / Alias", content: `Owner: ${model?.owner || "N/A"}. Alias: ${model?.alias || "N/A"}.` },
              { icon: AlertTriangle, title: "Status", content: `Status: ${model?.status || "N/A"}.` },
            ].map((card, i) => (
              <motion.div key={card.title} initial={{ opacity: 0, y: 20 }} animate={{ opacity: 1, y: 0 }} transition={{ delay: i * 0.05 }} className="glass-card p-5 space-y-2">
                <div className="flex items-center gap-2">
                  <card.icon className="w-4 h-4 text-primary" />
                  <h3 className="text-sm font-semibold">{card.title}</h3>
                </div>
                <p className="text-sm text-muted-foreground leading-relaxed">{card.content}</p>
              </motion.div>
            ))}
          </div>
        </TabsContent>

        <TabsContent value="metrics" className="tab-content">
          <div className="glass-card p-6 space-y-4">
            <h3 className="section-title">Performance Metrics</h3>
            <div className="grid grid-cols-3 gap-4">
              {(metricsData?.metrics || []).map(m => (
                <div key={m.label} className="bg-muted/50 rounded-xl p-4 text-center">
                  <p className="text-xs text-muted-foreground mb-1">{m.label}</p>
                  <p className="text-lg font-bold">{m.value}</p>
                </div>
              ))}
              {(!metricsData?.metrics || metricsData.metrics.length === 0) && (
                <div className="text-sm text-muted-foreground">No metrics available.</div>
              )}
            </div>
          </div>
        </TabsContent>

        <TabsContent value="explain" className="tab-content">
          <div className="glass-card p-6">
            <h3 className="section-title mb-4">Global Feature Importance</h3>
            <div className="space-y-3">
              {(explainData?.explainability || []).map(f => (
                <div key={f.feature} className="flex items-center gap-3">
                  <span className="text-xs font-mono w-40 text-muted-foreground">{f.feature}</span>
                  <div className="flex-1 h-3 rounded-full bg-muted overflow-hidden">
                    <motion.div
                      initial={{ width: 0 }}
                      animate={{ width: `${Math.min(f.importance * 100, 100)}%` }}
                      transition={{ duration: 0.6, delay: 0.2 }}
                      className="h-full rounded-full bg-gradient-to-r from-primary to-accent"
                    />
                  </div>
                  <span className="text-xs font-mono w-12 text-right">{(f.importance * 100).toFixed(0)}%</span>
                </div>
              ))}
              {(!explainData?.explainability || explainData.explainability.length === 0) && (
                <p className="text-sm text-muted-foreground">No explainability data.</p>
              )}
            </div>
          </div>
        </TabsContent>

        <TabsContent value="history" className="tab-content">
          <div className="glass-card p-6 space-y-4">
            <h3 className="section-title flex items-center gap-2"><GitBranch className="w-4 h-4 text-primary" /> Version History</h3>
            <div className="space-y-3">
              {(versionsData?.versions || []).map(v => (
                <div key={v.version} className="flex items-start gap-4 p-3 rounded-xl hover:bg-muted/30 transition-colors">
                  <div className="w-8 h-8 rounded-lg bg-primary/10 flex items-center justify-center text-xs font-bold text-primary">{v.version}</div>
                  <div>
                    <p className="text-sm font-medium">{v.note || "No notes"}</p>
                    <p className="text-xs text-muted-foreground">{v.date || ""} · Run: <span className="font-mono">{v.run_id || "—"}</span></p>
                  </div>
                </div>
              ))}
              {(!versionsData?.versions || versionsData.versions.length === 0) && (
                <p className="text-sm text-muted-foreground">No version history available.</p>
              )}
            </div>
          </div>
        </TabsContent>
      </Tabs>
    </div>
  );
}
