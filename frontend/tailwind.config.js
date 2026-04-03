/** @type {import('tailwindcss').Config} */
export default {
  content: [
    "./index.html",
    "./src/**/*.{js,ts,jsx,tsx}",
  ],
  theme: {
    extend: {
      colors: {
        primary: {
          DEFAULT: '#0d9488',
          hover: '#0f766e',
          light: '#f0fdf9',
        },
        surface: '#f8fafc',
        border: '#e2e8f0',
        textPrimary: '#0f172a',
        textMuted: '#64748b',
        success: '#22c55e',
        error: '#ef4444',
        warning: '#f59e0b',
      },
      fontFamily: {
        sans: ['DM Sans', 'sans-serif'],
        mono: ['DM Mono', 'monospace'],
      }
    },
  },
  plugins: [],
}
