import { BaseResponse } from "./common";

export interface DatasetEntry {
  name: string;
  rows: number;
  cols: number;
  lastUpdated?: string;
  quality?: number;
  missingness?: number;
}

export interface DatasetsResponse extends BaseResponse {
  datasets: DatasetEntry[];
  warnings?: string[];
}

export interface DatasetRowsResponse extends BaseResponse {
  name: string;
  rows: Record<string, unknown>[];
}

export interface DatasetTimeseriesResponse extends BaseResponse {
  name: string;
  series: { date: string; value: number }[];
}
