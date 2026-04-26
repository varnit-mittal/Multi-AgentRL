import { motion, useScroll, useTransform } from "framer-motion";

const NAV = [
  { id: "problem", label: "The problem" },
  { id: "roles", label: "Roles" },
  { id: "live", label: "Live episode" },
  { id: "rubric", label: "Rubric" },
  { id: "tasks", label: "Tasks" },
  { id: "results", label: "Results" },
];

export function Nav() {
  const { scrollYProgress } = useScroll();
  const opacity = useTransform(scrollYProgress, [0, 0.04], [0, 1]);
  return (
    <motion.nav
      style={{ opacity }}
      className="pointer-events-auto fixed left-1/2 top-5 z-50 -translate-x-1/2"
    >
      <div className="flex items-center gap-1 rounded-full border border-white/10 bg-black/60 px-2 py-1.5 backdrop-blur-xl">
        <a
          href="#top"
          className="rounded-full px-3 py-1.5 mono text-[11px] font-semibold uppercase tracking-[0.22em] text-white"
        >
          ◇ Whispers
        </a>
        <div className="hidden items-center gap-0.5 md:flex">
          {NAV.map((n) => (
            <a
              key={n.id}
              href={`#${n.id}`}
              className="whitespace-nowrap rounded-full px-3 py-1.5 text-xs font-medium text-white/55 transition hover:bg-white/[0.06] hover:text-white"
            >
              {n.label}
            </a>
          ))}
        </div>
      </div>
    </motion.nav>
  );
}
