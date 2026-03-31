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
        sidebar: "#eef1f5",
        panel: "#ffffff",
        surface: "#f8fafc",
        line: {
          DEFAULT: "#d7dde7",
          strong: "#c3ccd8"
        },
        ink: "#152033",
        muted: "#5f6c82",
        subtle: "#7f8a9c",
        accent: {
          DEFAULT: "#365a82",
          strong: "#27486d",
          soft: "#e8eef5"
        },
        success: {
          DEFAULT: "#0f766e",
          soft: "#e7f8f4"
        },
        warning: {
          DEFAULT: "#a16207",
          soft: "#fff5df"
        },
        danger: {
          DEFAULT: "#b42318",
          soft: "#fcebea"
        }
      },
      borderRadius: {
        xl: "1rem",
        "2xl": "1.25rem",
        "3xl": "1.5rem"
      },
      boxShadow: {
        panel: "0 1px 2px rgba(15, 23, 42, 0.04), 0 12px 24px rgba(15, 23, 42, 0.06)"
      },
      fontFamily: {
        sans: ["Aptos", "Segoe UI", "PingFang SC", "Hiragino Sans GB", "Microsoft YaHei", "sans-serif"]
      }
    }
  },
  plugins: []
};
