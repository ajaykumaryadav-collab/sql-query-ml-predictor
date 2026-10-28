import os
import sys
import time
import json
import random
import logging
import argparse
from pathlib import Path
from typing import Iterator

import pandas as pd
import numpy as np
from sqlalchemy import create_engine, text
from sklearn.model_selection import train_test_split
from sklearn.linear_model import LinearRegression
from sklearn.ensemble import HistGradientBoostingRegressor, RandomForestRegressor
from sklearn.metrics import mean_absolute_error, mean_squared_error, r2_score
try:
    from sklearn.metrics import root_mean_squared_error
except ImportError:
    def root_mean_squared_error(y_true, y_pred):
        return float(np.sqrt(mean_squared_error(y_true, y_pred)))
import joblib

try:
    from xgboost import XGBRegressor
    HAS_XGBOOST = True
except ImportError:
    HAS_XGBOOST = False

from app.services.feature_extractor import extract_features_from_plan
from app.config import settings

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S"
)
logger = logging.getLogger(__name__)

# Base paths
BASE_DIR = Path(__file__).resolve().parent.parent.parent
DATASETS_DIR = BASE_DIR / "datasets"
MODELS_DIR = BASE_DIR / "trained_models"
DEFAULT_DATASET_PATH = DATASETS_DIR / "dataset_v3_balanced.csv"
MODEL_PATH = MODELS_DIR / "best_model.joblib"
METRICS_PATH = MODELS_DIR / "metrics.json"
LOG_FILE_PATH = DATASETS_DIR / "training_deep.log"

DATASETS_DIR.mkdir(parents=True, exist_ok=True)
try:
    file_handler = logging.FileHandler(LOG_FILE_PATH, encoding="utf-8")
    file_handler.setFormatter(logging.Formatter("%(asctime)s [%(levelname)s] %(message)s", "%Y-%m-%d %H:%M:%S"))
    logger.addHandler(file_handler)
except Exception:
    pass

FEATURE_COLUMNS = [
    "startup_cost", "total_cost", "plan_rows", "plan_width",
    "parallel_aware", "plan_depth", "number_of_plan_nodes",
    "number_of_tables", "number_of_joins", "number_of_filters",
    "number_of_sort_nodes", "number_of_aggregate_nodes",
    "number_of_seq_scans", "number_of_index_scans",
    "number_of_nested_loop_joins", "number_of_hash_joins",
    "number_of_merge_joins",
    "total_scanned_rows", "max_intermediate_rows", "total_tree_cost",
    "has_hash_join", "has_bitmap_scan", "number_of_bitmap_scans",
    "max_plan_width", "has_limit", "number_of_limit_nodes",
    "has_materialize", "output_to_scanned_ratio", "is_unbounded_scan"
]
TARGET_COLUMN = "actual_execution_time"

CITIES = ['New York', 'Los Angeles', 'Chicago', 'Houston', 'Phoenix', 'Philadelphia', 'San Antonio']
CATEGORIES = ['Electronics', 'Clothing', 'Books', 'Home', 'Toys']
STATUSES = ['PENDING', 'CANCELLED', 'COMPLETED']
PAYMENT_METHODS = ['CREDIT_CARD', 'PAYPAL', 'BANK_TRANSFER']


