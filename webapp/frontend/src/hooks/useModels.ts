import { useQuery } from "@tanstack/react-query";
import { apiGet, isMockMode, ApiError } from "@/lib/api-client";
import { useApiErrorToast } from "@/hooks/use-api-error";
import {
  ModelDetailResponse,
  ModelExplainabilityResponse,
  ModelListResponse,
  ModelMetricsResponse,
  ModelVersionsResponse,
  ExperimentsResponse,
} from "@/api/types/models";
import { mockModels, mockExperiments } from "@/lib/mock-data";

export const useModels = () => {
  const onError = useApiErrorToast();
  const mock = isMockMode();
  return useQuery({
    queryKey: ["models", mock],
    queryFn: async () => {
      if (mock) {
        const models = mockModels.map(m => ({
          id: m.id,
          name: m.name,
          version: m.version,
          alias: m.alias,
          owner: m.owner,
          status: m.status,
          training_period: (m as any).trainingPeriod,
          dataset_hash: (m as any).datasetHash,
          key_metric: (m as any).keyMetric,
          notes: (m as any).notes,
        }));
        return { request_id: "mock", models } as ModelListResponse;
      }
      return apiGet<ModelListResponse>("/models");
    },
    staleTime: 60_000,
    retry: 1,
    onError,
  });
};

export const useModelDetail = (modelId?: string) => {
  const onError = useApiErrorToast();
  const mock = isMockMode();
  return useQuery({
    queryKey: ["modelDetail", modelId, mock],
    enabled: !!modelId,
    queryFn: async () => {
      if (mock) {
        const m = mockModels.find(m => m.id === modelId) || mockModels[0];
        const model = {
          id: m.id,
          name: m.name,
          version: m.version,
          alias: m.alias,
          owner: m.owner,
          status: m.status,
          training_period: (m as any).trainingPeriod,
          dataset_hash: (m as any).datasetHash,
          key_metric: (m as any).keyMetric,
          notes: (m as any).notes,
        };
        return { request_id: "mock", model } as ModelDetailResponse;
      }
      return apiGet<ModelDetailResponse>(`/models/${modelId}`);
    },
    retry: 1,
    onError,
  });
};

export const useModelMetrics = (modelId?: string) => {
  const onError = useApiErrorToast();
  const mock = isMockMode();
  return useQuery({
    queryKey: ["modelMetrics", modelId, mock],
    enabled: !!modelId,
    queryFn: async () => {
      if (mock) {
        return { request_id: "mock", metrics: [] } as ModelMetricsResponse;
      }
      return apiGet<ModelMetricsResponse>(`/models/${modelId}/metrics`);
    },
    retry: 1,
    onError,
  });
};

export const useModelExplainability = (modelId?: string) => {
  const onError = useApiErrorToast();
  const mock = isMockMode();
  return useQuery({
    queryKey: ["modelExplain", modelId, mock],
    enabled: !!modelId,
    queryFn: async () => {
      if (mock) {
        return { request_id: "mock", explainability: [] } as ModelExplainabilityResponse;
      }
      return apiGet<ModelExplainabilityResponse>(`/models/${modelId}/explainability`);
    },
    retry: 1,
    onError,
  });
};

export const useModelVersions = (modelId?: string) => {
  const onError = useApiErrorToast();
  const mock = isMockMode();
  return useQuery({
    queryKey: ["modelVersions", modelId, mock],
    enabled: !!modelId,
    queryFn: async () => {
      if (mock) {
        return { request_id: "mock", versions: [] } as ModelVersionsResponse;
      }
      return apiGet<ModelVersionsResponse>(`/models/${modelId}/versions`);
    },
    retry: 1,
    onError,
  });
};

export const useExperiments = (filter: string) => {
  const onError = useApiErrorToast();
  const mock = isMockMode();
  return useQuery({
    queryKey: ["experiments", filter, mock],
    queryFn: async () => {
      if (mock) {
        return { request_id: "mock", experiments: mockExperiments } as ExperimentsResponse;
      }
      try {
        return await apiGet<ExperimentsResponse>("/models/experiments");
      } catch (err) {
        if (err instanceof ApiError && err.status === 404) {
          return { request_id: "missing", experiments: mockExperiments, warnings: ["Experiments API not available"] } as ExperimentsResponse;
        }
        throw err;
      }
    },
    retry: 1,
    onError,
  });
};
