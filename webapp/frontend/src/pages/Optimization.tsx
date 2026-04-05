import { useEffect, useMemo, useState } from "react";
import { motion } from "framer-motion";
import {
  Target,
  Play,
  Loader2,
  Calendar,
  BarChart3,
  AlertTriangle,
} from "lucide-react";
import { PageHeader } from "@/components/common/PageHeader";
import { Tabs, TabsList, TabsTrigger, TabsContent } from "@/components/ui/tabs";
import { Slider } from "@/components/ui/slider";
import { Button } from "@/components/ui/button";
import { Badge } from "@/components/ui/badge";
import { Switch } from "@/components/ui/switch";
import { StatCard } from "@/components/common/StatCard";
import {
  BarChart,
  Bar,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  ResponsiveContainer,
} from "recharts";
import { useJobStatus, useOptimizeSubmit } from "@/hooks/useOptimize";
import type { OptimizeResult } from "@/api/types/optimize";

export default function Optimization() {
  const optimizeMutation = useOptimizeSubmit();

  const [maxPromos, setMaxPromos] = useState([12]);
  const [excludeQ1, setExcludeQ1] = useState(true);
  const [capacityLimit, setCapacityLimit] = useState([90]);
  const [discount, setDiscount] = useState([20]);
  const [durationWeeks, setDurationWeeks] = useState([3]);

  const [jobId, setJobId] = useState<string | null>(null);
  const [result, setResult] = useState<OptimizeResult | null>(null);

  const jobStatus = useJobStatus(jobId ?? undefined, !!jobId);

  useEffect(() => {
    if (jobStatus.data?.status === "completed" && jobStatus.data.result) {
      setResult(jobStatus.data.result as OptimizeResult);
    }
  }, [jobStatus.data]);

  const runOptimization = () => {
    optimizeMutation.mutate(
      {
        constraints: {
          max_promos_per_year: maxPromos[0],
          exclude_months: excludeQ1 ? [1, 2, 3] : [],
          capacity_limit_pct: capacityLimit[0],
          target_year: new Date().getFullYear(),
        },
        candidate_promos: [
          { type: "discount", discount_pct: discount[0] / 100, duration_weeks: durationWeeks[0] },
        ],
        products: [],
      },
      {
        onSuccess: (data) => {
          setJobId(data.job_id);
        },
      }
    );
  };

  const running = optimizeMutation.isPending || (jobStatus.data && jobStatus.data.status === "running");
  const progress = jobStatus.data?.progress ? Math.round(jobStatus.data.progress * 100) : 0;

  const promoCalendar = useMemo(() => {
    return (result?.promo_calendar || []).map(p => ({
      month: p.month,
      promos: p.promos,
      budget: p.budget,
      expected_lift_pct: p.expected_lift_pct,
    }));
  }, [result]);

  return (
    <div className="page-container">
      <PageHeader
        icon={Target}
        title="Promotion Optimization"
        description="Async profit optimization under real-world constraints"
      />

      <Tabs defaultValue="playground">
        <TabsList className="bg-card border border-border">
          <TabsTrigger value="playground">Playground</TabsTrigger>
          <TabsTrigger value="explain">Explain</TabsTrigger>
          <TabsTrigger value="api">API</TabsTrigger>
        </TabsList>

        {/* ================= PLAYGROUND ================= */}
        <TabsContent value="playground" className="tab-content">
          <div className="grid grid-cols-1 lg:grid-cols-4 gap-6">

            {/* ================= LEFT: CONTROLS ================= */}
            <div className="glass-card p-5 space-y-6">
              <h3 className="text-sm font-semibold">Constraints</h3>

              <div>
                <div className="flex items-center justify-between">
                  <label className="text-xs text-muted-foreground">
                    Max Promos / Year
                  </label>
                  <span className="text-xs font-mono text-muted-foreground">{maxPromos[0]}</span>
                </div>
                <Slider value={maxPromos} onValueChange={setMaxPromos} min={4} max={24} step={1} />
              </div>

              <div>
                <label className="text-xs text-muted-foreground">
                  Exclude Q1
                </label>
                <Switch checked={excludeQ1} onCheckedChange={setExcludeQ1} />
              </div>

              <div>
                <div className="flex items-center justify-between">
                  <label className="text-xs text-muted-foreground">
                    Capacity Limit (%)
                  </label>
                  <span className="text-xs font-mono text-muted-foreground">{capacityLimit[0]}%</span>
                </div>
                <Slider value={capacityLimit} onValueChange={setCapacityLimit} min={60} max={100} step={5} />
              </div>

              <hr className="border-border" />

              <h3 className="text-sm font-semibold">Candidate Promo Designer</h3>

              <div>
                <label className="text-xs text-muted-foreground">Promo Type</label>
                <Badge variant="outline">Discount</Badge>
              </div>

              <div>
                <div className="flex items-center justify-between">
                  <label className="text-xs text-muted-foreground">
                    Discount (%)
                  </label>
                  <span className="text-xs font-mono text-muted-foreground">{discount[0]}%</span>
                </div>
                <Slider value={discount} onValueChange={setDiscount} min={5} max={50} step={5} />
              </div>

              <div>
                <div className="flex items-center justify-between">
                  <label className="text-xs text-muted-foreground">
                    Duration (weeks)
                  </label>
                  <span className="text-xs font-mono text-muted-foreground">{durationWeeks[0]}</span>
                </div>
                <Slider value={durationWeeks} onValueChange={setDurationWeeks} min={1} max={8} step={1} />
              </div>

              <Button className="w-full gap-2" onClick={runOptimization} disabled={running}>
                {running ? (
                  <>
                    <Loader2 className="w-4 h-4 animate-spin" />
                    Optimizing…
                  </>
                ) : (
                  <>
                    <Play className="w-4 h-4" />
                    Run Optimization
                  </>
                )}
              </Button>

              {jobId && (
                <p className="text-xs text-muted-foreground text-center">
                  Job ID: <span className="font-mono">{jobId}</span>
                </p>
              )}

              {running && (
                <div className="space-y-2">
                  <div className="h-1.5 rounded-full bg-muted overflow-hidden">
                    <motion.div
                      animate={{ width: `${progress}%` }}
                      className="h-full bg-primary"
                    />
                  </div>
                  <p className="text-xs text-center text-muted-foreground">
                    Optimization in progress ({progress}%)
                  </p>
                </div>
              )}
            </div>

            {/* ================= RIGHT: RESULTS ================= */}
            <div className="lg:col-span-3 space-y-4">
              {result ? (
                <>
                  <div className="grid grid-cols-2 lg:grid-cols-4 gap-4">
                    <StatCard
                      icon={Target}
                      label="Total Profit"
                      value={`$${(result.summary.optimized_profit_mean / 1e6).toFixed(2)}M`}
                      change={`+${result.summary.profit_improvement_pct.toFixed(2)}%`}
                      trend="up"
                    />
                    <StatCard
                      icon={BarChart3}
                      label="Capacity Used"
                      value={`${result.summary.capacity_utilization_pct.toFixed(1)}%`}
                      trend="neutral"
                    />
                    <StatCard
                      icon={AlertTriangle}
                      label="Lost Sales"
                      value={`${result.summary.lost_sales_pct.toFixed(1)}%`}
                      trend="down"
                    />
                    <StatCard
                      icon={Calendar}
                      label="Promos Planned"
                      value={promoCalendar.reduce((s, p) => s + p.promos, 0)}
                    />
                  </div>

                  <div className="glass-card p-5">
                    <h3 className="section-title mb-4">Optimized Promo Schedule</h3>
                    <div className="h-64">
                      <ResponsiveContainer width="100%" height="100%">
                        <BarChart data={promoCalendar}>
                          <CartesianGrid strokeDasharray="3 3" />
                          <XAxis dataKey="month" />
                          <YAxis />
                          <Tooltip />
                          <Bar dataKey="budget" fill="hsl(199 89% 48%)" radius={[6, 6, 0, 0]} />
                          <Bar dataKey="expected_lift_pct" fill="hsl(160 84% 39%)" radius={[6, 6, 0, 0]} />
                        </BarChart>
                      </ResponsiveContainer>
                    </div>
                  </div>

                  <div className="glass-card p-5">
                    <h3 className="section-title mb-2">Constraint Report</h3>
                    <p className="text-sm text-muted-foreground">
                      Violations: <strong>{result.summary.violations}</strong>
                    </p>
                    <ul className="text-xs text-muted-foreground list-disc list-inside mt-2">
                      {result.constraint_report.details.length ? result.constraint_report.details.map((d, i) => (
                        <li key={i}>{d}</li>
                      )) : <li>No constraint violations</li>}
                    </ul>
                  </div>
                </>
              ) : (
                <div className="glass-card p-6">
                  <h3 className="section-title">Optimization Summary</h3>
                  <p className="text-sm text-muted-foreground mt-2">Run an optimization to see metrics and schedule.</p>
                </div>
              )}
            </div>
          </div>
        </TabsContent>

        {/* ================= EXPLAIN ================= */}
        <TabsContent value="explain" className="tab-content">
          <div className="glass-card p-6 space-y-6">
            <h3 className="section-title">Why These Promos?</h3>

            <div className="space-y-3">
              <p className="text-sm">• Highest marginal profit per unit discount</p>
              <p className="text-sm">• Capacity constraint binding in Q3</p>
              <p className="text-sm">• Q1 excluded due to low elasticity</p>
            </div>

            <div>
              <h4 className="text-sm font-semibold mb-2">Sensitivity Scenarios</h4>
              <div className="flex gap-2">
                <Badge variant="outline">Best</Badge>
                <Badge variant="outline">Median</Badge>
                <Badge variant="outline">Worst</Badge>
              </div>
            </div>
          </div>
        </TabsContent>

        {/* ================= API ================= */}
        <TabsContent value="api" className="tab-content">
          <div className="glass-card p-6 space-y-4">
            <h3 className="section-title">Async Optimization API</h3>

            <pre className="text-xs bg-muted/50 p-4 rounded-xl">
{`POST /api/v1/optimize/submit
{
  "constraints": {
    "max_promos_per_year": 12,
    "exclude_months": [1,2,3],
    "capacity_limit_pct": 0.9
  },
  "candidate_promos": [
    { "type": "discount", "discount_pct": 0.2, "duration_weeks": 3 }
  ]
}

→ returns { "job_id": "job_123" }

GET /api/v1/jobs/{job_id}`}
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
