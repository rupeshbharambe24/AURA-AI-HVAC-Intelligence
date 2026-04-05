export const mockModels = [
  { id: "forecast_v3", name: "Demand Forecast", version: "v3", alias: "prod", trainingPeriod: "2023-01 to 2024-12", datasetHash: "a3f8c2", owner: "ML Team", keyMetric: "MAPE: 4.2%", status: "active" },
  { id: "forecast_v2", name: "Demand Forecast", version: "v2", alias: "staging", trainingPeriod: "2023-01 to 2024-06", datasetHash: "b7d1e5", owner: "ML Team", keyMetric: "MAPE: 5.1%", status: "active" },
  { id: "anomaly_v2", name: "Anomaly Detector", version: "v2", alias: "prod", trainingPeriod: "2023-06 to 2024-12", datasetHash: "c9e4a1", owner: "Data Science", keyMetric: "F1: 0.94", status: "active" },
  { id: "promo_optimizer_v1", name: "Promo Optimizer", version: "v1", alias: "prod", trainingPeriod: "2023-01 to 2024-12", datasetHash: "d2f7b3", owner: "Optimization", keyMetric: "ROI: +18%", status: "active" },
  { id: "market_share_v1", name: "Market Share", version: "v1", alias: "dev", trainingPeriod: "2024-01 to 2024-12", datasetHash: "e5a8c4", owner: "Strategy", keyMetric: "R²: 0.87", status: "experimental" },
];

export const mockExperiments = [
  { id: "run_001", model: "forecast", name: "LSTM + External Signals", owner: "Alice", date: "2025-01-15", mape: 4.2, rmse: 12.3, status: "completed" },
  { id: "run_002", model: "forecast", name: "XGBoost Baseline", owner: "Bob", date: "2025-01-10", mape: 5.8, rmse: 15.1, status: "completed" },
  { id: "run_003", model: "anomaly", name: "Isolation Forest v2", owner: "Alice", date: "2025-01-12", mape: null, rmse: null, status: "completed", f1: 0.94 },
  { id: "run_004", model: "forecast", name: "Transformer Experiment", owner: "Charlie", date: "2025-01-20", mape: 3.9, rmse: 11.8, status: "running" },
  { id: "run_005", model: "market_share", name: "News-Enhanced Model", owner: "Diana", date: "2025-01-18", mape: null, rmse: null, status: "failed" },
];

export const mockForecastData = Array.from({ length: 24 }, (_, i) => {
  const date = new Date(2024, i, 1);
  const base = 1000 + Math.sin(i / 3) * 200 + i * 15;
  return {
    date: date.toISOString().slice(0, 7),
    actual: i < 12 ? Math.round(base + (Math.random() - 0.5) * 100) : null,
    predicted: Math.round(base + (Math.random() - 0.5) * 50),
    upper: Math.round(base + 120),
    lower: Math.round(base - 120),
  };
});

export const mockAnomalyData = Array.from({ length: 60 }, (_, i) => {
  const date = new Date(2024, 0, i + 1);
  const value = 500 + Math.sin(i / 7) * 100 + (Math.random() - 0.5) * 50;
  const isAnomaly = [12, 23, 45, 52].includes(i);
  return {
    date: date.toISOString().slice(0, 10),
    value: Math.round(value),
    expected: Math.round(500 + Math.sin(i / 7) * 100),
    isAnomaly,
    score: isAnomaly ? 0.85 + Math.random() * 0.15 : Math.random() * 0.3,
  };
});

export const mockMarketShareData = Array.from({ length: 12 }, (_, i) => ({
  month: new Date(2024, i, 1).toISOString().slice(0, 7),
  ourShare: 32 + Math.sin(i / 2) * 3 + i * 0.2,
  competitor1: 28 - Math.sin(i / 2) * 2,
  competitor2: 18 + Math.cos(i / 3) * 2,
  others: 22 - i * 0.1,
}));

export const mockDatasets = [
  { name: "demand", rows: 125430, cols: 24, lastUpdated: "2025-01-20", quality: 97, missingness: 0.3 },
  { name: "external_signals", rows: 89200, cols: 15, lastUpdated: "2025-01-19", quality: 94, missingness: 1.2 },
  { name: "promotions", rows: 34500, cols: 18, lastUpdated: "2025-01-18", quality: 99, missingness: 0.1 },
  { name: "capacity", rows: 12000, cols: 8, lastUpdated: "2025-01-20", quality: 100, missingness: 0 },
  { name: "market_share", rows: 45600, cols: 12, lastUpdated: "2025-01-17", quality: 92, missingness: 2.1 },
  { name: "news", rows: 78900, cols: 6, lastUpdated: "2025-01-20", quality: 88, missingness: 3.5 },
];

export const mockHealthMetrics = {
  apiLatency: 45,
  errorRate: 0.12,
  uptime: 99.97,
  lastDriftCheck: "2025-01-20 14:30",
  driftDetected: false,
  activeJobs: 2,
  modelsInProd: 3,
};

export const mockOptimizationResult = {
  totalProfit: 2450000,
  profitIncrease: 18.3,
  capacityUtilization: 87,
  lostSales: 3.2,
  promoCalendar: Array.from({ length: 6 }, (_, i) => ({
    month: new Date(2025, i, 1).toISOString().slice(0, 7),
    promos: Math.floor(Math.random() * 5) + 2,
    budget: Math.round(50000 + Math.random() * 30000),
    expectedLift: Math.round(8 + Math.random() * 12),
  })),
};

export const mockProducts = [
  "Product A - SKU001", "Product B - SKU002", "Product C - SKU003",
  "Product D - SKU004", "Product E - SKU005",
];

export const mockNewsTimeline = [
  { date: "2025-01-18", headline: "Competitor launches new product line", sentiment: "negative", impact: -2.1 },
  { date: "2025-01-14", headline: "Industry report shows market growth", sentiment: "positive", impact: 1.5 },
  { date: "2025-01-10", headline: "Supply chain disruption in Asia Pacific", sentiment: "negative", impact: -3.2 },
  { date: "2025-01-05", headline: "New regulatory framework announced", sentiment: "neutral", impact: 0.3 },
];
