import { Injectable, signal, effect } from '@angular/core';

export type ThemeMode = 'light' | 'dark';

@Injectable({
  providedIn: 'root'
})
export class ThemeService {
  private readonly THEME_KEY = 'kusor_theme_mode';
  
  // Default to light theme for corporate banking look
  currentTheme = signal<ThemeMode>('light');

  constructor() {
    // Load persisted theme or default to light
    const savedTheme = localStorage.getItem(this.THEME_KEY) as ThemeMode;
    if (savedTheme === 'dark' || savedTheme === 'light') {
      this.currentTheme.set(savedTheme);
    } else {
      this.currentTheme.set('light');
    }

    // Reactively update document class
    effect(() => {
      const theme = this.currentTheme();
      localStorage.setItem(this.THEME_KEY, theme);
      if (typeof document !== 'undefined') {
        const root = document.documentElement;
        if (theme === 'dark') {
          root.classList.add('dark');
          root.classList.remove('light');
        } else {
          root.classList.add('light');
          root.classList.remove('dark');
        }
      }
    });
  }

  toggleTheme() {
    this.currentTheme.update(current => current === 'light' ? 'dark' : 'light');
  }

  isDark(): boolean {
    return this.currentTheme() === 'dark';
  }
}
