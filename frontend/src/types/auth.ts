export interface User {
  id: string;
  email: string;
  full_name?: string;
  subscription_tier?: string;
}

export interface AuthTokens {
  access_token: string;
  refresh_token: string;
  expires_at?: string;
}

export interface LoginResponse {
  success: boolean;
  message: string;
  user?: User;
  access_token?: string;
  refresh_token?: string;
  expires_at?: string;
}

export interface SignupResponse {
  success: boolean;
  message: string;
  user_id?: string;
  email?: string;
  access_token?: string;
  refresh_token?: string;
}

export interface AuthContextType {
  user: User | null;
  isAuthenticated: boolean;
  isLoading: boolean;
  login: (email: string, password: string) => Promise<void>;
  signup: (email: string, password: string, fullName?: string) => Promise<void>;
  logout: () => void;
  refreshToken: () => Promise<boolean>;
}
