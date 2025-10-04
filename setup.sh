#!/bin/bash
set -e

echo "Starting Stock-ML Pipeline Setup..."

# Create data directory if it doesn't exist
mkdir -p data

# Check if virtual environment exists, create if not
if [ ! -d ".venv" ]; then
    echo "Creating virtual environment..."
    python3 -m venv .venv
fi

# Activate virtual environment
echo "Activating virtual environment..."
source .venv/bin/activate

# Install dependencies
echo "Installing dependencies..."
pip install -r requirements.txt

# Run initial pipeline to populate data
echo "Running initial data pipeline..."
python pipeline/build_universe.py
python pipeline/collect_prices_nse.py
python pipeline/collect_news.py
python pipeline/build_features.py
python pipeline/train_model.py
python pipeline/predict.py
python pipeline/evaluate_and_explain.py

echo "Pipeline setup complete!"
echo "To start the API server: uvicorn app.serve:app --host 0.0.0.0 --port 8000"
echo "To start the scheduler: python pipeline/scheduler.py"