def generate_queries_stream(total_count: int, seed: int = 42) -> Iterator[str]:
    """
    Bounded generator yielding diverse SQL queries covering all major database execution archetypes.
    """
    rng = random.Random(seed)
    
    for _ in range(total_count):
        archetype = rng.randint(1, 8)
        
        if archetype == 1:
            # 1. Point lookups (Primary Key & Unique Indexes)
            sub = rng.randint(1, 4)
            if sub == 1:
                yield f"SELECT * FROM customers WHERE id = {rng.randint(1, 50000)}"
            elif sub == 2:
                yield f"SELECT * FROM products WHERE id = {rng.randint(1, 1000)}"
            elif sub == 3:
                yield f"SELECT * FROM orders WHERE id = {rng.randint(1, 200000)}"
            else:
                cust_num = rng.randint(1, 50000)
                yield f"SELECT * FROM customers WHERE email = 'customer{cust_num}@example.com'"
                
        elif archetype == 2:
            # 2. Filter & Range Scans (Index Scans vs Sequential Scans)
            sub = rng.randint(1, 6)
            limit = rng.choice([10, 50, 100, 200, 500])
            if sub == 1:
                city = rng.choice(CITIES)
                yield f"SELECT * FROM customers WHERE city = '{city}' LIMIT {limit}"
            elif sub == 2:
                stock_val = rng.randint(5, 450)
                yield f"SELECT * FROM products WHERE stock < {stock_val}"
            elif sub == 3:
                p1 = rng.randint(10, 300)
                p2 = p1 + rng.randint(50, 400)
                cat = rng.choice(CATEGORIES)
                yield f"SELECT * FROM products WHERE price BETWEEN {p1} AND {p2} AND category = '{cat}'"
            elif sub == 4:
                amt = rng.randint(50, 4000)
                status = rng.choice(STATUSES)
                yield f"SELECT * FROM orders WHERE total_amount > {amt} AND status = '{status}' LIMIT {limit}"
            elif sub == 5:
                cid = rng.randint(1, 50000)
                yield f"SELECT * FROM orders WHERE customer_id = {cid}"
            else:
                amt = rng.randint(100, 3000)
                method = rng.choice(PAYMENT_METHODS)
                yield f"SELECT * FROM payments WHERE method = '{method}' AND amount > {amt} LIMIT {limit}"

        elif archetype == 3:
            # 3. Two-Table Joins (Hash Join, Nested Loop, Merge Join)
            sub = rng.randint(1, 4)
            limit = rng.choice([25, 50, 100, 250, 500])
            if sub == 1:
                amt = rng.randint(100, 3500)
                yield f"SELECT c.name, c.city, o.id, o.total_amount FROM customers c JOIN orders o ON c.id = o.customer_id WHERE o.total_amount > {amt} LIMIT {limit}"
            elif sub == 2:
                city = rng.choice(CITIES)
                status = rng.choice(STATUSES)
                yield f"SELECT c.name, o.order_date, o.status FROM customers c JOIN orders o ON c.id = o.customer_id WHERE c.city = '{city}' AND o.status = '{status}' LIMIT {limit}"
            elif sub == 3:
                cat = rng.choice(CATEGORIES)
                yield f"SELECT p.name, p.category, oi.quantity, oi.price FROM products p JOIN order_items oi ON p.id = oi.product_id WHERE p.category = '{cat}' LIMIT {limit}"
            else:
                method = rng.choice(PAYMENT_METHODS)
                yield f"SELECT o.id, o.total_amount, pay.amount, pay.method FROM orders o JOIN payments pay ON o.id = pay.order_id WHERE pay.method = '{method}' LIMIT {limit}"

        elif archetype == 4:
            # 4. Multi-Table Joins (3, 4, and 5 tables)
            sub = rng.randint(1, 4)
            limit = rng.choice([20, 50, 100, 200])
            if sub == 1:
                cid = rng.randint(1, 50000)
                yield f"SELECT c.name, o.id, oi.quantity, p.name FROM customers c JOIN orders o ON c.id = o.customer_id JOIN order_items oi ON o.id = oi.order_id JOIN products p ON oi.product_id = p.id WHERE c.id = {cid}"
            elif sub == 2:
                cat = rng.choice(CATEGORIES)
                amt = rng.randint(200, 3000)
                yield f"SELECT c.city, o.total_amount, p.name, oi.price FROM customers c JOIN orders o ON c.id = o.customer_id JOIN order_items oi ON o.id = oi.order_id JOIN products p ON oi.product_id = p.id WHERE p.category = '{cat}' AND o.total_amount > {amt} LIMIT {limit}"
            elif sub == 3:
                city = rng.choice(CITIES)
                amt = rng.randint(100, 2000)
                yield f"SELECT c.name, o.id, pay.amount, pay.method FROM customers c JOIN orders o ON c.id = o.customer_id JOIN payments pay ON o.id = pay.order_id WHERE c.city = '{city}' AND pay.amount > {amt} LIMIT {limit}"
            else:
                oid = rng.randint(1, 200000)
                yield f"SELECT c.name, o.id, oi.quantity, p.name, pay.method FROM customers c JOIN orders o ON c.id = o.customer_id JOIN order_items oi ON o.id = oi.order_id JOIN products p ON oi.product_id = p.id JOIN payments pay ON o.id = pay.order_id WHERE o.id = {oid}"

        elif archetype == 5:
            # 5. Aggregations, Grouping & Having (HashAggregate, GroupAggregate)
            sub = rng.randint(1, 5)
            if sub == 1:
                yield "SELECT category, COUNT(*), AVG(price), MIN(price), MAX(price) FROM products GROUP BY category"
            elif sub == 2:
                yield "SELECT status, COUNT(*), SUM(total_amount), AVG(total_amount) FROM orders GROUP BY status"
            elif sub == 3:
                yield "SELECT c.city, COUNT(c.id) as cust_cnt, SUM(o.total_amount) as total_rev FROM customers c JOIN orders o ON c.id = o.customer_id GROUP BY c.city"
            elif sub == 4:
                amt = rng.randint(1000, 15000)
                lim = rng.choice([10, 25, 50])
                yield f"SELECT customer_id, COUNT(id) as total_orders, SUM(total_amount) as total_spent FROM orders GROUP BY customer_id HAVING SUM(total_amount) > {amt} LIMIT {lim}"
            else:
                yield "SELECT EXTRACT(MONTH FROM order_date) as m, COUNT(id), AVG(total_amount) FROM orders GROUP BY EXTRACT(MONTH FROM order_date)"

        elif archetype == 6:
            # 6. Sorting & Top-N Limits
            sub = rng.randint(1, 4)
            limit = rng.choice([10, 25, 50, 100])
            if sub == 1:
                yield f"SELECT * FROM orders ORDER BY total_amount DESC LIMIT {limit}"
            elif sub == 2:
                yield f"SELECT * FROM customers ORDER BY created_at ASC LIMIT {limit}"
            elif sub == 3:
                yield f"SELECT c.name, SUM(o.total_amount) as total FROM customers c JOIN orders o ON c.id = o.customer_id GROUP BY c.name ORDER BY total DESC LIMIT {limit}"
            else:
                yield f"SELECT * FROM payments p JOIN orders o ON p.order_id = o.id ORDER BY p.amount DESC, o.order_date ASC LIMIT {limit}"

        elif archetype == 7:
            # 7. Date Intervals, Joins & Aggregations (like the user query)
            days = rng.choice([7, 14, 30, 60, 90, 180, 365])
            sub = rng.randint(1, 3)
            if sub == 1:
                yield f"SELECT c.city, COUNT(o.id) AS total_orders, SUM(o.total_amount) AS revenue FROM customers c JOIN orders o ON c.id = o.customer_id WHERE o.order_date >= CURRENT_DATE - INTERVAL '{days} days' GROUP BY c.city ORDER BY revenue DESC"
            elif sub == 2:
                yield f"SELECT p.category, COUNT(oi.id) AS items_sold, SUM(oi.price * oi.quantity) AS sales FROM products p JOIN order_items oi ON p.id = oi.product_id JOIN orders o ON oi.order_id = o.id WHERE o.order_date >= CURRENT_DATE - INTERVAL '{days} days' GROUP BY p.category ORDER BY sales DESC"
            else:
                yield f"SELECT c.name, COUNT(o.id) as orders_count FROM customers c JOIN orders o ON c.id = o.customer_id WHERE o.order_date >= CURRENT_DATE - INTERVAL '{days} days' GROUP BY c.name ORDER BY orders_count DESC LIMIT 25"

        else:
            # 8. Subqueries and CTEs
            sub = rng.randint(1, 4)
            limit = rng.choice([25, 50, 100])
            if sub == 1:
                amt = rng.randint(2000, 10000)
                yield f"WITH top_cust AS (SELECT customer_id, SUM(total_amount) as total FROM orders GROUP BY customer_id HAVING SUM(total_amount) > {amt}) SELECT c.name, c.city, tc.total FROM customers c JOIN top_cust tc ON c.id = tc.customer_id LIMIT {limit}"
            elif sub == 2:
                cat = rng.choice(CATEGORIES)
                yield f"SELECT * FROM products WHERE price > (SELECT AVG(price) FROM products WHERE category = '{cat}') LIMIT {limit}"
            elif sub == 3:
                amt = rng.randint(3000, 5000)
                yield f"SELECT c.name, c.email FROM customers c WHERE c.id IN (SELECT o.customer_id FROM orders o WHERE o.total_amount > {amt}) LIMIT {limit}"
            else:
                qty = rng.randint(2, 5)
                yield f"SELECT * FROM order_items WHERE price > (SELECT AVG(price) FROM order_items) AND quantity >= {qty} LIMIT {limit}"


