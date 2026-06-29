/** @type {import('tailwindcss').Config} */
module.exports = {
  content: ['./src/**/*.{js,ts,jsx,tsx}'],
  theme: {
    extend: {
      fontFamily: {
        sans: ['var(--font-noto)', 'Malgun Gothic', 'system-ui', 'sans-serif'],
      },
      colors: {
        /* 농사로, 농촌진흥청 포털 톤 */
        rda: {
          50: '#eef7f1',
          100: '#d5ebdc',
          200: '#a8d4b8',
          300: '#6fb88a',
          400: '#3d9a62',
          500: '#1a7d45',
          600: '#007a3d',
          700: '#006332',
          800: '#004d28',
          900: '#003a1f',
        },
        portal: {
          bg: '#f4f5f7',
          line: '#d9dde3',
          lineLight: '#e8ebef',
          text: '#222222',
          sub: '#555555',
          muted: '#888888',
          link: '#0066b3',
          gov: '#2c3e50',
        },
        surface: {
          DEFAULT: '#ffffff',
          muted: '#f8f9fa',
          subtle: '#eef0f3',
        },
        ink: {
          DEFAULT: '#222222',
          secondary: '#555555',
          muted: '#888888',
        },
        border: {
          DEFAULT: '#d9dde3',
          light: '#e8ebef',
        },
      },
      boxShadow: {
        card: '0 1px 3px rgba(0, 0, 0, 0.06)',
        portal: '0 2px 8px rgba(0, 0, 0, 0.08)',
      },
      borderRadius: {
        portal: '6px',
        '2xl': '8px',
        '3xl': '10px',
      },
      maxWidth: {
        portal: '1200px',
      },
    },
  },
  plugins: [],
};
