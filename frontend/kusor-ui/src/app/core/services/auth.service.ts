import { Injectable, signal, computed } from '@angular/core';
import { HttpClient } from '@angular/common/http';
import { Router } from '@angular/router';
import { Observable, tap } from 'rxjs';
import { environment } from '../../../environments/environment';

export interface User {
  id: string;
  username: string;
  email?: string;
  role: 'admin' | 'compliance' | 'legal' | 'credit' | 'user';
  full_name?: string;
  department?: string;
}

@Injectable({ providedIn: 'root' })
export class AuthService {
  private baseUrl = `${environment.apiUrl}/auth`;

  currentUser = signal<User | null>(this.loadStoredUser());
  isAuthenticated = computed(() => !!this.currentUser());
  userRole = computed(() => this.currentUser()?.role || 'user');

  constructor(private http: HttpClient, private router: Router) {}

  login(credentials: { username: string; password: string }): Observable<any> {
    return this.http.post<any>(`${this.baseUrl}/login`, credentials).pipe(
      tap(res => {
        if (res.access_token && res.user) {
          localStorage.setItem('kusor_token', res.access_token);
          localStorage.setItem('kusor_user', JSON.stringify(res.user));
          this.currentUser.set(res.user);
        }
      })
    );
  }

  logout(): void {
    localStorage.removeItem('kusor_token');
    localStorage.removeItem('kusor_user');
    this.currentUser.set(null);
    this.router.navigate(['/login']);
  }

  private loadStoredUser(): User | null {
    const raw = localStorage.getItem('kusor_user');
    if (!raw) return null;
    try {
      return JSON.parse(raw);
    } catch {
      return null;
    }
  }
}
