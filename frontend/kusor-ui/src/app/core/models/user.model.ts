export interface User {
  id: string;
  username: string;
  role: 'admin' | 'compliance' | 'legal' | 'credit' | 'user' | string;
  full_name?: string;
}

export interface LoginResponse {
  access_token: string;
  user: User;
}
