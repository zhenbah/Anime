'use client';

import { createContext, useContext, useState, ReactNode } from 'react';

interface User {
  id: string;
  name: string;
  email: string;
  role: 'admin' | 'user';
}

interface AuthContextType {
  user: User | null;
  login: (email: string, password: string) => Promise<void>;
  logout: () => void;
  isAuthenticated: boolean;
}

const AuthContext = createContext<AuthContextType | undefined>(undefined);

export function AuthProvider({ children }: { children: ReactNode }) {
  const [user, setUser] = useState<User | null>(null);

  useEffect(() => {
    // Check for stored token
    const token = localStorage.getItem('token');
    if (token) {
      // Validate token (mock)
      setUser({
        id: '1',
        name: 'Admin User',
        email: 'admin@scrapepro.com',
        role: 'admin',
      });
    }
  }, []);

  const login = async (email: string, password: string) => {
    // Mock API call
    await new Promise(resolve => setTimeout(resolve, 1000));
    
    const mockToken = 'mock-jwt-token';
    localStorage.setItem('token', mockToken);
    
    setUser({
      id: '1',
      name: 'Admin User',
      email,
      role: 'admin',
    });
  };

  const logout = () => {
    localStorage.removeItem('token');
    setUser(null);
  };

  return (
    <AuthContext.Provider value={{ user, login, logout, isAuthenticated: !!user }}>
      {children}
    </AuthContext.Provider>
  );
}

export function useAuth() {
  const context = useContext(AuthContext);
  if (context === undefined) {
    throw new Error('useAuth must be used within an AuthProvider');
  }
  return context;
}
