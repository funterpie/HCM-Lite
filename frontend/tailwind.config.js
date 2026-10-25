/** @type {import('tailwindcss').Config} */
export default {
  darkMode: 'class',
  content: ['./index.html', './src/**/*.{js,ts,jsx,tsx}'],
  theme: {
    extend: {
      colors: {
        background: 'var(--bg)',
        foreground: 'var(--fg)',
        surface: 'var(--surface)',
        'surface-elevated': 'var(--surface-elevated)',
        border: 'var(--border)',
        muted: 'var(--muted)',
        'muted-foreground': 'var(--muted-fg)',
        accent: {
          DEFAULT: 'var(--accent)',
          foreground: 'var(--accent-fg)',
          hover: 'var(--accent-hover)',
        },
        danger: {
          DEFAULT: '#EF4444',
          surface: '#FEF2F2',
          border: '#FCA5A5',
        },
        success: {
          DEFAULT: '#10B981',
          surface: '#ECFDF5',
          border: '#6EE7B7',
        },
        warning: {
          DEFAULT: '#F59E0B',
          surface: '#FFFBEB',
          border: '#FCD34D',
        },
      },
      fontFamily: {
        sans: ['Inter', 'system-ui', '-apple-system', 'sans-serif'],
      },
      borderRadius: {
        none: '0',
        sm: '2px',
        DEFAULT: '4px',
        md: '6px',
        lg: '8px',
      },
    },
  },
  plugins: [],
};
