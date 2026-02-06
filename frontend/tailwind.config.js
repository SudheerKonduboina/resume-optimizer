/** @type {import('tailwindcss').Config} */
module.exports = {
  content: ["./app/**/*.{ts,tsx}"],
  theme: {
    extend: {
      colors: {
        bg: "rgb(var(--bg))",
        card: "rgb(var(--card))",
        border: "rgb(var(--border))",
        text: "rgb(var(--text))",
        muted: "rgb(var(--muted))",
        gold: "rgb(var(--gold))",
        emerald: "rgb(var(--emerald))"
      }
    }
  },
  plugins: []
};