def count_existing_rows(csv_path: Path) -> int:
    """Fast line count of existing CSV dataset."""
    if not csv_path.exists():
        return 0
    try:
        with open(csv_path, "r", encoding="utf-8") as f:
            count = sum(1 for _ in f)
        return max(0, count - 1)
    except Exception:
        return 0


def gather_data_stream(
    engine,
    target_samples: int,
    csv_path: Path,
    batch_size: int = 1000,
    resume: bool = True
) -> int:
    """
    Executes queries against PostgreSQL using single-pass EXPLAIN ANALYZE.
    Extracts deep features (including scanned rows, intermediate tables, costs)
    and flushes batches directly to disk to prevent RAM bloat.
    """
    csv_path.parent.mkdir(parents=True, exist_ok=True)
    
    existing_count = count_existing_rows(csv_path) if resume else 0
    if existing_count >= target_samples:
        logger.info(f"Dataset at {csv_path} already contains {existing_count:,} samples (target: {target_samples:,}). Skipping gathering.")
        return existing_count
        
    remaining = target_samples - existing_count
    logger.info(f"Starting deep-feature data collection:")
    logger.info(f"  - Target samples: {target_samples:,}")
    logger.info(f"  - Existing samples: {existing_count:,}")
    logger.info(f"  - Remaining to gather: {remaining:,}")
    logger.info(f"  - Output file: {csv_path}")
    logger.info(f"  - Features: {len(FEATURE_COLUMNS)} deep plan metrics")
    logger.info(f"  - Batch flush interval: every {batch_size:,} queries")
    
    query_stream = generate_queries_stream(remaining, seed=existing_count + 1337)
    
    batch = []
    total_gathered = existing_count
    collected_in_run = 0
    start_time = time.time()
    
    file_exists = csv_path.exists() and (existing_count > 0)
    
    with engine.connect() as conn:
        for query in query_stream:
            try:
                raw_result = conn.execute(text(f"EXPLAIN (ANALYZE, BUFFERS, FORMAT JSON) {query}")).scalar()
                
                if isinstance(raw_result, str):
                    plan_data = json.loads(raw_result)
                else:
                    plan_data = raw_result
                    
                plan = plan_data[0].get("Plan", {}) if plan_data else {}
                if not plan:
                    continue
                    
                features = extract_features_from_plan(plan)
                features[TARGET_COLUMN] = float(plan.get("Actual Total Time", 0.0))
                batch.append(features)
                total_gathered += 1
                collected_in_run += 1
                
                if len(batch) >= batch_size:
                    df_batch = pd.DataFrame(batch)
                    df_batch.to_csv(csv_path, mode="a", header=not file_exists, index=False)
                    file_exists = True
                    batch.clear()
                    
                    elapsed = time.time() - start_time
                    speed = collected_in_run / elapsed if elapsed > 0 else 0.0
                    left_to_collect = target_samples - total_gathered
                    eta_sec = left_to_collect / speed if speed > 0 else 0.0
                    
                    eta_formatted = time.strftime("%H:%M:%S", time.gmtime(eta_sec))
                    elapsed_formatted = time.strftime("%H:%M:%S", time.gmtime(elapsed))
                    pct = (total_gathered / target_samples) * 100.0
                    
                    logger.info(
                        f"[{total_gathered:,} / {target_samples:,} ({pct:.1f}%)] "
                        f"Speed: {speed:.1f} q/s | Elapsed: {elapsed_formatted} | ETA: {eta_formatted} | Saved batch to CSV"
                    )
                    
            except Exception as e:
                continue
                
        # Flush remainder
        if batch:
            df_batch = pd.DataFrame(batch)
            df_batch.to_csv(csv_path, mode="a", header=not file_exists, index=False)
            batch.clear()
            
    total_elapsed = time.time() - start_time
    logger.info(f"Data collection completed: {total_gathered:,} total samples recorded in {total_elapsed:.1f}s.")
    return total_gathered


