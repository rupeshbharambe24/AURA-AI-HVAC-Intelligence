import { useEffect, useMemo, useState } from "react";
import { motion } from "framer-motion";
import { TrendingUp, Play } from "lucide-react";
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
  AreaChart,
  Area,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  ResponsiveContainer,
  Line,
} from "recharts";
import { isMockMode } from "@/lib/api-client";
import { mockForecastData } from "@/lib/mock-data";
import { useForecastMetrics, useForecastOptions, useForecastPredict } from "@/hooks/useForecast";
import type { ForecastResponse } from "@/api/types/forecast";

export default function Forecasting() {
  const { data: options, isLoading: loadingOptions } = useForecastOptions();
  const forecastMutation = useForecastPredict();
  const { data: modelMetrics } = useForecastMetrics();
  const mock = isMockMode();

  const [product, setProduct] = useState("");
  const [aps, setAps] = useState("");
  const [horizon, setHorizon] = useState([6]);
  const [temperatureScenario, setTemperatureScenario] = useState([0]);
  const [housingScenario, setHousingScenario] = useState([0]);
  const [result, setResult] = useState<ForecastResponse | null>(null);
  const [lastRunAt, setLastRunAt] = useState<string | null>(null);

  useEffect(() => {
    if (options?.products?.length && !product) {
      setProduct(options.products[0]);
    }
    if (options?.aps_list?.length && !aps) {
      setAps(options.aps_list[0]);
    }
  }, [options, product, aps]);

  const runForecast = () => {
    if (!product || !aps) return;
    forecastMutation.mutate(
      {
        product_id: product,
        aps,
        horizon_months: horizon[0],
        scenarios: {
          temperature_pct: temperatureScenario[0],
          housing_growth_pct: housingScenario[0],
        },
        include_actuals: true,
        include_explain: true,
      },
      {
        onSuccess: (data) => {
          setResult(data);
          setLastRunAt(new Date().toLocaleString());
        },
      }
    );
  };

  const chartData = useMemo(() => {
    if (result?.forecast?.length) {
      return result.forecast.map(item => ({
        date: item.date,
        actual: item.actual ?? null,
        predicted: item.predicted,
        lower: item.lower ?? null,
        upper: item.upper ?? null,
      }));
    }
    return mock ? mockForecastData : [];
  }, [result, mock]);

  const tableRows = result?.forecast?.length ? result.forecast.slice(0, horizon[0]) : [];

  return (
    <div className="page-container">
      <PageHeader
        icon={TrendingUp}
        title="Demand Forecasting"
        description="Predict future demand with uncertainty and scenario analysis"
      />

      <Tabs defaultValue="playground" className="w-full">
        <TabsList className="bg-card border border-border">
          <TabsTrigger value="playground">Playground</TabsTrigger>
          <TabsTrigger value="explain">Explain</TabsTrigger>
          <TabsTrigger value="metrics">Metrics</TabsTrigger>
          <TabsTrigger value="api">API</TabsTrigger>
        </TabsList>

        {/* ================= PLAYGROUND ================= */}
        <TabsContent value="playground" className="tab-content">
          <div className="grid grid-cols-1 lg:grid-cols-4 gap-6">

            {/* ================= CONTROLS ================= */}
            <div className="glass-card p-5 space-y-5">
              <h3 className="text-sm font-semibold">Configuration</h3>

              <div>
                <label className="text-xs text-muted-foreground">
                  Product / SKU
                </label>
                <Select value={product} onValueChange={setProduct}>
                  <SelectTrigger className="bg-muted/50 border-0">
                    <SelectValue placeholder={loadingOptions ? "Loading..." : "Select"} />
                  </SelectTrigger>
                  <SelectContent>
                    {(options?.products || []).map(p => (
                      <SelectItem key={p} value={p}>
                        {p}
                      </SelectItem>
                    ))}
                  </SelectContent>
                </Select>
              </div>

              <div>
                <label className="text-xs text-muted-foreground">
                  APS
                </label>
                <Select value={aps} onValueChange={setAps}>
                  <SelectTrigger className="bg-muted/50 border-0">
                    <SelectValue placeholder={loadingOptions ? "Loading..." : "Select"} />
                  </SelectTrigger>
                  <SelectContent>
                    {(options?.aps_list || []).map(a => (
                      <SelectItem key={a} value={a}>
                        {a}
                      </SelectItem>
                    ))}
                  </SelectContent>
                </Select>
              </div>

              <div>
                <label className="text-xs text-muted-foreground">
                  Horizon (months): {horizon[0]}
                </label>
                <Slider
                  value={horizon}
                  onValueChange={setHorizon}
                  min={1}
                  max={options?.max_horizon_months || 12}
                  step={1}
                />
              </div>

              <hr className="border-border" />

              <h4 className="text-xs font-semibold">
                Scenario Adjustments
              </h4>

              <div>
                <div className="flex items-center justify-between">
                  <label className="text-xs text-muted-foreground">
                    Temperature Impact (%)
                  </label>
                  <span className="text-xs font-mono text-muted-foreground">{temperatureScenario[0]}%</span>
                </div>
                <Slider
                  value={temperatureScenario}
                  onValueChange={setTemperatureScenario}
                  min={-20}
                  max={20}
                  step={2}
                />
              </div>

              <div>
                <div className="flex items-center justify-between">
                  <label className="text-xs text-muted-foreground">
                    Housing Growth (%)
                  </label>
                  <span className="text-xs font-mono text-muted-foreground">{housingScenario[0]}%</span>
                </div>
                <Slider
                  value={housingScenario}
                  onValueChange={setHousingScenario}
                  min={-15}
                  max={15}
                  step={1}
                />
              </div>

              <Button className="w-full gap-2" onClick={runForecast} disabled={forecastMutation.isPending}>
                <Play className="w-4 h-4" />
                Run Forecast
              </Button>

              {result?.warnings?.length ? (
                <div className="text-xs text-amber-500">
                  {result.warnings.map((w, i) => (<div key={i}>{w}</div>))}
                </div>
              ) : null}
            </div>

            {/* ================= OUTPUT ================= */}
            <div className="lg:col-span-3 space-y-4">

              {/* Forecast Chart */}
              <div className="glass-card p-5">
                <h3 className="section-title mb-4">
                  Forecast — {product} ({aps})
                </h3>

                <div className="h-80">
                  <ResponsiveContainer width="100%" height="100%">
                    <AreaChart data={chartData}>
                      <defs>
                        <linearGradient id="fcGrad" x1="0" y1="0" x2="0" y2="1">
                          <stop offset="0%" stopColor="hsl(199 89% 48%)" stopOpacity={0.25} />
                          <stop offset="100%" stopColor="hsl(199 89% 48%)" stopOpacity={0} />
                        </linearGradient>
                        <linearGradient id="ciGrad" x1="0" y1="0" x2="0" y2="1">
                          <stop offset="0%" stopColor="hsl(199 89% 48%)" stopOpacity={0.1} />
                          <stop offset="100%" stopColor="hsl(199 89% 48%)" stopOpacity={0.02} />
                        </linearGradient>
                      </defs>

                      <CartesianGrid strokeDasharray="3 3" />
                      <XAxis dataKey="date" />
                      <YAxis />
                      <Tooltip />

                      <Area dataKey="upper" stroke="none" fill="url(#ciGrad)" />
                      <Area dataKey="lower" stroke="none" fill="transparent" />
                      <Area
                        dataKey="predicted"
                        stroke="hsl(199 89% 48%)"
                        strokeWidth={2}
                        fill="url(#fcGrad)"
                      />
                      <Line
                        dataKey="actual"
                        stroke="hsl(160 84% 39%)"
                        strokeWidth={2}
                        dot={{ r: 3 }}
                      />
                    </AreaChart>
                  </ResponsiveContainer>
                </div>
              </div>

              {/* Forecast Table */}
              <div className="glass-card overflow-hidden">
                <table className="w-full text-sm">
                  <thead>
                    <tr className="border-b border-border text-xs uppercase text-muted-foreground">
                      <th className="px-5 py-3 text-left">Month</th>
                      <th className="px-5 py-3">Prediction</th>
                      <th className="px-5 py-3">Lower</th>
                      <th className="px-5 py-3">Upper</th>
                      <th className="px-5 py-3">Key Drivers</th>
                    </tr>
                  </thead>
                  <tbody>
                    {tableRows.length === 0 ? (
                      <tr>
                        <td className="px-5 py-6 text-center text-muted-foreground" colSpan={5}>
                          Run a forecast to see results.
                        </td>
                      </tr>
                    ) : (
                      tableRows.map(row => (
                        <tr key={row.date} className="border-b border-border/50">
                          <td className="px-5 py-3 font-mono text-xs">{row.date}</td>
                          <td className="px-5 py-3 font-medium">{row.predicted}</td>
                          <td className="px-5 py-3 text-muted-foreground">{row.lower ?? "—"}</td>
                          <td className="px-5 py-3 text-muted-foreground">{row.upper ?? "—"}</td>
                          <td className="px-5 py-3">
                            {(row.drivers || ["Seasonality"]).map((d, i) => (
                              <Badge key={`${row.date}-${i}`} variant="outline">{d}</Badge>
                            ))}
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

        {/* ================= EXPLAIN ================= */}
        <TabsContent value="explain" className="tab-content">
          <div className="glass-card p-6 space-y-6">
            <h3 className="section-title">
              SHAP Explanation
            </h3>

            {result?.explain?.local?.length ? (
              <>
                <h4 className="text-sm font-semibold">
                  Local (Selected Month)
                </h4>
                {Object.entries(result.explain.local[0]).map(([feature, value]) => (
                  <div key={feature} className="flex items-center gap-3">
                    <span className="text-xs font-mono w-36 text-muted-foreground">
                      {feature}
                    </span>
                    <div className="flex-1 h-4 bg-muted rounded overflow-hidden">
                      <motion.div
                        initial={{ width: 0 }}
                        animate={{ width: `${Math.abs(value) * 100}%` }}
                        className={`h-full ${value >= 0 ? "bg-accent/40" : "bg-destructive/40"}`}
                      />
                    </div>
                    <span className={`text-xs font-mono ${value >= 0 ? "text-accent" : "text-destructive"}`}>
                      {value.toFixed(2)}
                    </span>
                  </div>
                ))}
              </>
            ) : (
              <p className="text-sm text-muted-foreground">No local explainability available.</p>
            )}

            <hr className="border-border" />

            <h4 className="text-sm font-semibold">
              Global (Overall Model)
            </h4>
            <div className="flex flex-wrap gap-2">
              {(result?.explain?.global || []).length ? (
                result?.explain?.global?.map((g: any, i) => (
                  <Badge key={i} variant="outline">
                    {g.feature || Object.keys(g)[0]}
                  </Badge>
                ))
              ) : (
                <Badge variant="outline">No global importances</Badge>
              )}
            </div>
          </div>
        </TabsContent>

        {/* ================= METRICS ================= */}
        <TabsContent value="metrics" className="tab-content">
          <div className="glass-card p-6">
            <h3 className="section-title">Model Performance</h3>

            {!result ? (
              <p className="text-sm text-muted-foreground mt-2">Run a forecast to see run metrics.</p>
            ) : (
              <>
                <div className="grid grid-cols-2 lg:grid-cols-4 gap-4 mt-4">
                  {[
                    { label: "MAPE", value: result?.metrics?.mape ?? "—" },
                    { label: "RMSE", value: result?.metrics?.rmse ?? "—" },
                    { label: "Coverage (95%)", value: result?.metrics?.coverage_95 ?? "—" },
                    { label: "Bias", value: result?.metrics?.bias_pct ?? "—" },
                  ].map(m => (
                    <div key={m.label} className="bg-muted/50 rounded-xl p-4 text-center">
                      <p className="text-xs text-muted-foreground mb-1">
                        {m.label}
                      </p>
                      <p className="text-xl font-bold">{typeof m.value === "number" ? m.value.toFixed(2) : m.value}</p>
                    </div>
                  ))}
                </div>
                {lastRunAt && (
                  <p className="text-xs text-muted-foreground mt-2">Last updated: {lastRunAt}</p>
                )}
              </>
            )}

            {modelMetrics?.metrics?.length ? (
              <div className="mt-4 text-xs text-muted-foreground">
                <p className="font-semibold mb-1">Model Metrics</p>
                {modelMetrics.metrics.map((m, i) => (
                  <div key={i}>{m.label}: {m.value}</div>
                ))}
              </div>
            ) : (
              <p className="text-xs text-muted-foreground mt-4">Model-level metrics unavailable.</p>
            )}
          </div>
        </TabsContent>

        {/* ================= API ================= */}
        <TabsContent value="api" className="tab-content">
          <div className="glass-card p-6 space-y-4">
            <h3 className="section-title">API Reference</h3>

            <pre className="text-xs bg-muted/50 p-4 rounded-xl">
{`POST /api/v1/forecast/predict
{
  "product_id": "SKU001",
  "aps": "APS-North",
  "horizon_months": 6,
  "scenarios": {
    "temperature_pct": 5,
    "housing_growth_pct": -2
  }
}`}
            </pre>

            <div className="flex gap-3">
              <Button asChild>
                <a href="http://localhost:8001/docs" target="_blank">
                  Open Swagger
                </a>
              </Button>
              <Button asChild variant="outline">
                <a href="http://localhost:8001/redoc" target="_blank">
                  Open ReDoc
                </a>
              </Button>
            </div>
          </div>
        </TabsContent>
      </Tabs>
    </div>
  );
}
