import type { Config } from 'tailwindcss'
import tokens from './src/styles/tokens.json'



const config: Config = {
  darkMode: 'class',
  content: [
    './src/app/**/*.{ts,tsx}',
    './src/components/**/*.{ts,tsx}',
    './src/lib/**/*.{ts,tsx}',
    './src/stories/**/*.{ts,tsx}',
  ],
  theme: {
    container: {
      center: true,
      padding: '1rem',
      screens: {
        '2xl': '1400px',
      },
    },
    extend: {
      fontFamily: {
        sans: [tokens.typography.fontFamily.sans.split(',')[0], 'system-ui', 'sans-serif'],
        mono: [tokens.typography.fontFamily.mono.split(',')[0], 'ui-monospace', 'monospace'],
      },
      colors: {
        
        background: 'hsl(var(--background))',
        foreground: 'hsl(var(--foreground))',
        card: 'hsl(var(--card))',
        'card-foreground': 'hsl(var(--card-foreground))',
        popover: 'hsl(var(--popover))',
        'popover-foreground': 'hsl(var(--popover-foreground))',
        primary: 'hsl(var(--primary))',
        'primary-foreground': 'hsl(var(--primary-foreground))',
        secondary: 'hsl(var(--secondary))',
        'secondary-foreground': 'hsl(var(--secondary-foreground))',
        muted: 'hsl(var(--muted))',
        'muted-foreground': 'hsl(var(--muted-foreground))',
        accent: 'hsl(var(--accent))',
        'accent-foreground': 'hsl(var(--accent-foreground))',
        destructive: 'hsl(var(--destructive))',
        'destructive-foreground': 'hsl(var(--destructive-foreground))',
        border: 'hsl(var(--border))',
        input: 'hsl(var(--input))',
        ring: 'hsl(var(--ring))',
        
        'chart-1': 'hsl(var(--chart-1))',
        'chart-2': 'hsl(var(--chart-2))',
        'chart-3': 'hsl(var(--chart-3))',
        'chart-4': 'hsl(var(--chart-4))',
        'chart-5': 'hsl(var(--chart-5))',
        
        page: {
          DEFAULT: '#f8fafc',
          surface: '#ffffff',
          muted: '#f1f5f9',
          subtle: '#e2e8f0',
        },
        text: {
          DEFAULT: 'hsl(222, 84%, 4.9%)',
          secondary: 'hsl(215, 25%, 27%)',
          muted: 'hsl(215, 16%, 47%)',
        },
        
        blue: {
          50: '#f0f9ff',
          100: '#e0f2fe',
          200: '#bae6fd',
          300: '#7dd3fc',
          400: '#38bdf8',
          500: '#0ea5e9',
          600: '#0284c7',
          700: '#0369a1',
          800: '#075985',
          900: '#0c4a6e',
        },
        
        gradient: {
          primary: 'linear-gradient(135deg, #3b82f6 0%, #1d4ed8 50%, #1e40af 100%)',
          secondary: 'linear-gradient(135deg, #06b6d4 0%, #0891b2 50%, #0e7490 100%)',
          accent: 'linear-gradient(135deg, #8b5cf6 0%, #7c3aed 50%, #6d28d9 100%)',
          success: 'linear-gradient(135deg, #10b981 0%, #059669 50%, #047857 100%)',
          warning: 'linear-gradient(135deg, #f59e0b 0%, #d97706 50%, #b45309 100%)',
          hero: 'linear-gradient(135deg, #dbeafe 0%, #bfdbfe 25%, #93c5fd 50%, #60a5fa 100%)',
        },
      },
      borderRadius: {
        xs: '2px',
        sm: tokens.borderRadius.sm,
        DEFAULT: 'var(--radius)',
        base: tokens.borderRadius.base,
        md: tokens.borderRadius.md,
        lg: tokens.borderRadius.lg,
        xl: tokens.borderRadius.xl,
        '2xl': tokens.borderRadius['2xl'],
        '3xl': tokens.borderRadius['3xl'],
      },
      keyframes: {
        shimmer: {
          '0%': { backgroundPosition: '0% 50%' },
          '100%': { backgroundPosition: '200% 50%' },
        },
        pulseStrong: {
          '0%, 100%': { opacity: '1' },
          '50%': { opacity: '.4' },
        },
      },
      animation: {
        shimmer: 'shimmer 2.5s linear infinite',
        'pulse-strong': 'pulseStrong 2s ease-in-out infinite',
      },
      boxShadow: {
        focus: '0 0 0 1px hsl(var(--ring)), 0 0 0 4px hsl(var(--ring) / 0.35)',
        card: '0 4px 8px -2px rgba(0,0,0,0.08), 0 1px 3px rgba(0,0,0,0.06)',
        elevated: '0 10px 25px -5px rgba(0,0,0,0.25), 0 4px 6px -2px rgba(0,0,0,0.10)',
        'soft-lg': '0 6px 18px rgba(12,18,28,0.06)',
      },
      transitionDuration: {
        instant: tokens.motion.duration.instant,
        fast: tokens.motion.duration.fast,
        normal: tokens.motion.duration.normal,
        slow: tokens.motion.duration.slow,
        slower: tokens.motion.duration.slower,
        slowest: tokens.motion.duration.slowest,
      },
      transitionTimingFunction: {
        smooth: tokens.motion.easing.smooth,
        bounce: tokens.motion.easing.bounce,
        elastic: tokens.motion.easing.elastic,
      },
      zIndex: {
        dropdown: '1000',
        sticky: '1020',
        fixed: '1030',
        'modal-backdrop': '1040',
        modal: '1050',
        popover: '1060',
        tooltip: '1070',
        cursor: '9999',
      },
    },
  },
  future: {
    hoverOnlyWhenSupported: true,
  },
  plugins: [],
}
export default config
