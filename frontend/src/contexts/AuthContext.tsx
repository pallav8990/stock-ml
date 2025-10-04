import React, { createContext, useContext, useEffect, useState, ReactNode } from 'react';
import { GoogleOAuthProvider } from '@react-oauth/google';
import { User, AuthContextType } from '../types';

const AuthContext = createContext<AuthContextType | undefined>(undefined);

export const useAuth = () => {
  const context = useContext(AuthContext);
  if (context === undefined) {
    throw new Error('useAuth must be used within an AuthProvider');
  }
  return context;
};

interface AuthProviderProps {
  children: ReactNode;
}

export const AuthProvider: React.FC<AuthProviderProps> = ({ children }) => {
  const [user, setUser] = useState<User | null>(null);
  const [isLoading, setIsLoading] = useState(true);

  useEffect(() => {
    // Check if user is already logged in (from localStorage)
    const savedUser = localStorage.getItem('stockml_user');
    if (savedUser) {
      try {
        setUser(JSON.parse(savedUser));
      } catch (error) {
        console.error('Error parsing saved user:', error);
        localStorage.removeItem('stockml_user');
      }
    }
    setIsLoading(false);
  }, []);

  const login = () => {
    // This will be handled by the GoogleLogin component
    console.log('Login function called');
  };

  const logout = () => {
    setUser(null);
    localStorage.removeItem('stockml_user');
  };

  const handleLoginSuccess = (userData: User) => {
    setUser(userData);
    localStorage.setItem('stockml_user', JSON.stringify(userData));
  };

  const value = {
    user,
    isLoading,
    login,
    logout,
    handleLoginSuccess
  };

  return (
    <AuthContext.Provider value={value}>
      <GoogleOAuthProvider clientId={process.env.REACT_APP_GOOGLE_CLIENT_ID || ''}>
        {children}
      </GoogleOAuthProvider>
    </AuthContext.Provider>
  );
};