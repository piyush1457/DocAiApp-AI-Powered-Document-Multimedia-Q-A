/** @type {import('tailwindcss').Config} */
export default {
  content: [
    "./index.html",
    "./src/**/*.{js,ts,jsx,tsx}",
  ],
  theme: {
    extend: {
      colors: {
        background: '#050505',
        panel: '#0A0A0A',
        border: 'rgba(255, 255, 255, 0.08)',
        accent: '#F59E0B',
        textPrimary: '#F9FAFB',
        textSecondary: '#9CA3AF',
      },
      fontFamily: {
        sans: ['Inter', 'system-ui', 'sans-serif'],
        mono: ['"JetBrains Mono"', 'monospace'],
      },
      backgroundImage: {
        'gradient-amber': 'linear-gradient(to right, #F59E0B, #fbbf24)',
      },
      boxShadow: {
        'amber-glow': '0 0 20px rgba(245, 158, 11, 0.15)',
        'amber-glow-strong': '0 0 30px rgba(245, 158, 11, 0.3)',
      }
    },
  },
  plugins: [],
}
