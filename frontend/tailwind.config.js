/** @type {import('tailwindcss').Config} */
export default {
  content: [
    "./index.html",
    "./src/**/*.{js,ts,jsx,tsx}",
  ],
  darkMode: 'class',
  theme: {
    extend: {
      colors: {
        background: '#0F172A',
        card: '#111827',
        secondaryCard: '#1F2937',
        primary: '#2563EB',
        secondary: '#7C3AED',
        accent: '#06B6D4',
        success: '#22C55E',
        warning: '#F59E0B',
        danger: '#EF4444',
        primaryText: '#F8FAFC',
        secondaryText: '#94A3B8',
        mutedText: '#64748B',
        border: '#1F2937'
      }
    },
  },
  plugins: [],
}
