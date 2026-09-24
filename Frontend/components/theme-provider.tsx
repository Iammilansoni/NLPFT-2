'use client';

/**
 * Theme Provider - Manages dark/light mode and primary color customization
 * Persists preferences to localStorage
 */

import React, { createContext, useContext, useEffect, useState } from 'react';

type Theme = 'light' | 'dark';
type ThemeColor = 'blue' | 'purple' | 'green' | 'orange' | 'pink' | 'red';

interface ThemeContextType {
  theme: Theme;
  themeColor: ThemeColor;
  setTheme: (theme: Theme) => void;
  setThemeColor: (color: ThemeColor) => void;
  toggleTheme: () => void;
}

const ThemeContext = createContext<ThemeContextType | undefined>(undefined);

const THEME_STORAGE_KEY = 'nlpforge-theme';
const COLOR_STORAGE_KEY = 'nlpforge-theme-color';

export function ThemeProvider({ children }: { children: React.ReactNode }) {
  const [theme, setThemeState] = useState<Theme>('dark');
  const [themeColor, setThemeColorState] = useState<ThemeColor>('blue');
  const [mounted, setMounted] = useState(false);

  // Load saved preferences on mount
  useEffect(() => {
    const savedTheme = localStorage.getItem(THEME_STORAGE_KEY) as Theme | null;
    const savedColor = localStorage.getItem(COLOR_STORAGE_KEY) as ThemeColor | null;

    if (savedTheme) {
      setThemeState(savedTheme);
    } else {
      // Check system preference
      const prefersDark = window.matchMedia('(prefers-color-scheme: dark)').matches;
      setThemeState(prefersDark ? 'dark' : 'light');
    }

    if (savedColor) {
      setThemeColorState(savedColor);
    }

    setMounted(true);
  }, []);

  // Apply theme to DOM
  useEffect(() => {
    if (!mounted) return;

    const root = document.documentElement;
    
    // Remove existing theme class
    root.classList.remove('light', 'dark');
    root.classList.add(theme);
    
    // Update theme attribute
    root.setAttribute('data-theme', theme);
    
    // Save to localStorage
    localStorage.setItem(THEME_STORAGE_KEY, theme);
  }, [theme, mounted]);

  // The brand colour comes from the design tokens in styles/globals.css. It used
  // to be overwritten here with an inline --primary on <html>, which silently
  // replaced the palette (and its dark-mode variant) on every page load.
  useEffect(() => {
    if (!mounted) return;
    const root = document.documentElement;
    ['--primary', '--primary-h', '--primary-s', '--primary-l'].forEach((v) => root.style.removeProperty(v));
    localStorage.removeItem(COLOR_STORAGE_KEY);
  }, [mounted]);

  const setTheme = (newTheme: Theme) => {
    setThemeState(newTheme);
  };

  const setThemeColor = (color: ThemeColor) => {
    setThemeColorState(color);
  };

  const toggleTheme = () => {
    setThemeState(prev => prev === 'light' ? 'dark' : 'light');
  };

  const value: ThemeContextType = {
    theme,
    themeColor,
    setTheme,
    setThemeColor,
    toggleTheme,
  };

  return (
    <ThemeContext.Provider value={value}>
      {/* Prevent flash of unstyled content */}
      <div style={{ visibility: mounted ? 'visible' : 'hidden' }}>
        {children}
      </div>
    </ThemeContext.Provider>
  );
}

export function useTheme() {
  const context = useContext(ThemeContext);
  
  if (context === undefined) {
    throw new Error('useTheme must be used within a ThemeProvider');
  }
  
  return context;
}
