/** @type {import('tailwindcss').Config} */
export default {
  content: ['./index.html', './src/**/*.{ts,tsx}'],
  theme: {
    extend: {
      colors: {
        ink: '#172033',
        muted: '#667085',
        line: '#dde3ec',
        panel: '#ffffff',
        app: '#f4f7fb',
        brand: '#2563eb',
        mint: '#0f9f8f',
        coral: '#e05d44',
        amber: '#d89418',
      },
      boxShadow: {
        soft: '0 14px 40px rgba(23, 32, 51, 0.08)',
      },
    },
  },
  plugins: [],
};
