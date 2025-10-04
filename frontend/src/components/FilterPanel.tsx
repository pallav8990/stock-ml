import React from 'react';
import { FilterOptions, StockSeries } from '../types';

interface FilterPanelProps {
  filters: FilterOptions;
  onFilterChange: (filters: Partial<FilterOptions>) => void;
}

const FilterPanel: React.FC<FilterPanelProps> = ({ filters, onFilterChange }) => {
  const seriesOptions: { value: StockSeries; label: string; description: string }[] = [
    { value: 'ALL', label: 'All Series', description: 'All stock types' },
    { value: 'EQ', label: 'Equity (EQ)', description: 'Regular equity shares' },
    { value: 'BE', label: 'Book Entry (BE)', description: 'Dematerialized securities' },
    { value: 'ETF', label: 'ETF', description: 'Exchange Traded Funds' },
    { value: 'MF', label: 'Mutual Funds', description: 'Mutual Fund units' },
    { value: 'GS', label: 'Govt Securities', description: 'Government bonds & bills' },
  ];

  const sortOptions = [
    { value: 'y_pred_conf', label: 'Confidence Score' },
    { value: 'y_pred', label: 'Prediction Value' },
    { value: 'ticker', label: 'Stock Symbol' },
  ];

  const limitOptions = [25, 50, 100, 250, 500];

  return (
    <div className="bg-white rounded-lg shadow p-6">
      <h3 className="text-lg font-semibold text-gray-900 mb-4">Filters</h3>
      
      {/* Stock Series Filter */}
      <div className="mb-6">
        <label className="block text-sm font-medium text-gray-700 mb-2">
          Stock Series
        </label>
        <select
          value={filters.series}
          onChange={(e) => onFilterChange({ series: e.target.value as StockSeries })}
          className="w-full p-2 border border-gray-300 rounded-md focus:ring-2 focus:ring-blue-500 focus:border-blue-500"
        >
          {seriesOptions.map((option) => (
            <option key={option.value} value={option.value}>
              {option.label}
            </option>
          ))}
        </select>
        <p className="text-xs text-gray-500 mt-1">
          {seriesOptions.find(o => o.value === filters.series)?.description}
        </p>
      </div>

      {/* Sort By */}
      <div className="mb-6">
        <label className="block text-sm font-medium text-gray-700 mb-2">
          Sort By
        </label>
        <select
          value={filters.sortBy}
          onChange={(e) => onFilterChange({ sortBy: e.target.value as any })}
          className="w-full p-2 border border-gray-300 rounded-md focus:ring-2 focus:ring-blue-500 focus:border-blue-500"
        >
          {sortOptions.map((option) => (
            <option key={option.value} value={option.value}>
              {option.label}
            </option>
          ))}
        </select>
      </div>

      {/* Sort Order */}
      <div className="mb-6">
        <label className="block text-sm font-medium text-gray-700 mb-2">
          Sort Order
        </label>
        <div className="flex space-x-4">
          <label className="flex items-center">
            <input
              type="radio"
              name="sortOrder"
              value="desc"
              checked={filters.sortOrder === 'desc'}
              onChange={(e) => onFilterChange({ sortOrder: e.target.value as 'asc' | 'desc' })}
              className="mr-2"
            />
            <span className="text-sm text-gray-700">Descending</span>
          </label>
          <label className="flex items-center">
            <input
              type="radio"
              name="sortOrder"
              value="asc"
              checked={filters.sortOrder === 'asc'}
              onChange={(e) => onFilterChange({ sortOrder: e.target.value as 'asc' | 'desc' })}
              className="mr-2"
            />
            <span className="text-sm text-gray-700">Ascending</span>
          </label>
        </div>
      </div>

      {/* Limit */}
      <div className="mb-6">
        <label className="block text-sm font-medium text-gray-700 mb-2">
          Display Limit
        </label>
        <select
          value={filters.limit}
          onChange={(e) => onFilterChange({ limit: Number(e.target.value) })}
          className="w-full p-2 border border-gray-300 rounded-md focus:ring-2 focus:ring-blue-500 focus:border-blue-500"
        >
          {limitOptions.map((limit) => (
            <option key={limit} value={limit}>
              {limit} stocks
            </option>
          ))}
        </select>
      </div>

      {/* Legend */}
      <div className="border-t pt-4">
        <h4 className="text-sm font-medium text-gray-700 mb-2">Legend</h4>
        <div className="space-y-2 text-xs text-gray-600">
          <div className="flex items-center">
            <div className="w-3 h-3 bg-green-500 rounded mr-2"></div>
            <span>Positive Prediction (Expected gain)</span>
          </div>
          <div className="flex items-center">
            <div className="w-3 h-3 bg-red-500 rounded mr-2"></div>
            <span>Negative Prediction (Expected loss)</span>
          </div>
          <div className="flex items-center">
            <div className="w-3 h-3 bg-blue-500 rounded mr-2"></div>
            <span>High Confidence (Score &gt; 30)</span>
          </div>
        </div>
      </div>
    </div>
  );
};

export default FilterPanel;