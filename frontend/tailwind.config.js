/** @type {import('tailwindcss').Config} */
module.exports = {
  content: ["./src/**/*.{js,jsx,ts,tsx}"],
  theme: {
    extend: {
      colors: {
        "arxiv-blue": "#2563eb",
        "arxiv-dark": "#1e293b",
        "arxiv-gray": "#334155",
        "arxiv-light": "#f1f5f9", // add this for light text
      },
    },
  },
  plugins: [],
};
