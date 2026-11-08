"use client";

import { getHealth } from "@/lib/api";
import { useEffect, useState } from "react";

type ApiHealthStatus = "checking" | "available" | "unavailable";

const statusLabels: Record<ApiHealthStatus, string> = {
  checking: "Sprawdzam API…",
  available: "API dostępne",
  unavailable: "API niedostępne",
};

export default function ApiHealth() {
  const [currentStatus, setCurrentStatus] = useState<ApiHealthStatus>("checking");

  const checkStatus = async (): Promise<ApiHealthStatus> => {
    try {
      await getHealth();
      return "available";
    } catch {
      return "unavailable";
    }
  };

  useEffect(() => {
    checkStatus().then((status) => setCurrentStatus(status));
  }, []);

  return (
    <span
      className={`model-status api-health api-health--${currentStatus}`}
      role="status"
      aria-live="polite"
    >
      {statusLabels[currentStatus]}
    </span>
  );
}
