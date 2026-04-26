import { useEffect, useRef, useState } from "react";
import { useInView } from "framer-motion";

type Props = {
  to: number;
  duration?: number;
  decimals?: number;
  prefix?: string;
  suffix?: string;
  className?: string;
};

// Animated odometer-style number. Counts up once when scrolled into view.
export function CountUp({
  to,
  duration = 1.4,
  decimals = 0,
  prefix = "",
  suffix = "",
  className,
}: Props) {
  const ref = useRef<HTMLSpanElement | null>(null);
  const inView = useInView(ref, { once: true, margin: "0px 0px -10% 0px" });
  const [val, setVal] = useState(0);

  useEffect(() => {
    if (!inView) return;
    let raf = 0;
    const start = performance.now();
    const ease = (t: number) => 1 - Math.pow(1 - t, 3);
    const tick = (now: number) => {
      const t = Math.min(1, (now - start) / (duration * 1000));
      setVal(to * ease(t));
      if (t < 1) raf = requestAnimationFrame(tick);
    };
    raf = requestAnimationFrame(tick);
    return () => cancelAnimationFrame(raf);
  }, [inView, to, duration]);

  return (
    <span ref={ref} className={className}>
      {prefix}
      {val.toFixed(decimals)}
      {suffix}
    </span>
  );
}
