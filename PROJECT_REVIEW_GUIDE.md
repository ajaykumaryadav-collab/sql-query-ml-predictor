# PROJECT REVIEW & VIVA GUIDE
## SQL Query Performance & Cost Prediction Using Machine Learning

This document contains everything you need to explain your project successfully, including how it works, architectural decisions, and potential viva (oral exam) questions and answers.

---

### 1. PROJECT CONCEPT
Traditional databases (like PostgreSQL) use built-in mathematical formulas to estimate the "cost" of executing a query. However, these native estimators can be inaccurate for highly complex queries. 

This project explores an alternative approach: **Can a Machine Learning model predict actual query execution time more accurately than a database's native cost estimator?** 

We do this by extracting structural features from the database's execution plan (number of joins, expected rows, scan types) and passing them into a trained ML regression model to predict the final execution time in milliseconds.

---

### 2. ARCHITECTURE & TECH STACK
The project is built as a modern, microservice-based Web Application running in Docker.
* **Database (PostgreSQL):** Stores the synthetic e-commerce data (Customers, Orders, Products). It is responsible for generating the query execution plans via the `EXPLAIN` command.
* **Backend (Python / FastAPI / scikit-learn):** The brain of the operation. It handles security (blocking non-SELECT queries), communicates with the database to get the execution plan, extracts ML features from the JSON plan tree, and runs the Machine Learning model.
* **Frontend (React / Vite / TailwindCSS):** A sleek User Interface allowing the user to type SQL, view the execution plan visually (React Flow), and compare the ML predicted time vs the actual execution time.

---

### 3. HOW THE PIPELINE WORKS (Step-by-Step)
1. **Input:** The user types a SQL query into the frontend editor.
2. **Validation:** The backend checks the query to ensure it only starts with `SELECT` or `WITH`. Destructive queries (`DROP`, `DELETE`, `INSERT`) are blocked.
3. **Plan Extraction:** The backend sends the query to PostgreSQL wrapped in `EXPLAIN (ANALYZE, FORMAT JSON)`. 
4. **Feature Engineering:** PostgreSQL returns a deeply nested JSON tree representing how it plans to execute the query. Our `feature_extractor.py` recursively flattens this tree, counting features like:
   - Total number of nodes
   - Number of Hash Joins, Merge Joins, and Nested Loops
   - Number of Sequential Scans vs. Index Scans
   - The native "Total Cost" estimated by Postgres
5. **ML Prediction:** These extracted numbers are fed into our pre-trained **Random Forest Regressor**, which outputs a predicted time in milliseconds.
6. **Result:** The frontend dynamically groups the results into 4 logical sections:
   - **PostgreSQL Estimate:** The native Cost and Estimated Rows.
   - **ML Prediction:** The Predicted Execution Time and Preliminary Performance Category.
   - **Actual Execution:** The real ms time and Error percentage (if EXPLAIN ANALYZE was clicked).
   - **Query Features:** A summary of the extracted nodes, joins, and scans.

---

### 4. QUERY PLAN VISUALIZATION
The application includes a highly interactive React Flow canvas that visually maps out the PostgreSQL JSON execution plan tree.
* **Nodes:** Each box represents a distinct step in the database's execution strategy (e.g., `Hash Join`, `Seq Scan`, `Aggregate`).
* **Metrics:** Inside each node, we display the `Node Type`, `Estimated Cost`, `Estimated Rows`, and (if executed) the `Actual Total Time`.
* **Flow:** Arrows trace the flow of data from the initial table scans at the bottom, up through the joins and aggregations, to the final output node at the top. This allows you to visually prove to the reviewer that the ML model is receiving deeply nested, authentic query strategies.

---

### 5. MACHINE LEARNING DETAILS
* **Model Used:** Random Forest Regressor
* **Why Random Forest?:** It is highly effective for structured, tabular data. It handles non-linear relationships well (e.g., query execution time doesn't scale perfectly linearly with row count), and it trains extremely fast compared to Deep Learning/Neural Networks.
* **Target Variable:** Actual Execution Time (in milliseconds).
* **Evaluation Metrics:** Mean Absolute Error (MAE), Root Mean Squared Error (RMSE), and R² Score.

---

### 5. CRITICAL CONCEPTS TO MENTION (Will impress your professor)

#### A. The "PostgreSQL Caching" Phenomenon
If you run a heavy query twice, the first run might take 200ms, but the second run takes 10ms. Why? Because PostgreSQL caches the data in its RAM (Shared Buffers) after the first run. 
*Our ML model only looks at the query structure, so it predicts the exact same time for both runs.* This causes the error percentage to fluctuate when you hit refresh. **This is a known limitation of stateless ML models: they do not account for the live memory state of the database server.**

#### B. The "Percentage Error Near Zero" Problem
If a trivial query (`SELECT * FROM customers LIMIT 10`) takes 0.01 ms to run, and our ML model predicts 0.10 ms, the percentage error is technically **900%**. However, the absolute error is only **0.09 milliseconds**. You should explain that for instant queries, percentage errors are mathematically useless, and we should look at absolute error (MAE) instead.

---

### 6. COMMON VIVA QUESTIONS & ANSWERS

**Q1: Why do we need Machine Learning for this when PostgreSQL already has a built-in cost estimator?**
**Answer:** Postgres's native cost estimator uses static mathematical formulas and statistics. While good for simple queries, it can make poor assumptions on complex, multi-join queries (e.g., underestimating how many rows a filter will return). Machine Learning can learn from historical, real-world execution times on your specific hardware, potentially finding complex patterns that static math misses.

**Q2: What exact features did you extract from the query to feed into the ML model?**
**Answer:** I extracted structural data from the Postgres JSON plan. This includes the total native cost, estimated plan rows, plan width, and categorical counts (how many sequential scans, how many index scans, how many sorts, and what types of joins were used). 

**Q3: Why did you choose Random Forest instead of a Neural Network?**
**Answer:** For this dataset, we are dealing with structured, tabular numeric features. Neural Networks require massive amounts of data and compute time to outperform traditional algorithms on tabular data. Random Forest is highly interpretable, trains almost instantly, and captures non-linear relationships perfectly for this use case.

**Q4: How do you prevent SQL Injection or destructive queries from ruining the database?**
**Answer:** I implemented a strict validation layer in the FastAPI backend. Before the query is sent to the database, the system uses regular expressions to verify it only contains `SELECT` or `WITH` statements. Anything containing `DROP`, `UPDATE`, `INSERT`, or `DELETE` is immediately rejected.

**Q5: I noticed the ML prediction error is quite high on some queries. Does that mean the model failed?**
**Answer:** Not necessarily. High percentage errors occur for two main reasons. First, for queries that take less than 1 millisecond, a tiny miscalculation results in a massive percentage error (e.g., guessing 0.5ms instead of 0.1ms is a 400% error). Second, because of database caching, a query might execute 10x faster the second time it is run. Since our ML model doesn't track live RAM usage, it predicts the "cold cache" time, making it look wrong when it's actually just predicting an uncached execution.
