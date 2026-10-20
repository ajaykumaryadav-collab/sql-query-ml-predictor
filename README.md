# SQL Query ML Predictor

An ML-based SQL query execution-time prediction system that uses PostgreSQL query-plan features and compares predicted performance with actual execution performance.

## Problem
Native database cost estimators rely on static mathematical formulas. While fast, they can sometimes inaccurately estimate the cost of highly complex queries involving multiple joins, subqueries, and massive aggregations, as they cannot perfectly predict intermediate row counts or hardware-specific latency.

## Objectives
- Build a preliminary system that bridges database internals (Query Execution Plans) with Machine Learning.
- Extract structural features from a `EXPLAIN` JSON output.
- Train a regression model to predict actual query execution time.
- Provide a user-friendly UI to compare the ML predictions with the database's native estimates.

## Architecture
- **Frontend**: React, Vite, Tailwind CSS, React Flow (for plan visualization).
- **Backend**: FastAPI (Python), SQLAlchemy, scikit-learn.
- **Database**: PostgreSQL (Containerized via Docker).

## Methodology
1. A user submits a SQL `SELECT` query.
2. The system executes `EXPLAIN (FORMAT JSON)` (and optionally `EXPLAIN ANALYZE`) against PostgreSQL.
3. The resulting JSON plan tree is flattened into a one-dimensional array of numerical features.
4. The features are fed into a pre-trained ML model.
5. The predicted execution time (in ms) is presented to the user alongside the abstract PostgreSQL Estimated Cost.

## Feature Extraction
The system recursively parses the PostgreSQL JSON plan tree to extract:
- `total_cost` (Native PostgreSQL abstract cost)
- `plan_rows` (Estimated rows)
- `plan_width` (Estimated width)
- `number_of_nodes` (Total complexity)
- `plan_depth` (Depth of the execution tree)
- Categorical counts: `number_of_joins`, `number_of_seq_scans`, `number_of_index_scans`, `number_of_sort_nodes`, `number_of_aggregate_nodes`, `number_of_nested_loop_joins`, `number_of_hash_joins`, `number_of_merge_joins`.

## ML Pipeline & Dataset Generation
During startup, the system generates synthetic queries with varying complexity against a seeded e-commerce database (Customers, Orders, Products, Order Items).
The `train.py` script automatically runs these queries with `EXPLAIN ANALYZE` to gather the actual execution times (the target variable) without data leakage (no post-execution metrics are used as input features). 
The dataset is then split 80/20 for training and testing.

## Models
The training pipeline evaluates multiple regression models on the extracted dataset:
- **Linear Regression**
- **Random Forest Regressor**
- **Gradient Boosting Regressor**
The best performing model is dynamically saved as a joblib artifact and loaded by the FastAPI backend for real-time predictions.

## Evaluation Metrics
Preliminary evaluation uses standard regression metrics:
- **MAE** (Mean Absolute Error)
- **RMSE** (Root Mean Squared Error)
- **R²** (Coefficient of Determination)
- **MAPE** (Mean Absolute Percentage Error)

## Security
The application strictly validates SQL queries to prevent destructive operations. Only `SELECT` and `WITH` statements are allowed. Modifying queries (`INSERT`, `UPDATE`, `DELETE`, etc.) are actively blocked by the backend via regex and AST validation to ensure the safety of the demonstration database.

## Current Results
The current model performance is a **preliminary ML prediction**. Because the current dataset generated during startup is extremely small to allow for rapid container booting, the predictions are structurally sound but mathematically unoptimized. The UI categorizes predictions into Expected Latency tiers (e.g., Predicted Performance: LOW) to distinguish between concrete ms predictions and general risk estimation.

## Limitations
- **Hardware Dependency**: Execution time depends heavily on the machine running the database. The model is specific to the hardware it was trained on.
- **Cache Effects**: PostgreSQL caches data in memory (buffer cache). The first execution of a query will be slower than subsequent executions. Stateless ML models struggle to account for live RAM buffer states.
- **Percentage Error Math**: For trivial queries executing in < 0.1ms, even a microsecond misprediction results in mathematically inflated percentage errors (e.g., 800%), even when absolute error is effectively zero.

## Future Work
Before the final review, we aim to:
- Generate a massively expanded dataset (10,000+ queries).
- Implement database cache clearing (`pg_dropcache`) between training queries to ensure consistent cold-cache baseline labels.
- Explore integrating Postgres memory state features into the model.
