/** @type {import('tailwindcss').Config} */
module.exports = {
  content: ["./src/**/*.{js,jsx,ts,tsx}"],
  theme: {
    extend: {
      colors: {
        dark: {
          canvas: "var(--bg-canvas)",
          sidebar: "var(--bg-sidebar)",
          card: "var(--bg-card)",
          "card-hover": "var(--bg-card-hover)",
          inset: "var(--bg-inset)",
          subtle: "var(--bg-subtle)",
          border: "var(--border-default)",
          "border-subtle": "var(--border-subtle)",
          "text-primary": "var(--text-primary)",
          "text-secondary": "var(--text-secondary)",
          "text-muted": "var(--text-muted)",
        },
      },
    },
  },
  plugins: [],
};
