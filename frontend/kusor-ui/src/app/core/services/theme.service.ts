import { Injectable, signal, effect } from '@angular/core';

export type ThemeMode = 'light' | 'dark';

@Injectable({
  providedIn: 'root'
})
export class ThemeService {
  private readonly THEME_KEY = 'kusor_theme_mode';
  
  currentTheme = signal<ThemeMode>('dark');

  constructor() {
    const savedTheme = typeof localStorage !== 'undefined' ? localStorage.getItem(this.THEME_KEY) as ThemeMode : null;
    if (savedTheme === 'dark' || savedTheme === 'light') {
      this.currentTheme.set(savedTheme);
    } else {
      this.currentTheme.set('dark');
    }

    // Apply theme reactively to both root and body
    effect(() => {
      const theme = this.currentTheme();
      if (typeof localStorage !== 'undefined') {
        localStorage.setItem(this.THEME_KEY, theme);
      }
      if (typeof document !== 'undefined') {
        const root = document.documentElement;
        const body = document.body;
        if (theme === 'dark') {
          root.classList.add('dark');
          root.classList.remove('light');
          body.classList.add('dark');
          body.classList.remove('light');
        } else {
          root.classList.add('light');
          root.classList.remove('dark');
          body.classList.add('light');
          body.classList.remove('dark');
        }
      }
    });
  }

  toggleTheme() {
    this.currentTheme.update(current => current === 'light' ? 'dark' : 'light');
  }

  setTheme(theme: ThemeMode) {
    this.currentTheme.set(theme);
  }

  isDark(): boolean {
    return this.currentTheme() === 'dark';
  }
}
