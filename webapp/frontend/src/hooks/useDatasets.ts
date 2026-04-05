import { useQuery } from "@tanstack/react-query";
import { apiGet, ApiError, isMockMode } from "@/lib/api-client";
import { useApiErrorToast } from "@/hooks/use-api-error";
import { DatasetsResponse } from "@/api/types/datasets";
import { mockDatasets } from "@/lib/mock-data";
import { useState } from "react";

const buildMockSeries = () =>
  Array.from({ length: 30 }, (_, i) => ({
    date: `2025-01-${String(i + 1).padStart(2, "0")}`,
    value: 1000 + Math.sin(i / 3) * 200 + Math.random() * 100,
  }));

export const useDatasets = () => {
  const onError = useApiErrorToast();
  const mock = isMockMode();
  const [apiUnavailable, setApiUnavailable] = useState(false);

  const query = useQuery({
    queryKey: ["datasets", mock],
    queryFn: async () => {
      if (mock) {
        return { request_id: "mock", datasets: mockDatasets } as unknown as DatasetsResponse;
      }
      try {
        return await apiGet<DatasetsResponse>("/models/datasets");
      } catch (err) {
        if (err instanceof ApiError && err.status === 404) {
          setApiUnavailable(true);
          return { request_id: "missing", datasets: mockDatasets, warnings: ["Dataset API not available"] } as unknown as DatasetsResponse;
        }
        throw err;
      }
    },
    staleTime: 60_000,
    retry: 1,
    onError,
  });

  return { ...query, apiUnavailable };
};

export const useDatasetTimeseries = (name?: string) => {
  const onError = useApiErrorToast();
  const mock = isMockMode();
  const [apiUnavailable, setApiUnavailable] = useState(false);

  const query = useQuery({
    queryKey: ["datasetTimeseries", name, mock],
    enabled: !!name,
    queryFn: async () => {
      if (mock) {
        return { name: name || "mock", series: buildMockSeries(), request_id: "mock" };
      }
      try {
        return await apiGet<any>(`/models/datasets/${name}/timeseries`);
      } catch (err) {
        if (err instanceof ApiError && err.status === 404) {
          setApiUnavailable(true);
          return { name: name || "unknown", series: buildMockSeries(), request_id: "missing" };
        }
        throw err;
      }
    },
    retry: 1,
    onError,
  });

  return { ...query, apiUnavailable };
};
