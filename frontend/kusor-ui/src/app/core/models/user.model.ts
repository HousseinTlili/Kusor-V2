export interface User {
  id: string;
  username: string;
  role: 'admin' | 'user';
}

export interface LoginResponse {
  access_token: string;
  user: User;
}