def mean_absolute_percentage_error(y_true, y_pred):
    y_t = np.array(y_true, dtype=float)
    y_p = np.array(y_pred, dtype=float)
    # Floor denominator at 1.0 ms to avoid artificial explosion from microsecond noise
    effective_base = np.maximum(y_t, 1.0)
    return float(np.mean(np.abs(y_t - y_p) / effective_base) * 100.0)


def train_models_from_csv(csv_path: Path):
    """
    Trains scalable regressors in log-space (log1p) on the deep-feature dataset.
    Log-space training optimizes relative percentage error equally across small and large queries.
    """
    if not csv_path.exists():
        raise FileNotFoundError(f"Dataset file not found at {csv_path}")
        
    logger.info(f"Loading deep-feature training dataset from {csv_path}...")
    df = pd.read_csv(csv_path)
    logger.info(f"Loaded {len(df):,} samples.")
    
    if len(df) < 20:
        logger.warning("Dataset is too small to train reliable models (< 20 samples).")
        return
        
    # Ensure all feature columns exist
    for col in FEATURE_COLUMNS:
        if col not in df.columns:
            df[col] = 0.0
            
    X = df[FEATURE_COLUMNS]
    y = df[TARGET_COLUMN]
    
    X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2, random_state=42)
    logger.info(f"Dataset split: {len(X_train):,} training samples, {len(X_test):,} testing samples.")
    
    # Target log-transform: log(1 + y) ensures optimization focuses on percentage error
    y_train_log = np.log1p(y_train)
    
    models = {
        "Histogram Gradient Boosting": HistGradientBoostingRegressor(
            max_iter=180,
            learning_rate=0.07,
            min_samples_leaf=20,
            random_state=42
        ),
        "Random Forest": RandomForestRegressor(
            n_estimators=100,
            max_depth=18,
            n_jobs=-1,
            random_state=42
        )
    }
    
    if HAS_XGBOOST:
        models["XGBoost (Hist)"] = XGBRegressor(
            n_estimators=150,
            max_depth=8,
            learning_rate=0.07,
            tree_method="hist",
            n_jobs=-1,
            random_state=42
        )
        
    results = {}
    best_model_name = None
    best_model = None
    best_mae = float("inf")
    
    for name, model in models.items():
        logger.info(f"Fitting {name} in Log-Space...")
        t0 = time.time()
        model.fit(X_train, y_train_log)
        fit_time = time.time() - t0
        
        preds_log = model.predict(X_test)
        # Invert log transform back to actual execution time milliseconds
        preds = np.maximum(0.01, np.expm1(preds_log))
        
        mae = mean_absolute_error(y_test, preds)
        rmse = root_mean_squared_error(y_test, preds)
        r2 = r2_score(y_test, preds)
        mape = mean_absolute_percentage_error(y_test, preds)
        
        results[name] = {
            "MAE": round(mae, 4),
            "RMSE": round(rmse, 4),
            "R2": round(r2, 4),
            "MAPE": round(mape, 4),
            "FitTimeSec": round(fit_time, 2)
        }
        
        logger.info(f"  {name} -> MAE: {mae:.4f} ms | RMSE: {rmse:.4f} ms | R2: {r2:.4f} | MAPE: {mape:.2f}% | Fit Time: {fit_time:.2f}s")
        
        if mae < best_mae:
            best_mae = mae
            best_model_name = name
            best_model = model
            
    logger.info(f"Champion Model Selected: '{best_model_name}' (MAE: {best_mae:.4f} ms)")
    
    # Mark champion model as using log-target so PredictionService automatically calls np.expm1
    setattr(best_model, "_is_log_target", True)
    
    # Save best model
    MODELS_DIR.mkdir(parents=True, exist_ok=True)
    joblib.dump(best_model, MODEL_PATH)
    logger.info(f"Saved champion model to {MODEL_PATH}")
    
    # Save training metrics
    metrics = {
        "best_model": best_model_name,
        "is_log_target": True,
        "results": results,
        "total_dataset_samples": len(df),
        "training_samples": len(X_train),
        "testing_samples": len(X_test),
        "number_of_features": len(FEATURE_COLUMNS),
        "features": FEATURE_COLUMNS,
        "target_variable": TARGET_COLUMN,
        "trained_at": time.strftime("%Y-%m-%d %H:%M:%S")
    }
    with open(METRICS_PATH, "w", encoding="utf-8") as f:
        json.dump(metrics, f, indent=4)
    logger.info(f"Saved evaluation metrics to {METRICS_PATH}")


