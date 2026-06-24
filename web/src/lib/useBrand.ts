"use client";

import { useCallback, useState } from "react";

const STORAGE_KEY = "momento_brand_id";

export function useBrand() {
  const [brandId, setBrandIdState] = useState<string | null>(() =>
    typeof window === "undefined" ? null : window.localStorage.getItem(STORAGE_KEY)
  );

  const setBrandId = useCallback((id: string) => {
    window.localStorage.setItem(STORAGE_KEY, id);
    setBrandIdState(id);
  }, []);

  return { brandId, setBrandId };
}
