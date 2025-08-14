/** @type {import('tailwindcss').Config} */
export default {
  darkmode: ["class"],
  content: ["./index.html", "./src/**/*.{js,jsx,ts,tsx}", "./components/**/*"],
  theme: { extend: {} },
  plugins: [require("tailwindcss-animate")],
}
