/** @type {import('tailwindcss').Config} */
module.exports = {
  content: [
    "./app/**/*.{js,ts,jsx,tsx,mdx}",
    "./components/**/*.{js,ts,jsx,tsx,mdx}",
    "./lib/**/*.{js,ts,jsx,tsx,mdx}",
    "./types/**/*.{js,ts,jsx,tsx,mdx}"
  ],
  theme: {
    extend: {
      colors: {
        canvas: "#f3f5f8",
        sidebar: "#eef2f6",
        panel: "#ffffff",
        surface: "#f7f9fc",
        inset: "#f1f4f8",
        line: {
          DEFAULT: "#d9e1ea",
          strong: "#bfcadb"
        },
        ink: "#17202d",
        muted: "#526173",
        subtle: "#738296",
        accent: {
          DEFAULT: "#355f91",
          strong: "#284d78",
          soft: "#edf4fb"
        },
        success: {
          DEFAULT: "#16745f",
          soft: "#edf8f3"
        },
        warning: {
          DEFAULT: "#9c5f12",
          soft: "#fff6e8"
        },
        danger: {
          DEFAULT: "#b42318",
          soft: "#fcedec"
        }
      },
      borderRadius: {
        xl: "0.375rem",
        "2xl": "0.5rem",
        "3xl": "0.5rem"
      },
      boxShadow: {
        panel: "0 1px 2px rgba(15, 23, 42, 0.03), 0 10px 24px rgba(15, 23, 42, 0.03)",
        float: "0 18px 40px rgba(15, 23, 42, 0.10), 0 4px 12px rgba(15, 23, 42, 0.06)",
        inset: "inset 0 1px 0 rgba(255, 255, 255, 0.8)"
      },
      fontFamily: {
        sans: ["Aptos", "Segoe UI", "PingFang SC", "Hiragino Sans GB", "Microsoft YaHei", "sans-serif"]
      }
    }
  },
  plugins: []
};
