export interface BaseResponse {
  request_id: string;
}

export interface ErrorResponse {
  error: string;
  message: string;
  request_id: string;
  details?: unknown;
}
