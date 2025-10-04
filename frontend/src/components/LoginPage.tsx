import React from 'react';
import { GoogleLogin, CredentialResponse } from '@react-oauth/google';
import { useAuth } from '../contexts/AuthContext';
import { User } from '../types';

interface LoginPageProps {
  onLoginSuccess?: () => void;
}

const LoginPage: React.FC<LoginPageProps> = ({ onLoginSuccess }) => {
  const { handleLoginSuccess } = useAuth();

  const decodeJWT = (token: string): any => {
    try {
      const base64Url = token.split('.')[1];
      const base64 = base64Url.replace(/-/g, '+').replace(/_/g, '/');
      const jsonPayload = decodeURIComponent(
        atob(base64)
          .split('')
          .map(c => '%' + ('00' + c.charCodeAt(0).toString(16)).slice(-2))
          .join('')
      );
      return JSON.parse(jsonPayload);
    } catch (error) {
      console.error('Error decoding JWT:', error);
      return null;
    }
  };

  const handleSuccess = (credentialResponse: CredentialResponse) => {
    if (credentialResponse.credential) {
      const userInfo = decodeJWT(credentialResponse.credential);
      
      if (userInfo) {
        const userData: User = {
          email: userInfo.email,
          name: userInfo.name,
          picture: userInfo.picture,
          sub: userInfo.sub,
        };
        
        handleLoginSuccess(userData);
        onLoginSuccess?.();
      }
    }
  };

  const handleError = () => {
    console.error('Google Login Failed');
  };

  return (
    <div className="min-h-screen bg-gradient-to-br from-blue-900 via-purple-900 to-indigo-900 flex items-center justify-center px-4">
      <div className="max-w-md w-full space-y-8">
        <div className="text-center">
          <h1 className="text-4xl font-bold text-white mb-2">Stock-ML</h1>
          <h2 className="text-xl text-gray-300 mb-8">NSE Stock Predictions Dashboard</h2>
          <div className="bg-white/10 backdrop-blur-sm rounded-lg p-8 border border-white/20">
            <div className="text-center mb-6">
              <div className="w-16 h-16 bg-blue-500 rounded-full flex items-center justify-center mx-auto mb-4">
                <svg className="w-8 h-8 text-white" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 19v-6a2 2 0 00-2-2H5a2 2 0 00-2 2v6a2 2 0 002 2h2a2 2 0 002-2zm0 0V9a2 2 0 012-2h2a2 2 0 012 2v10m-6 0a2 2 0 002 2h2a2 2 0 002-2m0 0V5a2 2 0 012-2h2a2 2 0 012 2v14a2 2 0 01-2 2h-2a2 2 0 01-2-2z" />
                </svg>
              </div>
              <h3 className="text-lg font-semibold text-white mb-2">
                Sign in to access predictions
              </h3>
              <p className="text-gray-300 text-sm mb-6">
                Get daily NSE stock predictions powered by machine learning
              </p>
            </div>
            
            <div className="flex justify-center">
              <GoogleLogin
                onSuccess={handleSuccess}
                onError={handleError}
                useOneTap={false}
                theme="filled_blue"
                size="large"
                text="signin_with"
                shape="rectangular"
              />
            </div>
            
            <div className="mt-6 text-xs text-gray-400 text-center">
              <p>By signing in, you agree to our Terms of Service</p>
              <p className="mt-1">This is for educational analysis only - not investment advice</p>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
};

export default LoginPage;