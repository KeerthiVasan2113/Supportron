import type { Config } from 'tailwindcss'

const config: Config = {
  content: [
    './pages/**/*.{js,ts,jsx,tsx,mdx}',
    './components/**/*.{js,ts,jsx,tsx,mdx}',
    './app/**/*.{js,ts,jsx,tsx,mdx}',
  ],
  theme: {
    extend: {
      colors: {
        'primary': '#00f0ff',
        'primary-dark': '#00a8b8',
        'accent': '#7c3aed',
        'accent-light': '#a78bfa',
        'neon-cyan': '#00f0ff',
        'neon-purple': '#7c3aed',
        'neon-green': '#00ff88',
        'neon-pink': '#ff00ff',
        'tech-dark': '#0a0a0f',
        'tech-darker': '#050508',
        'tech-surface': '#111118',
        'tech-surface-hover': '#1a1a24',
        'tech-border': '#1e1e2e',
        'tech-border-glow': '#00f0ff33',
        'cyber-blue': '#0066ff',
        'cyber-purple': '#7c3aed',
        'text-primary': '#e0e0ff',
        'text-secondary': '#a0a0d0',
        'text-muted': '#7070a0',
        'text-glow': '#00f0ff',
      },
      screens: {
        'xs': '475px',
        '3xl': '1920px',
        '4xl': '2560px',
      },
      fontSize: {
        'fluid-xs': 'clamp(0.75rem, 0.7rem + 0.25vw, 0.875rem)',
        'fluid-sm': 'clamp(0.875rem, 0.8rem + 0.375vw, 1rem)',
        'fluid-base': 'clamp(1rem, 0.9rem + 0.5vw, 1.125rem)',
        'fluid-lg': 'clamp(1.125rem, 1rem + 0.625vw, 1.25rem)',
        'fluid-xl': 'clamp(1.25rem, 1.1rem + 0.75vw, 1.5rem)',
        'fluid-2xl': 'clamp(1.5rem, 1.3rem + 1vw, 2rem)',
        'fluid-3xl': 'clamp(1.875rem, 1.5rem + 1.875vw, 2.5rem)',
        'fluid-4xl': 'clamp(2.25rem, 1.8rem + 2.25vw, 3rem)',
        'fluid-5xl': 'clamp(3rem, 2.4rem + 3vw, 4rem)',
      },
      spacing: {
        'safe-top': 'env(safe-area-inset-top)',
        'safe-bottom': 'env(safe-area-inset-bottom)',
        'safe-left': 'env(safe-area-inset-left)',
        'safe-right': 'env(safe-area-inset-right)',
      },
      animation: {
        'pulse-slow': 'pulse 3s cubic-bezier(0.4, 0, 0.6, 1) infinite',
        'gradient': 'gradient 15s ease infinite',
        'float': 'float 6s ease-in-out infinite',
        'glow': 'glow 2s ease-in-out infinite alternate',
        'glow-cyan': 'glow-cyan 2s ease-in-out infinite alternate',
        'glow-purple': 'glow-purple 2.5s ease-in-out infinite alternate',
        'scan': 'scan 8s linear infinite',
        'glitch': 'glitch 0.3s infinite',
        'flicker': 'flicker 3s infinite',
        'grid-move': 'grid-move 20s linear infinite',
      },
      keyframes: {
        gradient: {
          '0%, 100%': {
            'background-position': '0% 50%',
          },
          '50%': {
            'background-position': '100% 50%',
          },
        },
        float: {
          '0%, 100%': {
            transform: 'translateY(0px)',
          },
          '50%': {
            transform: 'translateY(-20px)',
          },
        },
        glow: {
          '0%': {
            opacity: '0.5',
          },
          '100%': {
            opacity: '1',
          },
        },
        'glow-cyan': {
          '0%': {
            'text-shadow': '0 0 5px #00f0ff, 0 0 10px #00f0ff, 0 0 15px #00f0ff',
            opacity: '0.8',
          },
          '100%': {
            'text-shadow': '0 0 10px #00f0ff, 0 0 20px #00f0ff, 0 0 30px #00f0ff, 0 0 40px #00f0ff',
            opacity: '1',
          },
        },
        'glow-purple': {
          '0%': {
            'box-shadow': '0 0 5px #7c3aed, 0 0 10px #7c3aed',
            opacity: '0.7',
          },
          '100%': {
            'box-shadow': '0 0 10px #7c3aed, 0 0 20px #7c3aed, 0 0 30px #7c3aed',
            opacity: '1',
          },
        },
        scan: {
          '0%': {
            transform: 'translateY(-100%)',
          },
          '100%': {
            transform: 'translateY(100vh)',
          },
        },
        glitch: {
          '0%, 100%': {
            transform: 'translate(0)',
          },
          '20%': {
            transform: 'translate(-2px, 2px)',
          },
          '40%': {
            transform: 'translate(-2px, -2px)',
          },
          '60%': {
            transform: 'translate(2px, 2px)',
          },
          '80%': {
            transform: 'translate(2px, -2px)',
          },
        },
        flicker: {
          '0%, 100%': {
            opacity: '1',
          },
          '41.99%': {
            opacity: '1',
          },
          '42%': {
            opacity: '0',
          },
          '43%': {
            opacity: '0',
          },
          '43.01%': {
            opacity: '1',
          },
          '47.99%': {
            opacity: '1',
          },
          '48%': {
            opacity: '0',
          },
          '49%': {
            opacity: '0',
          },
          '49.01%': {
            opacity: '1',
          },
        },
        'grid-move': {
          '0%': {
            transform: 'translate(0, 0)',
          },
          '100%': {
            transform: 'translate(50px, 50px)',
          },
        },
      },
      backgroundImage: {
        'gradient-radial': 'radial-gradient(var(--tw-gradient-stops))',
        'gradient-conic': 'conic-gradient(from 180deg at 50% 50%, var(--tw-gradient-stops))',
      },
    },
  },
  plugins: [],
}
export default config

