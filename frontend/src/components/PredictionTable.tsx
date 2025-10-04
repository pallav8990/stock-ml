import React from 'react';
import { StockPrediction, StockAccuracy } from '../types';

interface PredictionTableProps {
  predictions: StockPrediction[];
  accuracy: StockAccuracy[];
  loading: boolean;
}

const PredictionTable: React.FC<PredictionTableProps> = ({ predictions, accuracy, loading }) => {
  const getAccuracyForStock = (ticker: string): StockAccuracy | undefined => {
    return accuracy.find(acc => acc.ticker === ticker);
  };

  const formatPrediction = (value: number): string => {
    const percentage = (value * 100).toFixed(3);
    return `${percentage}%`;
  };

  const formatConfidence = (value: number): string => {
    return value.toFixed(2);
  };

  const getPredictionColor = (value: number): string => {
    if (value > 0) return 'text-green-600 bg-green-50';
    if (value < 0) return 'text-red-600 bg-red-50';
    return 'text-gray-600 bg-gray-50';
  };

  const getConfidenceColor = (value: number): string => {
    if (value > 30) return 'text-blue-600 bg-blue-50';
    if (value > 20) return 'text-yellow-600 bg-yellow-50';
    return 'text-gray-600 bg-gray-50';
  };

  if (loading) {
    return (
      <div className="bg-white rounded-lg shadow">
        <div className="p-8 text-center">
          <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-blue-600 mx-auto"></div>
          <p className="mt-2 text-gray-600">Loading predictions...</p>
        </div>
      </div>
    );
  }

  if (predictions.length === 0) {
    return (
      <div className="bg-white rounded-lg shadow">
        <div className="p-8 text-center">
          <div className="text-gray-400 mb-4">
            <svg className="w-12 h-12 mx-auto" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 19v-6a2 2 0 00-2-2H5a2 2 0 00-2 2v6a2 2 0 002 2h2a2 2 0 002-2zm0 0V9a2 2 0 012-2h2a2 2 0 012 2v10m-6 0a2 2 0 002 2h2a2 2 0 002-2m0 0V5a2 2 0 012-2h2a2 2 0 012 2v14a2 2 0 01-2 2h-2a2 2 0 01-2-2z" />
            </svg>
          </div>
          <h3 className="text-lg font-medium text-gray-900 mb-2">No predictions available</h3>
          <p className="text-gray-500">Try adjusting your filters or check back later for new predictions.</p>
        </div>
      </div>
    );
  }

  return (
    <div className="bg-white rounded-lg shadow overflow-hidden">
      <div className="px-6 py-4 border-b border-gray-200">
        <h3 className="text-lg font-semibold text-gray-900">Stock Predictions</h3>
        <p className="text-sm text-gray-500">
          Showing {predictions.length} predictions sorted by confidence score
        </p>
      </div>
      
      <div className="overflow-x-auto">
        <table className="min-w-full divide-y divide-gray-200">
          <thead className="bg-gray-50">
            <tr>
              <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                Stock Symbol
              </th>
              <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                Series
              </th>
              <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                Prediction
              </th>
              <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                Confidence
              </th>
              <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                Historical Accuracy
              </th>
              <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                Date
              </th>
            </tr>
          </thead>
          <tbody className="bg-white divide-y divide-gray-200">
            {predictions.map((prediction, index) => {
              const stockAccuracy = getAccuracyForStock(prediction.ticker);
              return (
                <tr key={`${prediction.ticker}-${index}`} className="hover:bg-gray-50">
                  <td className="px-6 py-4 whitespace-nowrap">
                    <div className="text-sm font-medium text-gray-900">
                      {prediction.ticker}
                    </div>
                  </td>
                  <td className="px-6 py-4 whitespace-nowrap">
                    <span className="inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium bg-gray-100 text-gray-800">
                      {prediction.series}
                    </span>
                  </td>
                  <td className="px-6 py-4 whitespace-nowrap">
                    <span className={`inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium ${getPredictionColor(prediction.y_pred)}`}>
                      {formatPrediction(prediction.y_pred)}
                    </span>
                  </td>
                  <td className="px-6 py-4 whitespace-nowrap">
                    <span className={`inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium ${getConfidenceColor(prediction.y_pred_conf)}`}>
                      {formatConfidence(prediction.y_pred_conf)}
                    </span>
                  </td>
                  <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-500">
                    {stockAccuracy ? (
                      <div>
                        <div>Accuracy: {(stockAccuracy.directional_accuracy * 100).toFixed(1)}%</div>
                        <div>MAE: {stockAccuracy.mae.toFixed(4)}</div>
                      </div>
                    ) : (
                      <span className="text-gray-400">No data</span>
                    )}
                  </td>
                  <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-500">
                    {new Date(prediction.date).toLocaleDateString()}
                  </td>
                </tr>
              );
            })}
          </tbody>
        </table>
      </div>
    </div>
  );
};

export default PredictionTable;