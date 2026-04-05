import { useEffect, useMemo, useState } from "react";
import { motion } from "framer-motion";
import {
  PieChart as PieIcon,
  Play,
  Newspaper,
  TrendingDown,
  TrendingUp,
  AlertTriangle,
  Upload,
} from "lucide-react";
import { PageHeader } from "@/components/common/PageHeader";
import { Tabs, TabsList, TabsTrigger, TabsContent } from "@/components/ui/tabs";
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from "@/components/ui/select";
import { Slider } from "@/components/ui/slider";
import { Button } from "@/components/ui/button";
import { Badge } from "@/components/ui/badge";
import { Switch } from "@/components/ui/switch";
import {
  AreaChart,
  Area,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  ResponsiveContainer,
} from "recharts";
import { useJobStatus } from "@/hooks/useOptimize";
import { useMarketShareBatch, useMarketShareMetrics, useMarketShareOptions, useMarketSharePredict } from "@/hooks/useMarketShare";
import type { MarketShareResponse } from "@/api/types/marketShare";

export default function MarketShare() {
  const { data: options } = useMarketShareOptions();
  const predictMutation = useMarketSharePredict();
  const batchMutation = useMarketShareBatch();
  const { data: metrics } = useMarketShareMetrics();

  const [product, setProduct] = useState("");
  const [horizon, setHorizon] = useState(3);
  const [newsFilters, setNewsFilters] = useState({
    competitor: true,
    regulation: true,
    supply_chain: true,
    pricing: true,
  });

  const [result, setResult] = useState<MarketShareResponse | null>(null);
  const [lastRunAt, setLastRunAt] = useState<string | null>(null);

  const [batchFile, setBatchFile] = useState<File | null>(null);
  const [batchJobId, setBatchJobId] = useState<string | null>(null);
  const [batchResult, setBatchResult] = useState<MarketShareResponse[] | null>(null);
  const [batchError, setBatchError] = useState<string | null>(null);

  const jobStatus = useJobStatus(batchJobId ?? undefined, !!batchJobId);

  useEffect(() => {
    if (options?.products?.length && !product) {
      setProduct(options.products[0]);
    }
  }, [options, product]);

  useEffect(() => {
    if (jobStatus.data?.status === "completed" && jobStatus.data.result?.results) {
      setBatchResult(jobStatus.data.result.results as MarketShareResponse[]);
    }
  }, [jobStatus.data]);

  const runAnalysis = () => {
    if (!product) return;
    predictMutation.mutate(
      {
        product_id: product,
        horizon_months: horizon,
        as_of_date: options?.default_as_of_date,
        news_filters: newsFilters,
      },
      {
        onSuccess: (data) => {
          setResult(data);
          setLastRunAt(new Date().toLocaleString());
        },
      }
    );
  };

  const uploadBatch = () => {
    if (!batchFile) return;
    setBatchError(null);
    batchMutation.mutate(batchFile, {
      onSuccess: (data) => {
        if (data.job_id) {
          setBatchJobId(data.job_id);
        } else if (data.results) {
          setBatchResult(data.results);
        }
      },
      onError: (err: any) => {
        setBatchError(err?.message || "Batch upload failed");
      },
    });
  };

  const resetBatch = () => {
    setBatchFile(null);
    setBatchJobId(null);
    setBatchResult(null);
    setBatchError(null);
  };

  const chartData = useMemo(() => {
    if (!result?.forecast) return [];
    return result.forecast.map(f => ({
      month: f.month,
      ourShare: f.our_share,
      lower: f.lower ?? null,
      upper: f.upper ?? null,
    }));
  }, [result]);

  const batchRows = useMemo(() => {
    const rows: Array<Record<string, string | number>> = [];
    (batchResult || []).forEach(res => {
      const alertsCount = res.alerts?.length || 0;
      (res.forecast || []).forEach(f => {
        rows.push({
          product_id: res.product_id,
          horizon_months: res.horizon_months,
          month: f.month,
          our_share: f.our_share,
          lower: f.lower ?? "",
          upper: f.upper ?? "",
          alerts_count: alertsCount,
        });
      });
    });
    return rows;
  }, [batchResult]);

  const downloadBatchCsv = () => {
    if (!batchRows.length) return;
    const headers = Object.keys(batchRows[0]);
    const csv = [
      headers.join(","),
      ...batchRows.map(r => headers.map(h => JSON.stringify(r[h] ?? "")).join(",")),
    ].join("\n");
    const blob = new Blob([csv], { type: "text/csv;charset=utf-8;" });
    const url = URL.createObjectURL(blob);
    const link = document.createElement("a");
    link.href = url;
    link.download = "market_share_batch_results.csv";
    link.click();
    URL.revokeObjectURL(url);
  };

  const firstAlert = result?.alerts?.[0];
  const riskDetected = (result?.alerts || []).some(a => a.type === "risk_drop");

  return (
    <div className="page-container">
      <PageHeader
        icon={PieIcon}
        title="Market Share Intelligence"
        description="Forecast market position with news-driven signals"
      />

      <Tabs defaultValue="playground">
        <TabsList className="bg-card border border-border">
          <TabsTrigger value="playground">Playground</TabsTrigger>
          <TabsTrigger value="batch">Batch Test</TabsTrigger>
          <TabsTrigger value="explain">Explain</TabsTrigger>
          <TabsTrigger value="metrics">Metrics</TabsTrigger>
          <TabsTrigger value="api">API</TabsTrigger>
        </TabsList>

        {/* ================= PLAYGROUND ================= */}
        <TabsContent value="playground" className="tab-content">
          <div className="grid grid-cols-1 lg:grid-cols-4 gap-6">
            <div className="glass-card p-5 space-y-5">
              <h3 className="text-sm font-semibold">Configuration</h3>

              <div>
                <label className="text-xs text-muted-foreground">Product</label>
                <Select value={product} onValueChange={setProduct}>
                  <SelectTrigger className="bg-muted/50 border-0">
                    <SelectValue placeholder="Select" />
                  </SelectTrigger>
                  <SelectContent>
                    {(options?.products || []).map(p => (
                      <SelectItem key={p} value={p}>{p}</SelectItem>
                    ))}
                  </SelectContent>
                </Select>
              </div>

              <div>
                <div className="flex items-center justify-between">
                  <label className="text-xs text-muted-foreground">Horizon (3–6 months)</label>
                  <span className="text-xs font-mono text-muted-foreground">{horizon}</span>
                </div>
                <Slider min={3} max={6} step={1} value={[horizon]} onValueChange={v => setHorizon(v[0])} />
              </div>

              <div className="space-y-2">
                <p className="text-xs font-semibold">News Filters</p>
                {Object.entries(newsFilters).map(([k, v]) => (
                  <div key={k} className="flex items-center justify-between">
                    <span className="text-xs capitalize">{k.replace("_", " ")}</span>
                    <Switch checked={v} onCheckedChange={val => setNewsFilters(prev => ({ ...prev, [k]: val }))} />
                  </div>
                ))}
              </div>

              <Button className="w-full gap-2" onClick={runAnalysis} disabled={predictMutation.isPending}>
                <Play className="w-4 h-4" /> Run Analysis
              </Button>

              {result?.warnings?.length ? (
                <div className="text-xs text-amber-500">
                  {result.warnings.map((w, i) => (<div key={i}>{w}</div>))}
                </div>
              ) : null}
            </div>

            <div className="lg:col-span-3 space-y-4">
              {firstAlert && (
                <div className={`flex items-center gap-3 p-4 rounded-xl ${riskDetected ? "bg-destructive/10 border border-destructive/30" : "bg-muted/40 border border-border"}`}>
                  <AlertTriangle className={`w-5 h-5 ${riskDetected ? "text-destructive" : "text-muted-foreground"}`} />
                  <p className="text-sm">
                    <strong>{firstAlert.type.replace("_", " ")}:</strong> {firstAlert.message}
                  </p>
                </div>
              )}

              <div className="glass-card p-5">
                <h3 className="section-title mb-4">Market Share Forecast (with Confidence Interval)</h3>

                <div className="h-72">
                  <ResponsiveContainer width="100%" height="100%">
                    <AreaChart data={chartData}>
                      <CartesianGrid strokeDasharray="3 3" />
                      <XAxis dataKey="month" />
                      <YAxis unit="%" />
                      <Tooltip />
                      <Area dataKey="upper" stroke="none" fill="hsl(199 89% 48% / 0.15)" />
                      <Area dataKey="lower" stroke="none" fill="hsl(225 25% 10%)" />
                      <Area type="monotone" dataKey="ourShare" stroke="hsl(199 89% 48%)" strokeWidth={2} fill="none" />
                    </AreaChart>
                  </ResponsiveContainer>
                </div>
              </div>

              <div className="glass-card p-5">
                <h3 className="section-title mb-4 flex items-center gap-2">
                  <Newspaper className="w-4 h-4 text-primary" />
                  News Timeline
                </h3>

                <div className="space-y-3">
                  {(result?.news_timeline || []).map(news => (
                    <div key={`${news.date}-${news.headline}`} className="flex items-start gap-3 p-3 rounded-xl hover:bg-muted/30">
                      {news.sentiment === "positive"
                        ? <TrendingUp className="w-4 h-4 text-accent mt-1" />
                        : <TrendingDown className="w-4 h-4 text-destructive mt-1" />}
                      <div className="flex-1">
                        <p className="text-sm font-medium">{news.headline}</p>
                        <p className="text-xs text-muted-foreground">{news.date}</p>
                      </div>
                      <Badge variant="outline">{news.relevance.toFixed(2)}</Badge>
                    </div>
                  ))}
                </div>
              </div>
            </div>
          </div>
        </TabsContent>

        {/* ================= BATCH TEST ================= */}
        <TabsContent value="batch" className="tab-content">
          <div className="glass-card p-6 space-y-6">
            <h3 className="section-title">Batch Test (CSV Upload)</h3>

            <div className="border border-dashed border-border rounded-xl p-6 text-center">
              <Upload className="mx-auto mb-2 w-5 h-5" />
              <p className="text-sm font-medium">Upload CSV file</p>
              <p className="text-xs text-muted-foreground">Required columns: product_id, horizon_months</p>
              <input type="file" accept=".csv" onChange={(e) => setBatchFile(e.target.files?.[0] || null)} />
              <div className="mt-4 flex items-center justify-center gap-2">
                <Button onClick={uploadBatch} disabled={!batchFile || batchMutation.isPending}>
                  {batchMutation.isPending ? "Uploading..." : "Upload & Run"}
                </Button>
                <Button variant="outline" onClick={resetBatch} disabled={batchMutation.isPending}>
                  Reset
                </Button>
              </div>
            </div>

            {batchJobId && (
              <p className="text-xs text-muted-foreground">Job: {batchJobId} ({jobStatus.data?.status})</p>
            )}
            {batchError && (
              <p className="text-xs text-destructive">Error: {batchError}</p>
            )}

            {batchRows.length > 0 ? (
              <div className="space-y-3">
                <div className="flex items-center justify-between">
                  <p className="text-xs text-muted-foreground">Rows processed: {batchRows.length}</p>
                  <Button variant="outline" size="sm" onClick={downloadBatchCsv}>Download CSV</Button>
                </div>
                <div className="overflow-auto border border-border rounded-xl">
                  <table className="w-full text-xs">
                    <thead>
                      <tr className="border-b border-border text-muted-foreground">
                        <th className="px-3 py-2 text-left">Product</th>
                        <th className="px-3 py-2">Horizon</th>
                        <th className="px-3 py-2">Month</th>
                        <th className="px-3 py-2">Share</th>
                        <th className="px-3 py-2">Lower</th>
                        <th className="px-3 py-2">Upper</th>
                        <th className="px-3 py-2">Alerts</th>
                      </tr>
                    </thead>
                    <tbody>
                      {batchRows.map((r, i) => (
                        <tr key={`${r.product_id}-${r.month}-${i}`} className="border-b border-border/40">
                          <td className="px-3 py-2 text-left">{r.product_id}</td>
                          <td className="px-3 py-2 text-center">{r.horizon_months}</td>
                          <td className="px-3 py-2 text-center">{r.month}</td>
                          <td className="px-3 py-2 text-center">{r.our_share}</td>
                          <td className="px-3 py-2 text-center">{r.lower || "—"}</td>
                          <td className="px-3 py-2 text-center">{r.upper || "—"}</td>
                          <td className="px-3 py-2 text-center">{r.alerts_count}</td>
                        </tr>
                      ))}
                    </tbody>
                  </table>
                </div>
              </div>
            ) : (
              <p className="text-xs text-muted-foreground">No batch results yet.</p>
            )}
          </div>
        </TabsContent>

        {/* ================= EXPLAIN ================= */}
        <TabsContent value="explain">
          <div className="glass-card p-6 space-y-6">
            <h3 className="section-title">Top Drivers & SHAP Explanation</h3>

            {(result?.drivers || []).map(d => (
              <div key={d.name} className="flex items-center gap-3">
                <span className="text-xs w-40">{d.name}</span>
                <div className="flex-1 h-3 bg-muted rounded-full overflow-hidden">
                  <motion.div initial={{ width: 0 }} animate={{ width: `${d.importance_pct}%` }} className="h-full bg-gradient-to-r from-primary to-accent" />
                </div>
                <span className="text-xs">{d.importance_pct.toFixed(0)}%</span>
              </div>
            ))}
          </div>
        </TabsContent>

        {/* ================= METRICS ================= */}
        <TabsContent value="metrics">
          <div className="glass-card p-6 space-y-6">
            <h3 className="section-title">Offline Evaluation Metrics</h3>

            {!result ? (
              <p className="text-sm text-muted-foreground">Run market-share analysis to see metrics.</p>
            ) : (
              <>
                <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
                  {[
                    { label: "MAE", value: result?.metrics?.mae_pct ?? "—" },
                    { label: "RMSE", value: result?.metrics?.rmse_pct ?? "—" },
                    { label: "MAPE", value: result?.metrics?.mape_pct ?? "—" },
                    { label: "Coverage", value: result?.metrics?.coverage_pct ?? "—" },
                  ].map(m => (
                    <div key={m.label} className="p-4 rounded-xl bg-muted/40">
                      <p className="text-xs text-muted-foreground">{m.label}</p>
                      <p className="text-lg font-semibold">{m.value}</p>
                    </div>
                  ))}
                </div>
                {lastRunAt && (
                  <p className="text-xs text-muted-foreground mt-2">Last updated: {lastRunAt}</p>
                )}
              </>
            )}

            {metrics?.metrics?.length ? (
              <div className="text-xs text-muted-foreground">
                <p className="font-semibold mb-1">Model Metrics</p>
                {metrics.metrics.map((m, i) => (
                  <div key={i}>{m.label}: {m.value}</div>
                ))}
              </div>
            ) : (
              <p className="text-xs text-muted-foreground">Model-level metrics unavailable.</p>
            )}
          </div>
        </TabsContent>

        {/* ================= API ================= */}
        <TabsContent value="api">
          <div className="glass-card p-6 space-y-4">
            <h3 className="section-title">API Reference</h3>

            <pre className="text-xs bg-muted/50 p-4 rounded-xl">
              {`POST /api/v1/market-share/predict
              {
                "product_id": "SKU001",
                "horizon_months": 3,
                "news_filters": {
                  "competitor": true,
                  "regulation": true,
                  "supply_chain": true,
                  "pricing": true
                }
              }`}
            </pre>

            <div className="flex gap-3">
              <Button asChild>
                <a href="http://localhost:8001/docs" target="_blank">Open Swagger</a>
              </Button>
              <Button asChild variant="outline">
                <a href="http://localhost:8001/redoc" target="_blank">Open ReDoc</a>
              </Button>
            </div>
          </div>
        </TabsContent>
      </Tabs>
    </div>
  );
}
