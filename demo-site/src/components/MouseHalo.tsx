import { useEffect, useState } from "react";
import { motion, useMotionValue, useSpring } from "framer-motion";

type Props = {
  className?: string;
  size?: number;
};

// A radial gradient that follows the cursor with a tiny spring lag.
// Lives inside its parent — clamp it to the parent's bounding rect.
export function MouseHalo({ className, size = 520 }: Props) {
  const x = useMotionValue(-9999);
  const y = useMotionValue(-9999);
  const sx = useSpring(x, { stiffness: 200, damping: 30, mass: 0.6 });
  const sy = useSpring(y, { stiffness: 200, damping: 30, mass: 0.6 });
  const [active, setActive] = useState(false);

  useEffect(() => {
    const onMove = (e: PointerEvent) => {
      x.set(e.clientX);
      y.set(e.clientY);
      setActive(true);
    };
    const onLeave = () => setActive(false);
    window.addEventListener("pointermove", onMove, { passive: true });
    window.addEventListener("pointerleave", onLeave);
    return () => {
      window.removeEventListener("pointermove", onMove);
      window.removeEventListener("pointerleave", onLeave);
    };
  }, [x, y]);

  return (
    <motion.div
      aria-hidden
      className={
        "pointer-events-none fixed left-0 top-0 -z-10 rounded-full blur-3xl " +
        (className ?? "")
      }
      style={{
        width: size,
        height: size,
        x: sx,
        y: sy,
        translateX: "-50%",
        translateY: "-50%",
        background:
          "radial-gradient(circle at center, rgba(167,139,250,0.22) 0%, rgba(34,211,238,0.10) 40%, rgba(0,0,0,0) 70%)",
        opacity: active ? 1 : 0,
        transition: "opacity 600ms ease",
        mixBlendMode: "screen",
      }}
    />
  );
}
