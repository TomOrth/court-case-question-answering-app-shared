/** @type {import('tailwindcss').Config} */
export default {
  content: [
    "./index.html",
    "./src/**/*.{js,ts,jsx,tsx}",
  ],
  theme: {
    extend: {
      colors: {
        primary: '#2563eb',  // Blue for primary actions
        secondary: '#64748b',  // Gray for secondary elements
      },
    },
  },
  plugins: [],
}

