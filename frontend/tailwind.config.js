/** @type {import('tailwindcss').Config} */
export default {
  content: ["./index.html", "./src/**/*.{js,ts,jsx,tsx}"],
  theme: {
    extend: {
      colors: {
        ink: {
          DEFAULT: "#0A0D13",
          panel: "#12161F",
          hover: "#171C27",
          border: "#232A38",
          borderLight: "#2C3444",
        },
        text: {
          primary: "#E7EAEE",
          muted: "#8A93A6",
          faint: "#5B6478",
        },
        signal: {
          teal: "#4FD1C5",
          amber: "#F2B84B",
          coral: "#F2665B",
          indigo: "#7C8CF8",
        },
      },
      fontFamily: {
        display: ["'Space Grotesk'", "sans-serif"],
        body: ["'Inter'", "sans-serif"],
        mono: ["'JetBrains Mono'", "monospace"],
      },
      boxShadow: {
        panel: "0 1px 0 0 rgba(255,255,255,0.03) inset, 0 8px 24px -12px rgba(0,0,0,0.5)",
      },
    },
  },
  plugins: [],
};
