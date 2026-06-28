import type { Config } from "tailwindcss";

const config: Config = {
  content: ["./src/**/*.{js,ts,jsx,tsx,mdx}"],
  theme: {
    extend: {
      colors: {
        saffron: {
          50: "#fff8ed",
          100: "#ffefd4",
          500: "#f59e0b",
          600: "#d97706",
          700: "#b45309",
          900: "#78350f",
        },
        temple: {
          800: "#1c1917",
          900: "#0c0a09",
        },
      },
    },
  },
  plugins: [],
};

export default config;
