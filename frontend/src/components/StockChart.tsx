import React from 'react';
import {
  Chart as ChartJS,
  CategoryScale,
  LinearScale,
  PointElement,
  LineElement,
  BarElement,
  Title,
  Tooltip,
  Legend,
} from 'chart.js';
import { Scatter, Bar } from 'react-chartjs-2';
import { StockPrediction, StockAccuracy } from '../types';

ChartJS.register(
  CategoryScale,
  LinearScale,
  PointElement,
  LineElement,
  BarElement,
  Title,
  Tooltip,
  Legend
);

interface StockChartProps {
  predictions: StockPrediction[];
  accuracy: StockAccuracy[];
}

const StockChart: React.FC<StockChartProps> = ({ predictions, accuracy }) => {
  const [chartType, setChartType] = React.useState<'scatter' | 'confidence'>('scatter');

  // Scatter plot data: Prediction vs Confidence
  const scatterData = {
    datasets: [
      {
        label: 'Positive Predictions',
        data: predictions
          .filter(p => p.y_pred > 0)
          .map(p => ({
            x: p.y_pred * 100, // Convert to percentage
            y: p.y_pred_conf,
          })),
        backgroundColor: 'rgba(16, 185, 129, 0.6)',
        borderColor: 'rgba(16, 185, 129, 1)',
        borderWidth: 1,
      },
      {
        label: 'Negative Predictions',
        data: predictions
          .filter(p => p.y_pred <= 0)
          .map(p => ({
            x: p.y_pred * 100,
            y: p.y_pred_conf,
          })),
        backgroundColor: 'rgba(239, 68, 68, 0.6)',
        borderColor: 'rgba(239, 68, 68, 1)',
        borderWidth: 1,
      },
    ],
  };

  const scatterOptions = {
    responsive: true,
    plugins: {
      legend: {
        position: 'top' as const,
      },
      title: {
        display: true,
        text: 'Prediction Value vs Confidence Score',
      },
      tooltip: {
        callbacks: {
          label: function(context: any) {
            return `Prediction: ${context.parsed.x.toFixed(3)}%, Confidence: ${context.parsed.y.toFixed(2)}`;
          },
        },
      },
    },
    scales: {
      x: {
        display: true,
        title: {
          display: true,
          text: 'Prediction Value (%)',
        },
      },
      y: {
        display: true,
        title: {
          display: true,
          text: 'Confidence Score',
        },
      },
    },
  };

  // Bar chart data: Confidence distribution
  const confidenceRanges = ['0-10', '10-20', '20-30', '30-40', '40+'];
  const confidenceData = {
    labels: confidenceRanges,
    datasets: [
      {
        label: 'Number of Stocks',
        data: [
          predictions.filter(p => p.y_pred_conf >= 0 && p.y_pred_conf < 10).length,
          predictions.filter(p => p.y_pred_conf >= 10 && p.y_pred_conf < 20).length,
          predictions.filter(p => p.y_pred_conf >= 20 && p.y_pred_conf < 30).length,
          predictions.filter(p => p.y_pred_conf >= 30 && p.y_pred_conf < 40).length,
          predictions.filter(p => p.y_pred_conf >= 40).length,
        ],
        backgroundColor: [
          'rgba(156, 163, 175, 0.8)',
          'rgba(251, 191, 36, 0.8)',
          'rgba(59, 130, 246, 0.8)',
          'rgba(16, 185, 129, 0.8)',
          'rgba(139, 92, 246, 0.8)',
        ],
        borderColor: [
          'rgba(156, 163, 175, 1)',
          'rgba(251, 191, 36, 1)',
          'rgba(59, 130, 246, 1)',
          'rgba(16, 185, 129, 1)',
          'rgba(139, 92, 246, 1)',
        ],
        borderWidth: 1,
      },
    ],
  };

  const barOptions = {
    responsive: true,
    plugins: {
      legend: {
        display: false,
      },
      title: {
        display: true,
        text: 'Confidence Score Distribution',
      },
    },
    scales: {
      y: {
        beginAtZero: true,
        title: {
          display: true,
          text: 'Number of Stocks',
        },
      },
      x: {
        title: {
          display: true,
          text: 'Confidence Range',
        },
      },
    },
  };

  return (
    <div className="bg-white rounded-lg shadow p-6">
      <div className="flex justify-between items-center mb-4">
        <h3 className="text-lg font-semibold text-gray-900">Prediction Analysis</h3>
        <div className="flex space-x-2">
          <button
            onClick={() => setChartType('scatter')}
            className={`px-3 py-1 rounded text-sm ${
              chartType === 'scatter'
                ? 'bg-blue-600 text-white'
                : 'bg-gray-200 text-gray-700 hover:bg-gray-300'
            }`}
          >
            Scatter Plot
          </button>
          <button
            onClick={() => setChartType('confidence')}
            className={`px-3 py-1 rounded text-sm ${
              chartType === 'confidence'
                ? 'bg-blue-600 text-white'
                : 'bg-gray-200 text-gray-700 hover:bg-gray-300'
            }`}
          >
            Confidence Distribution
          </button>
        </div>
      </div>

      <div className="h-80">
        {chartType === 'scatter' ? (
          <Scatter data={scatterData} options={scatterOptions} />
        ) : (
          <Bar data={confidenceData} options={barOptions} />
        )}
      </div>

      {/* Chart insights */}
      <div className="mt-4 p-4 bg-gray-50 rounded-md">
        <h4 className="text-sm font-medium text-gray-700 mb-2">Insights</h4>
        <div className="grid grid-cols-1 md:grid-cols-2 gap-4 text-sm text-gray-600">
          <div>
            <span className="font-medium">Total Predictions:</span> {predictions.length}
          </div>
          <div>
            <span className="font-medium">Positive Predictions:</span>{' '}
            {predictions.filter(p => p.y_pred > 0).length} (
            {((predictions.filter(p => p.y_pred > 0).length / predictions.length) * 100).toFixed(1)}%)
          </div>
          <div>
            <span className="font-medium">High Confidence (&gt;30):</span>{' '}
            {predictions.filter(p => p.y_pred_conf > 30).length}
          </div>
          <div>
            <span className="font-medium">Avg Confidence:</span>{' '}
            {predictions.length > 0
              ? (predictions.reduce((sum, p) => sum + p.y_pred_conf, 0) / predictions.length).toFixed(2)
              : 'N/A'}
          </div>
        </div>
      </div>
    </div>
  );
};

export default StockChart;