import React, { useState, useEffect } from 'react';
import { useAuth } from '../contexts/AuthContext';
import { stockApi } from '../services/api';
import { StockPrediction, StockAccuracy, FilterOptions, StockSeries } from '../types';
import PredictionTable from '../components/PredictionTable';
import StockChart from '../components/StockChart';
import FilterPanel from '../components/FilterPanel';
import LoadingSpinner from '../components/LoadingSpinner';

const Dashboard: React.FC = () => {
  const { user, logout } = useAuth();
  const [predictions, setPredictions] = useState<StockPrediction[]>([]);
  const [accuracy, setAccuracy] = useState<StockAccuracy[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [filters, setFilters] = useState<FilterOptions>({
    series: 'ALL',
    sortBy: 'y_pred_conf',
    sortOrder: 'desc',
    limit: 50,
  });

  useEffect(() => {
    fetchData();
  }, []);

  const fetchData = async () => {
    try {
      setLoading(true);
      setError(null);
      
      const [predictionsData, accuracyData] = await Promise.all([
        stockApi.getPredictionsToday(),
        stockApi.getAccuracyByStock(60), // 60-day window
      ]);
      
      setPredictions(predictionsData || []);
      setAccuracy(accuracyData || []);
    } catch (err) {
      setError('Failed to fetch data. Please try again.');
      console.error('Error fetching dashboard data:', err);
    } finally {
      setLoading(false);
    }
  };

  const handleFilterChange = (newFilters: Partial<FilterOptions>) => {
    setFilters(prev => ({ ...prev, ...newFilters }));
  };

  const filteredAndSortedPredictions = React.useMemo(() => {
    let filtered = predictions;
    
    // Filter by series
    if (filters.series !== 'ALL') {
      filtered = filtered.filter(p => p.series === filters.series);
    }
    
    // Sort
    filtered = [...filtered].sort((a, b) => {
      let aValue = a[filters.sortBy];
      let bValue = b[filters.sortBy];
      
      if (typeof aValue === 'string') {
        aValue = aValue.toLowerCase();
        bValue = (bValue as string).toLowerCase();
      }
      
      if (filters.sortOrder === 'asc') {
        return aValue > bValue ? 1 : -1;
      } else {
        return aValue < bValue ? 1 : -1;
      }
    });
    
    // Limit results
    return filtered.slice(0, filters.limit);
  }, [predictions, filters]);

  const statsData = React.useMemo(() => {
    const totalStocks = predictions.length;
    const positiveStocks = predictions.filter(p => p.y_pred > 0).length;
    const highConfidenceStocks = predictions.filter(p => p.y_pred_conf > 30).length;
    const avgConfidence = predictions.length > 0 
      ? predictions.reduce((sum, p) => sum + p.y_pred_conf, 0) / predictions.length 
      : 0;

    return {
      totalStocks,
      positiveStocks,
      highConfidenceStocks,
      avgConfidence: avgConfidence.toFixed(2),
    };
  }, [predictions]);

  if (loading) {
    return <LoadingSpinner />;
  }

  return (
    <div className="min-h-screen bg-gray-50">
      {/* Header */}
      <header className="bg-white shadow-sm border-b">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <div className="flex justify-between items-center h-16">
            <div className="flex items-center">
              <h1 className="text-2xl font-bold text-gray-900">Stock-ML Dashboard</h1>
            </div>
            <div className="flex items-center space-x-4">
              <div className="flex items-center space-x-3">
                <img 
                  src={user?.picture} 
                  alt={user?.name}
                  className="w-8 h-8 rounded-full"
                />
                <span className="text-sm text-gray-700">{user?.name}</span>
              </div>
              <button
                onClick={logout}
                className="bg-red-600 text-white px-4 py-2 rounded-md text-sm hover:bg-red-700 transition-colors"
              >
                Logout
              </button>
            </div>
          </div>
        </div>
      </header>

      {/* Main Content */}
      <main className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
        {error && (
          <div className="mb-6 bg-red-50 border border-red-200 text-red-700 px-4 py-3 rounded-md flex items-center justify-between">
            <span>{error}</span>
            <button
              onClick={fetchData}
              className="text-red-600 hover:text-red-800 font-medium"
            >
              Retry
            </button>
          </div>
        )}

        {/* Stats Cards */}
        <div className="grid grid-cols-1 md:grid-cols-4 gap-6 mb-8">
          <div className="bg-white p-6 rounded-lg shadow">
            <div className="flex items-center">
              <div className="flex-shrink-0">
                <div className="w-8 h-8 bg-blue-500 rounded-full flex items-center justify-center">
                  <span className="text-white text-sm font-bold">#</span>
                </div>
              </div>
              <div className="ml-4">
                <p className="text-sm font-medium text-gray-500">Total Stocks</p>
                <p className="text-2xl font-semibold text-gray-900">{statsData.totalStocks}</p>
              </div>
            </div>
          </div>

          <div className="bg-white p-6 rounded-lg shadow">
            <div className="flex items-center">
              <div className="flex-shrink-0">
                <div className="w-8 h-8 bg-green-500 rounded-full flex items-center justify-center">
                  <span className="text-white text-sm font-bold">+</span>
                </div>
              </div>
              <div className="ml-4">
                <p className="text-sm font-medium text-gray-500">Positive Predictions</p>
                <p className="text-2xl font-semibold text-gray-900">{statsData.positiveStocks}</p>
              </div>
            </div>
          </div>

          <div className="bg-white p-6 rounded-lg shadow">
            <div className="flex items-center">
              <div className="flex-shrink-0">
                <div className="w-8 h-8 bg-purple-500 rounded-full flex items-center justify-center">
                  <span className="text-white text-sm font-bold">★</span>
                </div>
              </div>
              <div className="ml-4">
                <p className="text-sm font-medium text-gray-500">High Confidence</p>
                <p className="text-2xl font-semibold text-gray-900">{statsData.highConfidenceStocks}</p>
              </div>
            </div>
          </div>

          <div className="bg-white p-6 rounded-lg shadow">
            <div className="flex items-center">
              <div className="flex-shrink-0">
                <div className="w-8 h-8 bg-orange-500 rounded-full flex items-center justify-center">
                  <span className="text-white text-sm font-bold">%</span>
                </div>
              </div>
              <div className="ml-4">
                <p className="text-sm font-medium text-gray-500">Avg Confidence</p>
                <p className="text-2xl font-semibold text-gray-900">{statsData.avgConfidence}</p>
              </div>
            </div>
          </div>
        </div>

        {/* Filters and Chart */}
        <div className="grid grid-cols-1 lg:grid-cols-3 gap-8 mb-8">
          <div className="lg:col-span-1">
            <FilterPanel 
              filters={filters}
              onFilterChange={handleFilterChange}
            />
          </div>
          <div className="lg:col-span-2">
            <StockChart 
              predictions={filteredAndSortedPredictions}
              accuracy={accuracy}
            />
          </div>
        </div>

        {/* Predictions Table */}
        <PredictionTable 
          predictions={filteredAndSortedPredictions}
          accuracy={accuracy}
          loading={loading}
        />
      </main>
    </div>
  );
};

export default Dashboard;