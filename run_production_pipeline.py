#!/usr/bin/env python3
"""
Production Pipeline Runner for Stock-ML
Executes complete pipeline with real NSE data where available
"""

import subprocess
import sys
import time
from datetime import datetime
from pathlib import Path

def run_command(description: str, command: list, critical: bool = True) -> bool:
    """Run a pipeline command with proper logging"""
    print(f"\n{'='*60}")
    print(f"🚀 {description}")
    print(f"{'='*60}")
    print(f"📝 Command: {' '.join(command)}")
    print(f"⏰ Started: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    
    try:
        start_time = time.time()
        result = subprocess.run(command, check=True, capture_output=True, text=True)
        duration = time.time() - start_time
        
        print(f"✅ SUCCESS ({duration:.1f}s)")
        if result.stdout:
            print("📊 Output:")
            print(result.stdout)
        
        return True
        
    except subprocess.CalledProcessError as e:
        duration = time.time() - start_time
        print(f"❌ FAILED ({duration:.1f}s)")
        print(f"Error: {e}")
        if e.stdout:
            print("📊 Stdout:")
            print(e.stdout)
        if e.stderr:
            print("📊 Stderr:")
            print(e.stderr)
        
        if critical:
            print(f"\n💥 CRITICAL FAILURE: {description}")
            print("🛑 Pipeline execution stopped")
            sys.exit(1)
        else:
            print(f"⚠️  Non-critical failure: {description}")
            print("▶️  Continuing pipeline execution")
            return False

def main():
    print("🚀 STOCK-ML PRODUCTION PIPELINE")
    print("=" * 80)
    print("🎯 Mode: Production with Real NSE Data")
    print("📅 Started:", datetime.now().strftime('%Y-%m-%d %H:%M:%S'))
    print("📁 Working Directory:", Path.cwd())
    
    # Ensure we're in the right directory
    if not Path("pipeline").exists():
        print("❌ Error: pipeline directory not found")
        print("📁 Please run from the stock-ml root directory")
        sys.exit(1)
    
    # Python executable path
    python_cmd = str(Path(".venv/bin/python").absolute())
    
    # Pipeline steps
    pipeline_steps = [
        {
            "name": "Universe Building",
            "desc": "Building NSE universe with real equity data",
            "cmd": [python_cmd, "pipeline/build_universe.py"],
            "critical": True
        },
        {
            "name": "Price Collection", 
            "desc": "Collecting price data (real NSE or enhanced mock)",
            "cmd": [python_cmd, "pipeline/collect_prices_nse.py"],
            "critical": True
        },
        {
            "name": "News Collection",
            "desc": "Collecting RSS news sentiment data",
            "cmd": [python_cmd, "pipeline/collect_news.py"], 
            "critical": True
        },
        {
            "name": "Feature Engineering",
            "desc": "Building technical indicators and features",
            "cmd": [python_cmd, "pipeline/build_features.py"],
            "critical": True
        },
        {
            "name": "Model Training",
            "desc": "Training LightGBM model with TimeSeriesSplit",
            "cmd": [python_cmd, "pipeline/train_model.py"],
            "critical": True
        },
        {
            "name": "Prediction Generation",
            "desc": "Generating next-day return predictions",
            "cmd": [python_cmd, "pipeline/predict.py"],
            "critical": True
        },
        {
            "name": "Evaluation & Explanation",
            "desc": "Creating SHAP explanations and performance metrics",
            "cmd": [python_cmd, "pipeline/evaluate_and_explain.py"],
            "critical": True
        }
    ]
    
    # Execute pipeline
    success_count = 0
    total_start = time.time()
    
    for i, step in enumerate(pipeline_steps, 1):
        print(f"\n🎯 STEP {i}/{len(pipeline_steps)}: {step['name']}")
        success = run_command(
            step['desc'], 
            step['cmd'], 
            step['critical']
        )
        if success:
            success_count += 1
    
    total_duration = time.time() - total_start
    
    # Final summary
    print(f"\n{'='*80}")
    print("🏁 PIPELINE EXECUTION COMPLETE")
    print(f"{'='*80}")
    print(f"✅ Successful steps: {success_count}/{len(pipeline_steps)}")
    print(f"⏱️  Total duration: {total_duration:.1f} seconds")
    print(f"📅 Completed: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    
    if success_count == len(pipeline_steps):
        print("🎉 ALL STEPS SUCCESSFUL - PRODUCTION READY!")
        print("\n📊 Generated Files:")
        data_files = [
            "data/universe.parquet",
            "data/prices_daily.parquet", 
            "data/news_daily.parquet",
            "data/features_daily.parquet",
            "data/model.joblib",
            "data/predictions_daily.parquet",
            "data/eval_explain_daily.parquet"
        ]
        
        for file_path in data_files:
            if Path(file_path).exists():
                size_kb = Path(file_path).stat().st_size / 1024
                print(f"  ✅ {file_path} ({size_kb:.1f} KB)")
            else:
                print(f"  ❌ {file_path} (missing)")
        
        print("\n🚀 Ready to start API server!")
        print("Run: uvicorn app.serve:app --host 0.0.0.0 --port 8000")
        
    else:
        print("⚠️  Some steps failed - check logs above")
        sys.exit(1)

if __name__ == "__main__":
    main()