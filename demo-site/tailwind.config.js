/** @type {import('tailwindcss').Config} */
export default {
  content: ["./index.html", "./src/**/*.{ts,tsx}"],
  theme: {
    extend: {
      colors: {
        ink: {
          950: "#06060a",
          900: "#0a0a12",
          800: "#0f0f1a",
          700: "#15162400",
          border: "#1c1d2e",
        },
        neon: {
          cyan: "#22d3ee",
          violet: "#a78bfa",
          pink: "#f472b6",
          lime: "#a3e635",
          amber: "#fbbf24",
          red: "#fb7185",
        },
      },
      fontFamily: {
        sans: [
          "Inter",
          "ui-sans-serif",
          "system-ui",
          "-apple-system",
          "Segoe UI",
          "sans-serif",
        ],
        mono: [
          "JetBrains Mono",
          "ui-monospace",
          "SFMono-Regular",
          "Menlo",
          "monospace",
        ],
        display: [
          "Inter",
          "ui-sans-serif",
          "system-ui",
          "-apple-system",
          "Segoe UI",
          "sans-serif",
        ],
      },
      boxShadow: {
        glow: "0 0 60px -10px rgba(167,139,250,0.45)",
        "glow-cyan": "0 0 60px -10px rgba(34,211,238,0.45)",
        "glow-pink": "0 0 60px -10px rgba(244,114,182,0.45)",
      },
      backgroundImage: {
        "grid-fade":
          "radial-gradient(circle at center, rgba(255,255,255,0.06) 0, rgba(255,255,255,0) 60%)",
        "noise":
          "url(\"data:image/svg+xml;utf8,<svg xmlns='http://www.w3.org/2000/svg' width='160' height='160'><filter id='n'><feTurbulence type='fractalNoise' baseFrequency='0.9' numOctaves='2' stitchTiles='stitch'/><feColorMatrix values='0 0 0 0 1 0 0 0 0 1 0 0 0 0 1 0 0 0 0.06 0'/></filter><rect width='100%' height='100%' filter='url(%23n)'/></svg>\")",
      },
      animation: {
        "pulse-slow": "pulse 4s cubic-bezier(0.4, 0, 0.6, 1) infinite",
        "spin-slow": "spin 30s linear infinite",
        "float": "float 8s ease-in-out infinite",
        "glow-pulse": "glow-pulse 3s ease-in-out infinite",
        "gradient-x": "gradient-x 8s ease infinite",
      },
      keyframes: {
        float: {
          "0%, 100%": { transform: "translateY(0px)" },
          "50%": { transform: "translateY(-12px)" },
        },
        "glow-pulse": {
          "0%, 100%": { opacity: 0.6 },
          "50%": { opacity: 1 },
        },
        "gradient-x": {
          "0%, 100%": { "background-position": "0% 50%" },
          "50%": { "background-position": "100% 50%" },
        },
      },
    },
  },
  plugins: [],
};
