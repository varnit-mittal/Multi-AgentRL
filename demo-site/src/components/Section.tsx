import { motion, useInView } from "framer-motion";
import { useRef, type ReactNode } from "react";
import clsx from "clsx";

type Props = {
  id?: string;
  eyebrow?: string;
  title?: ReactNode;
  subtitle?: ReactNode;
  children: ReactNode;
  className?: string;
  align?: "center" | "left";
};

export function Section({
  id,
  eyebrow,
  title,
  subtitle,
  children,
  className,
  align = "center",
}: Props) {
  const ref = useRef<HTMLDivElement>(null);
  const inView = useInView(ref, { once: true, margin: "-15% 0% -15% 0%" });

  return (
    <section
      id={id}
      ref={ref}
      className={clsx(
        "relative z-10 mx-auto w-full max-w-7xl px-6 py-32 md:px-10",
        className
      )}
    >
      {(eyebrow || title || subtitle) && (
        <motion.div
          initial={{ opacity: 0, y: 24 }}
          animate={inView ? { opacity: 1, y: 0 } : {}}
          transition={{ duration: 0.7, ease: [0.22, 1, 0.36, 1] }}
          className={clsx(
            "mb-14 max-w-3xl",
            align === "center" && "mx-auto text-center"
          )}
        >
          {eyebrow && (
            <div className="pill mb-5">
              <span className="h-1.5 w-1.5 rounded-full bg-violet-400 shadow-[0_0_10px_rgba(167,139,250,0.9)]" />
              {eyebrow}
            </div>
          )}
          {title && (
            <h2 className="font-display text-4xl font-semibold leading-[1.05] tracking-[-0.02em] text-white md:text-6xl">
              {title}
            </h2>
          )}
          {subtitle && (
            <p className="mt-5 text-lg leading-relaxed text-white/55 md:text-xl">
              {subtitle}
            </p>
          )}
        </motion.div>
      )}
      {children}
    </section>
  );
}
