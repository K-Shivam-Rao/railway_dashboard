"use client";

import { useEffect, useState, useRef } from "react";

export function useCountUp(end: number, duration = 1500, delay = 0) {
  const [value, setValue] = useState(0);
  const frameRef = useRef<number>(0);

  const decimals = Number.isInteger(end) ? 0 : String(end).split(".")[1]?.length || 0;

  useEffect(() => {
    const timeout = setTimeout(() => {
      const startTime = performance.now();
      const startValue = 0;

      function tick(now: number) {
        const elapsed = now - startTime;
        const progress = Math.min(elapsed / duration, 1);
        const eased = 1 - Math.pow(1 - progress, 3);
        const raw = startValue + (end - startValue) * eased;
        setValue(decimals > 0 ? parseFloat(raw.toFixed(decimals)) : Math.round(raw));

        if (progress < 1) {
          frameRef.current = requestAnimationFrame(tick);
        }
      }

      frameRef.current = requestAnimationFrame(tick);
    }, delay);

    return () => {
      clearTimeout(timeout);
      cancelAnimationFrame(frameRef.current);
    };
  }, [end, duration, delay]);

  return value;
}