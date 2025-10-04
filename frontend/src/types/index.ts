export interface StockPrediction {
  ticker: string;
  date: string;
  series: string;
  y_pred: number;
  y_pred_conf: number;
  prediction_rank?: number;
}

export interface StockAccuracy {
  ticker: string;
  mae: number;
  rmse: number;
  directional_accuracy: number;
  abs_gap: number;
  signed_gap: number;
}

export interface ApiResponse<T> {
  data: T;
  status: string;
  message?: string;
}

export interface User {
  email: string;
  name: string;
  picture: string;
  sub: string;
}

export interface AuthContextType {
  user: User | null;
  isLoading: boolean;
  login: () => void;
  logout: () => void;
  handleLoginSuccess: (userData: User) => void;
}

export type StockSeries = 'EQ' | 'BE' | 'MF' | 'ETF' | 'GS' | 'ALL';

export interface FilterOptions {
  series: StockSeries;
  sortBy: 'y_pred' | 'y_pred_conf' | 'ticker';
  sortOrder: 'asc' | 'desc';
  limit: number;
}