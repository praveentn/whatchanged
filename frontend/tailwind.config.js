// frontend/tailwind.config.js
/** @type {import('tailwindcss').Config} */
export default {
  content: [
    "./index.html",
    "./src/**/*.{js,ts,jsx,tsx}",
  ],
  theme: {
    extend: {
      colors: {
        // Brand colors
        primary: {
          50: '#eff6ff',
          100: '#dbeafe',
          200: '#bfdbfe',
          300: '#93c5fd',
          400: '#60a5fa',
          500: '#3b82f6',
          600: '#2563eb',
          700: '#1d4ed8',
          800: '#1e40af',
          900: '#1e3a8a',
        },
        // Semantic colors for document analysis
        intent: {
          overview: '#10b981',      // Green
          requirements: '#3b82f6',  // Blue
          design: '#8b5cf6',        // Purple
          procedure: '#f59e0b',     // Orange
          risks: '#ef4444',         // Red
          example: '#06b6d4',       // Cyan
          conclusion: '#6b7280',    // Gray
          other: '#9ca3af',         // Light gray
        },
        // Diff colors
        diff: {
          add: '#dcfce7',           // Light green
          'add-text': '#166534',    // Dark green
          delete: '#fef2f2',        // Light red
          'delete-text': '#991b1b', // Dark red
          change: '#fef3c7',        // Light yellow
          'change-text': '#92400e', // Dark yellow
          move: '#dbeafe',          // Light blue
          'move-text': '#1d4ed8',   // Dark blue
        }
      },
      fontFamily: {
        sans: ['Inter', 'system-ui', 'sans-serif'],
        mono: ['JetBrains Mono', 'Fira Code', 'Monaco', 'Consolas', 'monospace'],
      },
      spacing: {
        '18': '4.5rem',
        '88': '22rem',
      },
      animation: {
        'fade-in': 'fadeIn 0.5s ease-in-out',
        'slide-up': 'slideUp 0.3s ease-out',
        'slide-down': 'slideDown 0.3s ease-out',
        'pulse-slow': 'pulse 3s infinite',
      },
      keyframes: {
        fadeIn: {
          '0%': { opacity: '0' },
          '100%': { opacity: '1' },
        },
        slideUp: {
          '0%': { transform: 'translateY(10px)', opacity: '0' },
          '100%': { transform: 'translateY(0)', opacity: '1' },
        },
        slideDown: {
          '0%': { transform: 'translateY(-10px)', opacity: '0' },
          '100%': { transform: 'translateY(0)', opacity: '1' },
        },
      },
      typography: {
        DEFAULT: {
          css: {
            maxWidth: 'none',
            color: '#374151',
            '[class~="lead"]': {
              color: '#6b7280',
            },
            strong: {
              color: '#111827',
            },
            'ol > li::before': {
              color: '#6b7280',
            },
            'ul > li::before': {
              backgroundColor: '#d1d5db',
            },
            hr: {
              borderColor: '#e5e7eb',
            },
            blockquote: {
              color: '#6b7280',
              borderLeftColor: '#e5e7eb',
            },
            h1: {
              color: '#111827',
            },
            h2: {
              color: '#111827',
            },
            h3: {
              color: '#111827',
            },
            h4: {
              color: '#111827',
            },
            'figure figcaption': {
              color: '#6b7280',
            },
            code: {
              color: '#111827',
              backgroundColor: '#f3f4f6',
              paddingLeft: '4px',
              paddingRight: '4px',
              paddingTop: '2px',
              paddingBottom: '2px',
              borderRadius: '0.25rem',
              fontWeight: '600',
            },
            'code::before': {
              content: '""',
            },
            'code::after': {
              content: '""',
            },
            pre: {
              backgroundColor: '#1f2937',
              color: '#f9fafb',
            },
            'pre code': {
              backgroundColor: 'transparent',
              color: 'inherit',
            },
          },
        },
      },
      boxShadow: {
        'outline-blue': '0 0 0 3px rgba(59, 130, 246, 0.1)',
        'outline-red': '0 0 0 3px rgba(239, 68, 68, 0.1)',
        'outline-green': '0 0 0 3px rgba(16, 185, 129, 0.1)',
      },
      screens: {
        'xs': '475px',
      },
      gridTemplateColumns: {
        'sidebar': '16rem 1fr',
        'sidebar-collapsed': '4rem 1fr',
      },
    },
  },
  plugins: [
    require('@tailwindcss/forms'),
    require('@tailwindcss/typography'),
    require('@tailwindcss/aspect-ratio'),
    // Custom plugin for utility classes
    function({ addUtilities }) {
      const newUtilities = {
        '.scrollbar-hide': {
          /* IE and Edge */
          '-ms-overflow-style': 'none',
          /* Firefox */
          'scrollbar-width': 'none',
          /* Safari and Chrome */
          '&::-webkit-scrollbar': {
            display: 'none'
          }
        },
        '.scrollbar-default': {
          /* IE and Edge */
          '-ms-overflow-style': 'auto',
          /* Firefox */
          'scrollbar-width': 'auto',
          /* Safari and Chrome */
          '&::-webkit-scrollbar': {
            display: 'block'
          }
        },
        // Glass morphism effect
        '.glass': {
          'background': 'rgba(255, 255, 255, 0.1)',
          'backdrop-filter': 'blur(10px)',
          'border': '1px solid rgba(255, 255, 255, 0.2)',
        },
        // Gradient text
        '.gradient-text': {
          'background': 'linear-gradient(45deg, #3b82f6, #8b5cf6)',
          '-webkit-background-clip': 'text',
          '-webkit-text-fill-color': 'transparent',
          'background-clip': 'text',
        },
        // Code block styling
        '.code-block': {
          'background': '#1f2937',
          'color': '#f9fafb',
          'border-radius': '0.5rem',
          'padding': '1rem',
          'font-family': 'JetBrains Mono, Fira Code, Monaco, Consolas, monospace',
          'font-size': '0.875rem',
          'line-height': '1.5',
          'overflow-x': 'auto',
        },
        // Diff highlighting
        '.diff-line-add': {
          'background-color': '#dcfce7',
          'color': '#166534',
          'border-left': '4px solid #22c55e',
        },
        '.diff-line-delete': {
          'background-color': '#fef2f2',
          'color': '#991b1b',
          'border-left': '4px solid #ef4444',
        },
        '.diff-line-change': {
          'background-color': '#fef3c7',
          'color': '#92400e',
          'border-left': '4px solid #f59e0b',
        },
        // Loading states
        '.loading-shimmer': {
          'background': 'linear-gradient(110deg, #e2e8f0 8%, #f1f5f9 18%, #e2e8f0 33%)',
          'background-size': '200% 100%',
          'animation': 'shimmer 1.5s infinite',
        },
      }

      addUtilities(newUtilities)
    },
    // Custom plugin for animations
    function({ addKeyframes }) {
      addKeyframes({
        shimmer: {
          '0%': { 'background-position': '-200% 0' },
          '100%': { 'background-position': '200% 0' },
        }
      })
    }
  ],
  // Dark mode configuration
  darkMode: 'class',
}