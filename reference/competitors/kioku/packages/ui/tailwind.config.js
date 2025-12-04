/** @type {import('tailwindcss').Config} */
export default {
  content: [
    "./index.html",
    "./src/**/*.{js,ts,jsx,tsx}",
  ],
  theme: {
    extend: {
      colors: {
        // Kioku brand colors (matching main project aesthetic)
        'kioku-primary': '#6366f1',    // Indigo-500
        'kioku-secondary': '#8b5cf6',  // Violet-500
        'kioku-success': '#10b981',    // Emerald-500
        'kioku-warning': '#f59e0b',    // Amber-500
        'kioku-danger': '#ef4444',     // Red-500
        'kioku-info': '#3b82f6',       // Blue-500
        'kioku-dark': '#1f2937',       // Gray-800
        'kioku-light': '#f9fafb',      // Gray-50
      },
      animation: {
        'pulse-slow': 'pulse 3s cubic-bezier(0.4, 0, 0.6, 1) infinite',
        'spin-slow': 'spin 3s linear infinite',
      },
      boxShadow: {
        'glass': '0 8px 32px 0 rgba(31, 38, 135, 0.37)',
      },
      backdropBlur: {
        'xs': '2px',
      },
    },
  },
  plugins: [],
}
