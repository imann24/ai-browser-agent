/** @type {import('tailwindcss').Config} */
module.exports = {
  content: [
    "./src/**/*.{js,jsx,ts,tsx}",
  ],
  darkMode: 'class',
  theme: {
    extend: {
      colors: {
        primary: {
          DEFAULT: '#0d6efd',
          light: '#0d6efd',
          dark: '#0056b3',
        },
        secondary: {
          DEFAULT: '#6c757d',
          light: '#6c757d',
          dark: '#495057',
        },
        user: {
          light: '#e6f7ff',
          lightText: '#0c5460',
          dark: '#0056b3',
          darkText: '#ffffff',
        },
        agent: {
          light: '#f0f4f8',
          lightBorder: '#d0d7de',
          dark: '#343a40',
          darkBorder: '#495057',
        },
        thinking: {
          light: '#fff8e6',
          lightText: '#664d03',
          dark: '#665d3c',
          darkText: '#fff3cd',
        },
        progress: {
          light: '#e9ecef',
          lightText: '#2d3748',
          dark: '#495057',
          darkText: '#e2e3e5',
        },
        error: {
          light: '#f8d7da',
          lightText: '#842029',
          dark: '#721c24',
          darkText: '#f8d7da',
        },
      },
    },
  },
  plugins: [],
} 
