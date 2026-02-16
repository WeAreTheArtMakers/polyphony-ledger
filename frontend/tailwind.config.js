/** @type {import('tailwindcss').Config} */
module.exports = {
  content: [
    './src/app/**/*.{js,ts,jsx,tsx,mdx}',
    './src/components/**/*.{js,ts,jsx,tsx,mdx}',
    './src/lib/**/*.{js,ts,jsx,tsx,mdx}'
  ],
  theme: {
    extend: {
      colors: {
        ink: '#0d1b2a',
        sea: '#1b263b',
        mint: '#2a9d8f',
        amber: '#f4a261',
        coral: '#e76f51'
      },
      backgroundImage: {
        grid: 'linear-gradient(to right, rgba(13,27,42,0.06) 1px, transparent 1px), linear-gradient(to bottom, rgba(13,27,42,0.06) 1px, transparent 1px)'
      }
    }
  },
  plugins: []
};
