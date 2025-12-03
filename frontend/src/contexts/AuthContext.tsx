'use client';

import React, { createContext, useContext, useState, useEffect, ReactNode } from 'react';
import apiClient from '@/lib/api-client';
import { User, AuthContextType, LoginResponse, SignupResponse } from '@/types/auth';

const AuthContext = createContext<AuthContextType | undefined>(undefined);

export function AuthProvider({ children }: { children: ReactNode }) {
  const [user, setUser] = useState<User | null>(null);
  const [isLoading, setIsLoading] = useState(true);

  // Check if user is already logged in on mount
  useEffect(() => {
    const checkAuth = async () => {
      const token = localStorage.getItem('access_token');
      const storedUser = localStorage.getItem('user');

      if (token && storedUser) {
        try {
          setUser(JSON.parse(storedUser));
        } catch (error) {
          console.error('Failed to parse stored user:', error);
          localStorage.removeItem('user');
        }
      }
      setIsLoading(false);
    };

    checkAuth();
  }, []);

  const login = async (email: string, password: string) => {
    try {
      const response = await apiClient.post<LoginResponse>('/api/v1/auth/login', {
        email,
        password,
      });

      if (!response.data.success || !response.data.data) {
        throw new Error(response.data.message || 'Login failed');
      }

      // Backend returns: { success, message, data: { user, access_token, refresh_token } }
      const { user: userData, access_token, refresh_token } = response.data.data;

      // Save tokens and user data
      if (access_token) localStorage.setItem('access_token', access_token);
      if (refresh_token) localStorage.setItem('refresh_token', refresh_token);
      localStorage.setItem('user', JSON.stringify(userData));

      setUser(userData);
    } catch (error: any) {
      throw new Error(error.message || 'Login failed');
    }
  };

  const signup = async (email: string, password: string, fullName?: string) => {
    try {
      const response = await apiClient.post<SignupResponse>('/api/v1/auth/signup', {
        email,
        password,
        full_name: fullName,
      });

      if (!response.data.success || !response.data.data) {
        throw new Error(response.data.message || 'Signup failed');
      }

      // Backend returns: { success, message, data: { user_id, email, access_token, refresh_token } }
      const { user_id, email: userEmail, access_token, refresh_token } = response.data.data;

      // Create user object
      const userData: User = {
        id: user_id || '',
        email: userEmail || email,
        full_name: fullName,
      };

      // Save tokens and user data
      if (access_token) localStorage.setItem('access_token', access_token);
      if (refresh_token) localStorage.setItem('refresh_token', refresh_token);
      localStorage.setItem('user', JSON.stringify(userData));

      setUser(userData);
    } catch (error: any) {
      throw new Error(error.message || 'Signup failed');
    }
  };

  const logout = () => {
    // Clear all auth data
    localStorage.removeItem('access_token');
    localStorage.removeItem('refresh_token');
    localStorage.removeItem('user');
    setUser(null);

    // Call backend logout endpoint (fire and forget)
    const token = localStorage.getItem('access_token');
    if (token) {
      apiClient.post('/api/v1/auth/logout').catch(() => {
        // Ignore errors
      });
    }

    // Redirect to login
    if (typeof window !== 'undefined') {
      window.location.href = '/login';
    }
  };

  const refreshToken = async (): Promise<boolean> => {
    try {
      const refreshToken = localStorage.getItem('refresh_token');
      if (!refreshToken) return false;

      const response = await apiClient.post('/api/v1/auth/refresh', {
        refresh_token: refreshToken,
      });

      // Handle both nested and flat response structure
      const responseData = response.data.data || response.data;
      const access_token = responseData.access_token;
      const newRefreshToken = responseData.refresh_token;

      if (!access_token) {
        console.error('❌ No access token in refresh response');
        return false;
      }

      localStorage.setItem('access_token', access_token);
      if (newRefreshToken) {
        localStorage.setItem('refresh_token', newRefreshToken);
      }

      return true;
    } catch (error) {
      logout();
      return false;
    }
  };

  const value: AuthContextType = {
    user,
    isAuthenticated: !!user,
    isLoading,
    login,
    signup,
    logout,
    refreshToken,
  };

  return <AuthContext.Provider value={value}>{children}</AuthContext.Provider>;
}

export function useAuth() {
  const context = useContext(AuthContext);
  if (context === undefined) {
    throw new Error('useAuth must be used within an AuthProvider');
  }
  return context;
}
