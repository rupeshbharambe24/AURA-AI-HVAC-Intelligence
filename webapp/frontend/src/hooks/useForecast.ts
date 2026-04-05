import { useMutation, useQuery } from "@tanstack/react-query";
import { ApiError, apiGet, apiPost, isMockMode } from "@/lib/api-client";
import { useApiErrorToast } from "@/hooks/use-api-error";
import {
  ForecastModelMetricsResponse,
  ForecastOptionsResponse,
  ForecastRequest,
  ForecastResponse,
} from "@/api/types/forecast";
import { mockForecastData, mockProducts } from "@/lib/mock-data";

const mockOptions: ForecastOptionsResponse = {
  request_id: "mock",
  products: mockProducts,
  aps_list: ["APS-North", "APS-South", "APS-East", "APS-West"],
  max_horizon_months: 12,
};

const buildMockForecast = (req: ForecastRequest): ForecastResponse => {
  const horizon = req.horizon_months || 6;
  const forecast = mockForecastData.slice(0, horizon).map(row => ({
    date: row.date,
    actual: row.actual ?? null,
    predicted: row.predicted,
    lower: row.lower ?? null,
    upper: row.upper ?? null,
    drivers: ["Seasonality"],
  }));
  return {
    request_id: "mock",
    model_id: "forecast_v3",
    product_id: req.product_id,
    aps: req.aps,
    cutoff_date: new Date().toISOString().slice(0, 10),
    forecast,
    metrics: { mape: 4.2, rmse: 12.3, coverage_95: 94.2, bias_pct: 0.3 },
    explain: {
      local: [{ seasonality: 0.4, promo: 0.2 }],
      global: [{ lag_demand: 0.5 }, { seasonality: 0.3 }],
    },
    applied_scenarios: {},
    warnings: [],
  };
};

export const useForecastOptions = () => {
  const onError = useApiErrorToast();
  const mock = isMockMode();
  return useQuery({
    queryKey: ["forecastOptions", mock],
    queryFn: async () => {
      if (mock) return mockOptions;
      return apiGet<ForecastOptionsResponse>("/forecast/options");
    },
    staleTime: 60_000,
    retry: 1,
    onError,
  });
};

export const useForecastPredict = () => {
  const onError = useApiErrorToast();
  const mock = isMockMode();
  return useMutation({
    mutationFn: async (req: ForecastRequest) => {
      if (mock) return buildMockForecast(req);
      return apiPost<ForecastResponse>("/forecast/predict", req);
    },
    onError,
  });
};

export const useForecastMetrics = () => {
  const onError = useApiErrorToast();
  const mock = isMockMode();
  return useQuery({
    queryKey: ["forecastMetrics", mock],
    queryFn: async () => {
      if (mock) {
        return { request_id: "mock", metrics: [{ label: "MAPE", value: "4.2%" }] } as ForecastModelMetricsResponse;
      }
      try {
        return await apiGet<ForecastModelMetricsResponse>("/forecast/metrics");
      } catch (err) {
        if (err instanceof ApiError && err.status === 404) {
          return null as unknown as ForecastModelMetricsResponse;
        }
        throw err;
      }
    },
    staleTime: 60_000,
    retry: 1,
    onError,
  });
};
