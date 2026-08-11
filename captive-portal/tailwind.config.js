/** @type {import('tailwindcss').Config} */
export default {
  content: ['./index.html', './src/**/*.{js,ts,jsx,tsx}'],
  theme: {
    extend: {
      colors: {
        telix: {
          DEFAULT: '#0f4c81',
          dark: '#0a3660',
          light: '#e8f1fa',
        },
      },
    },
  },
  plugins: [],
};
