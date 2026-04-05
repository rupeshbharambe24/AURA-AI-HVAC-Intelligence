import { toast } from "@/hooks/use-toast";
import { ApiError } from "@/lib/api-client";

export const useApiErrorToast = () => {
  return (error: unknown) => {
    let message = "Request failed";
    let requestId: string | undefined;

    if (error instanceof ApiError) {
      message = error.message || message;
      requestId = error.requestId;
    } else if (error instanceof Error) {
      message = error.message || message;
    }

    toast({
      title: "API Error",
      description: requestId ? `${message} (request_id: ${requestId})` : message,
      variant: "destructive",
    });
  };
};
