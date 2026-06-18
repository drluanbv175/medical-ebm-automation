import type { Config } from "tailwindcss";

const config: Config = {
  content: ["./app/**/*.{ts,tsx}", "./components/**/*.{ts,tsx}", "./lib/**/*.{ts,tsx}"],
  theme: {
    extend: {
      colors: {
        ink: "#16202a",
        paper: "#f8faf7",
        clinic: "#246b61",
        caution: "#b46a00",
        danger: "#b42318"
      }
    }
  },
  plugins: []
};

export default config;
