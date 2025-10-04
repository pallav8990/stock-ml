/** @type {import('tailwindcss').Config} */
module.exports = {
  content: [
    "./src/**/*.{js,jsx,ts,tsx}",
  ],
  theme: {
    extend: {
      colors: {
        'stock-green': '#10B981',
        'stock-red': '#EF4444',
        'primary': '#1F2937',
        'secondary': '#374151',
      },
    },
  },
}