def print_status(csv_path: Path):
    rows = count_existing_rows(csv_path)
    print("\n" + "=" * 62)
    print("      SQL QUERY ML PREDICTOR - SYSTEM & TRAINING STATUS")
    print("=" * 62)
    print(f"Dataset File:       {csv_path}")
    print(f"Collected Samples:  {rows:,} / 1,000,000 ({rows / 1000000 * 100:.2f}%)")
    
    import glob
    is_running = False
    try:
        for f in glob.glob('/proc/[0-9]*/cmdline'):
            try:
                cmd = open(f, 'rb').read().decode('utf-8', errors='ignore').replace('\x00', ' ')
                if 'python -m app.ml.train' in cmd and '--status' not in cmd and os.getpid() != int(Path(f).parent.name):
                    is_running = True
                    break
            except Exception:
                pass
    except Exception:
        pass
        
    status_str = "ACTIVE (Query generation running in background)" if is_running else "IDLE (No active background collection)"
    print(f"Pipeline State:     {status_str}")
    
    if METRICS_PATH.exists():
        try:
            with open(METRICS_PATH, "r", encoding="utf-8") as f:
                metrics = json.load(f)
            print("-" * 62)
            print(f"Champion Model:     {metrics.get('best_model')}")
            print(f"Target Transform:   {'Log-Transformed (log1p)' if metrics.get('is_log_target') else 'Linear'}")
            print(f"Trained At:         {metrics.get('trained_at')}")
            print(f"Total Trained On:   {metrics.get('total_dataset_samples', 0):,} samples")
            print(f"Features:           {metrics.get('number_of_features', 0)} deep features")
            print("\nCandidate Models Performance:")
            for m_name, res in metrics.get("results", {}).items():
                print(f"  * {m_name:<28} | MAE: {res.get('MAE'):<7} ms | R2: {res.get('R2'):<6} | MAPE: {res.get('MAPE'):<7}%")
        except Exception as e:
            print(f"Metrics file error: {e}")
            
    print("=" * 62 + "\n")


