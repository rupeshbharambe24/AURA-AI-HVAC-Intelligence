import { useEffect, useMemo, useState } from "react";
import { motion } from "framer-motion";
import {
  AlertTriangle,
  Play,
  Upload,
  Link as LinkIcon,
} from "lucide-react";
import { PageHeader } from "@/components/common/PageHeader";
import { Tabs, TabsList, TabsTrigger, TabsContent } from "@/components/ui/tabs";
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "@/components/ui/select";
import { Slider } from "@/components/ui/slider";
import { Button } from "@/components/ui/button";
import { Badge } from "@/components/ui/badge";
import {
  ComposedChart,
  Line,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  ResponsiveContainer,
  Scatter,
} from "recharts";
import { useAnomalyBatch, useAnomalyDetect, useAnomalyMetrics, useAnomalyOptions } from "@/hooks/useAnomaly";
import { useJobStatus } from "@/hooks/useOptimize";
import type { AnomalyDetectResponse, AnomalySeriesItem } from "@/api/types/anomaly";

export default function Anomalies() {
  const { data: options } = useAnomalyOptions();
  const { data: anomalyMetrics } = useAnomalyMetrics();
  const detectMutation = useAnomalyDetect();
  const batchMutation = useAnomalyBatch();

  const [threshold, setThreshold] = useState([0.7]);
  const [product, setProduct] = useState("");
  const [aps, setAps] = useState("");
  const [selectedAnomaly, setSelectedAnomaly] = useState<AnomalySeriesItem | null>(null);
  const [result, setResult] = useState<AnomalyDetectResponse | null>(null);

  const [batchFile, setBatchFile] = useState<File | null>(null);
  const [batchJobId, setBatchJobId] = useState<string | null>(null);
  const [batchResult, setBatchResult] = useState<AnomalyDetectResponse[] | null>(null);
  const [batchError, setBatchError] = useState<string | null>(null);

  useEffect(() => {
    if (options?.products?.length && !product) {
      setProduct(options.products[0]);
    }
    if (options?.aps_list?.length && !aps) {
      setAps(options.aps_list[0]);
    }
    if (options?.default_thresholds?.point && threshold[0] === 0.7) {
      setThreshold([options.default_thresholds.point]);
    }
  }, [options, product, aps, threshold]);

  const runDetect = () => {
    if (!product || !aps) return;
    detectMutation.mutate(
      {
        product_id: product,
        aps,
        threshold: threshold[0],
        include_explanations: true,
      },
      {
        onSuccess: (data) => {
          setResult(data);
          const first = data.series.find(s => s.is_anomaly) || null;
          setSelectedAnomaly(first);
        },
      }
    );
  };

  const chartData = useMemo(() => {
    return result?.series || [];
  }, [result]);

  const anomalies = useMemo(() => {
    return (result?.series || []).filter(d => d.is_anomaly);
  }, [result]);

  const batchRows = useMemo(() => {
    const rows: Array<Record<string, string | number | boolean>> = [];
    (batchResult || []).forEach(res => {
      (res.series || []).forEach(s => {
        rows.push({
          product_id: res.product_id,
          aps: res.aps,
          date: s.date,
          demand: s.demand,
          expected: s.expected,
          is_anomaly: s.is_anomaly,
          anomaly_type: s.anomaly_type || s.anomaly_family || "anomaly",
          score: s.anomaly_score,
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
    link.download = "anomaly_batch_results.csv";
    link.click();
    URL.revokeObjectURL(url);
  };

  const jobStatus = useJobStatus(batchJobId ?? undefined, !!batchJobId);

  useEffect(() => {
    if (jobStatus.data?.status === "completed" && jobStatus.data.result?.results) {
      setBatchResult(jobStatus.data.result.results as AnomalyDetectResponse[]);
    }
  }, [jobStatus.data]);

  const uploadBatch = () => {
    if (!batchFile) return;
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

  return (
    <div className="page-container">
      <PageHeader
        icon={AlertTriangle}
        title="Anomaly Detection"
        description="Detect and explain outliers in demand signals"
      />

      <Tabs defaultValue="playground" className="w-full">
        <TabsList className="bg-card border border-border">
          <TabsTrigger value="playground">Playground</TabsTrigger>
          <TabsTrigger value="batch">Batch Test</TabsTrigger>
          <TabsTrigger value="explain">Explain</TabsTrigger>
          <TabsTrigger value="api">API</TabsTrigger>
        </TabsList>

        {/* ================= PLAYGROUND ================= */}
        <TabsContent value="playground" className="tab-content">
          <div className="grid grid-cols-1 lg:grid-cols-4 gap-6">

            {/* Controls */}
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
                <label className="text-xs text-muted-foreground">APS</label>
                <Select value={aps} onValueChange={setAps}>
                  <SelectTrigger className="bg-muted/50 border-0">
                    <SelectValue placeholder="Select" />
                  </SelectTrigger>
                  <SelectContent>
                    {(options?.aps_list || []).map(a => (
                      <SelectItem key={a} value={a}>{a}</SelectItem>
                    ))}
                  </SelectContent>
                </Select>
              </div>

              <div>
                <label className="text-xs text-muted-foreground">
                  Threshold (Precision ↔ Recall): {threshold[0]}
                </label>
                <Slider
                  value={threshold}
                  onValueChange={setThreshold}
                  min={0.3}
                  max={4}
                  step={0.1}
                />
              </div>

              <Button className="w-full gap-2" onClick={runDetect} disabled={detectMutation.isPending}>
                <Play className="w-4 h-4" />
                Detect Anomalies
              </Button>

              {result?.warnings?.length ? (
                <div className="text-xs text-amber-500">
                  {result.warnings.map((w, i) => (<div key={i}>{w}</div>))}
                </div>
              ) : null}
            </div>

            {/* Output */}
            <div className="lg:col-span-3 space-y-4">

              {/* Timeline */}
              <div className="glass-card p-5">
                <h3 className="section-title mb-4">Anomaly Timeline</h3>
                <div className="h-72">
                  <ResponsiveContainer width="100%" height="100%">
                    <ComposedChart data={chartData}>
                      <CartesianGrid strokeDasharray="3 3" />
                      <XAxis dataKey="date" interval={9} tick={{ fontSize: 10 }} />
                      <YAxis />
                      <Tooltip />
                      <Line type="monotone" dataKey="expected" stroke="hsl(225 10% 40%)" strokeDasharray="5 5" dot={false} />
                      <Line type="monotone" dataKey="demand" stroke="hsl(199 89% 48%)" strokeWidth={2} dot={false} />
                      <Scatter data={anomalies} dataKey="demand" fill="hsl(0 72% 51%)" r={6} />
                    </ComposedChart>
                  </ResponsiveContainer>
                </div>
              </div>

              <div className="glass-card p-5">
                <h3 className="section-title mb-4">Summary Metrics</h3>
                {!result ? (
                  <p className="text-sm text-muted-foreground">Run detection to see summary metrics.</p>
                ) : (
                  <>
                    <div className="grid grid-cols-2 lg:grid-cols-4 gap-4">
                      <div className="bg-muted/50 rounded-xl p-4 text-center">
                        <p className="text-xs text-muted-foreground">Total Points</p>
                        <p className="text-xl font-bold">{result.summary.total}</p>
                      </div>
                      <div className="bg-muted/50 rounded-xl p-4 text-center">
                        <p className="text-xs text-muted-foreground">Anomalies</p>
                        <p className="text-xl font-bold">{result.summary.anomalies}</p>
                      </div>
                      <div className="bg-muted/50 rounded-xl p-4 text-center">
                        <p className="text-xs text-muted-foreground">Anomaly Rate</p>
                        <p className="text-xl font-bold">
                          {result.summary.total ? ((result.summary.anomalies / result.summary.total) * 100).toFixed(1) : "0"}%
                        </p>
                      </div>
                      <div className="bg-muted/50 rounded-xl p-4 text-center">
                        <p className="text-xs text-muted-foreground">Families</p>
                        <p className="text-xl font-bold">{Object.keys(result.summary.by_family || {}).length}</p>
                      </div>
                    </div>
                    <div className="mt-3 text-xs text-muted-foreground">
                      <p className="font-semibold mb-1">Unsupervised summary metrics</p>
                      {Object.entries(result.summary.by_family || {}).map(([k, v]) => (
                        <div key={k}>{k}: {v}</div>
                      ))}
                    </div>
                  </>
                )}

                {anomalyMetrics?.metrics?.length ? (
                  <div className="mt-4 text-xs text-muted-foreground">
                    <p className="font-semibold mb-1">Model Metrics</p>
                    {anomalyMetrics.metrics.map((m, i) => (
                      <div key={i}>{m.label}: {m.value}</div>
                    ))}
                  </div>
                ) : (
                  <p className="text-xs text-muted-foreground mt-4">Model-level metrics unavailable.</p>
                )}
              </div>

              {/* Anomaly Table */}
              <div className="glass-card overflow-hidden">
                <table className="w-full text-sm">
                  <thead>
                    <tr className="border-b border-border text-left text-xs text-muted-foreground uppercase">
                      <th className="px-5 py-3">Date</th>
                      <th className="px-5 py-3">Value</th>
                      <th className="px-5 py-3">Expected</th>
                      <th className="px-5 py-3">Score</th>
                      <th className="px-5 py-3">Type</th>
                    </tr>
                  </thead>
                  <tbody>
                    {anomalies.length === 0 ? (
                      <tr>
                        <td colSpan={5} className="px-5 py-6 text-center text-muted-foreground">
                          Run detection to view anomalies.
                        </td>
                      </tr>
                    ) : (
                      anomalies.map(a => (
                        <tr
                          key={a.date}
                          className="border-b border-border/50 hover:bg-muted/30 cursor-pointer"
                          onClick={() => setSelectedAnomaly(a)}
                        >
                          <td className="px-5 py-3 font-mono text-xs">{a.date}</td>
                          <td className="px-5 py-3 font-medium text-destructive">{a.demand}</td>
                          <td className="px-5 py-3 text-muted-foreground">{a.expected}</td>
                          <td className="px-5 py-3">
                            <div className="flex items-center gap-2">
                              <div className="w-16 h-1.5 rounded-full bg-muted overflow-hidden">
                                <div
                                  className="h-full bg-destructive"
                                  style={{ width: `${Math.min(a.anomaly_score * 10, 100)}%` }}
                                />
                              </div>
                              <span className="text-xs">{a.anomaly_score.toFixed(2)}</span>
                            </div>
                          </td>
                          <td className="px-5 py-3">
                            <Badge variant="outline">{a.anomaly_family || "Anomaly"}</Badge>
                          </td>
                        </tr>
                      ))
                    )}
                  </tbody>
                </table>
              </div>
            </div>
          </div>
        </TabsContent>

        {/* ================= BATCH TEST ================= */}
        <TabsContent value="batch" className="tab-content">
          <div className="glass-card p-8 flex flex-col items-center text-center space-y-4">
            <div className="w-16 h-16 rounded-2xl bg-muted flex items-center justify-center">
              <Upload className="w-8 h-8 text-muted-foreground" />
            </div>
            <h3 className="text-base font-semibold">Upload CSV for Batch Detection</h3>
            <p className="text-sm text-muted-foreground max-w-sm">
              CSV columns: <code>date</code>, <code>product_id</code>, <code>value</code> or <code>demand</code>.
            </p>
            <input
              type="file"
              accept=".csv"
              onChange={(e) => setBatchFile(e.target.files?.[0] || null)}
            />
            <div className="flex items-center gap-2">
              <Button onClick={uploadBatch} disabled={!batchFile || batchMutation.isPending}>
                {batchMutation.isPending ? "Uploading..." : "Upload & Run"}
              </Button>
              <Button variant="outline" onClick={resetBatch} disabled={batchMutation.isPending}>
                Reset
              </Button>
            </div>

            {batchJobId && (
              <p className="text-xs text-muted-foreground">Job: {batchJobId} ({jobStatus.data?.status})</p>
            )}
            {batchError && (
              <p className="text-xs text-destructive">Error: {batchError}</p>
            )}

            {batchRows.length > 0 ? (
              <div className="w-full space-y-3">
                <div className="flex items-center justify-between">
                  <p className="text-xs text-muted-foreground">Rows processed: {batchRows.length}</p>
                  <Button variant="outline" size="sm" onClick={downloadBatchCsv}>Download CSV</Button>
                </div>
                <div className="overflow-auto border border-border rounded-xl">
                  <table className="w-full text-xs">
                    <thead>
                      <tr className="border-b border-border text-muted-foreground">
                        <th className="px-3 py-2 text-left">Product</th>
                        <th className="px-3 py-2">APS</th>
                        <th className="px-3 py-2">Date</th>
                        <th className="px-3 py-2">Demand</th>
                        <th className="px-3 py-2">Expected</th>
                        <th className="px-3 py-2">Anomaly</th>
                        <th className="px-3 py-2">Type</th>
                        <th className="px-3 py-2">Score</th>
                      </tr>
                    </thead>
                    <tbody>
                      {batchRows.map((r, i) => (
                        <tr key={`${r.product_id}-${r.date}-${i}`} className="border-b border-border/40">
                          <td className="px-3 py-2 text-left">{r.product_id}</td>
                          <td className="px-3 py-2 text-center">{r.aps}</td>
                          <td className="px-3 py-2 text-center">{r.date}</td>
                          <td className="px-3 py-2 text-center">{r.demand}</td>
                          <td className="px-3 py-2 text-center">{r.expected}</td>
                          <td className="px-3 py-2 text-center">{r.is_anomaly ? "Yes" : "No"}</td>
                          <td className="px-3 py-2 text-center">{r.anomaly_type}</td>
                          <td className="px-3 py-2 text-center">{r.score}</td>
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
        <TabsContent value="explain" className="tab-content">
          <div className="glass-card p-6 space-y-6">
            <h3 className="section-title">Why Was This Flagged?</h3>

            {selectedAnomaly ? (
              <>
                <div className="space-y-2">
                  <p className="text-sm">
                    <strong>Residual:</strong> {selectedAnomaly.residual.toFixed(2)}
                  </p>
                  <p className="text-sm">
                    <strong>Anomaly Score:</strong> {selectedAnomaly.anomaly_score.toFixed(2)}
                  </p>
                  <p className="text-sm">
                    <strong>Root Cause:</strong> {selectedAnomaly.root_cause || "—"}
                  </p>
                </div>

                <div>
                  <h4 className="text-sm font-semibold mb-2">Root Cause Evidence</h4>
                  <ul className="list-disc list-inside text-sm space-y-1">
                    {(selectedAnomaly.evidence || []).map((e, i) => (
                      <li key={i}>{e.type}: {e.detail}</li>
                    ))}
                  </ul>
                </div>

                <div className="flex items-center gap-2 text-xs text-muted-foreground">
                  <LinkIcon className="w-3 h-3" />
                  Evidence links available in backend logs
                </div>
              </>
            ) : (
              <p className="text-sm text-muted-foreground">
                Select an anomaly from the table or timeline to view explanation.
              </p>
            )}
          </div>
        </TabsContent>

        {/* ================= API ================= */}
        <TabsContent value="api" className="tab-content">
          <div className="glass-card p-6 space-y-4">
            <h3 className="section-title">API Reference</h3>

            <pre className="text-xs bg-muted/50 p-4 rounded-xl">
{`POST /api/v1/anomaly/detect
{
  "product_id": "SKU001",
  "date_range": ["2024-01-01", "2024-03-01"],
  "threshold": 0.7
}

POST /api/v1/anomaly/batch (multipart/form-data)
file=@data.csv`}
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
