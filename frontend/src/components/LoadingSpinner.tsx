import React from 'react';

const LoadingSpinner: React.FC = () => {
  return (
    <div className="min-h-screen flex items-center justify-center bg-gray-50">
      <div className="text-center">
        <div className="animate-spin rounded-full h-16 w-16 border-b-2 border-blue-600 mx-auto"></div>
        <h2 className="text-xl text-gray-700 mt-4">Loading Stock Predictions...</h2>
        <p className="text-gray-500 mt-2">Fetching the latest ML predictions from NSE data</p>
      </div>
    </div>
  );
};

export default LoadingSpinner;