def main():
    parser = argparse.ArgumentParser(description="SQL Execution Cost ML Training Pipeline")
    parser.add_argument("--samples", type=int, default=None, help="Target sample count")
    parser.add_argument("--batch-size", type=int, default=1000, help="Batch flush size for streaming CSV")
    parser.add_argument("--dataset-path", type=str, default=str(DEFAULT_DATASET_PATH), help="Path to CSV dataset")
    parser.add_argument("--resume", action="store_true", default=True, help="Resume from existing CSV samples")
    parser.add_argument("--no-resume", action="store_false", dest="resume", help="Overwrite existing dataset")
    parser.add_argument("--train-only", action="store_true", help="Skip data gathering and train ML models on existing dataset")
    parser.add_argument("--force", action="store_true", help="Force training even if model exists")
    parser.add_argument("--boot-check", action="store_true", help="Run boot check mode for container startup")
    parser.add_argument("--status", action="store_true", help="Print system status, progress, and model metrics")
    
    args = parser.parse_args()
    csv_path = Path(args.dataset_path)
    
    if args.status:
        print_status(csv_path)
        return
        
    is_docker_boot = (args.samples is None and not args.force and not args.train_only)
    if is_docker_boot or args.boot_check:
        if MODEL_PATH.exists():
            logger.info("=" * 65)
            logger.info("Trained model found at: trained_models/best_model.joblib")
            logger.info("Skipping container boot training so FastAPI starts immediately.")
            logger.info("=" * 65)
            return
        else:
            logger.info("No pre-trained model found. Running fast bootstrap training (1,000 samples)...")
            args.samples = 1000
            
    target_samples = args.samples if args.samples is not None else 25000
    
    if not args.train_only:
        engine = create_engine(settings.DATABASE_URL)
        gather_data_stream(
            engine=engine,
            target_samples=target_samples,
            csv_path=csv_path,
            batch_size=args.batch_size,
            resume=args.resume
        )
        
    train_models_from_csv(csv_path)


if __name__ == "__main__":
    main()
