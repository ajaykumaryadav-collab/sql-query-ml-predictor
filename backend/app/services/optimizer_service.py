import re
import json
import logging
from typing import Dict, Any, List, Optional
from sqlalchemy import text

logger = logging.getLogger(__name__)

class OptimizerService:
    """
    Automated Database Optimizer, Index Advisor & Query Rewriter.
    1. Detects bottlenecks and provides index tuning recommendations.
    2. Runs What-If index simulation inside isolated rollback transactions.
    3. Rewrites suboptimal SQL into high-performance queries with rule-based transformations.
    4. Projects cloud infrastructure compute costs ($) and buffer cache metrics.
    """

    LARGE_TABLE_THRESHOLDS = {
        "customers": 50000,
        "orders": 200000,
        "order_items": 500000,
        "products": 1000,
        "payments": 160000
    }

    EXISTING_INDEXES = {
        "customers": ["id", "city", "email"],
        "products": ["id", "category"],
        "orders": ["id", "customer_id", "order_date"],
        "order_items": ["id", "order_id", "product_id"],
        "payments": ["id", "order_id"]
    }

    TABLE_RECOMMENDED_COLS = {
        "customers": "c.id, c.name, c.city, c.email",
        "orders": "o.id AS order_id, o.order_date, o.total_amount, o.status",
        "order_items": "oi.product_id, oi.quantity, oi.price",
        "products": "p.id AS product_id, p.name AS product_name, p.category, p.price",
        "payments": "pay.id AS payment_id, pay.amount, pay.method"
    }

    def analyze(self, query: str, plan: Dict[str, Any], features: Dict[str, Any], actual_time_ms: float = None) -> Dict[str, Any]:
        recommendations = []
        bottlenecks = []
        anti_patterns = []
        
        total_time = actual_time_ms if actual_time_ms is not None else float(plan.get("Actual Total Time", 0.0))
        total_cost = float(plan.get("Total Cost", 1.0))

        # 1. Traverse plan to detect bottlenecks and scan operations
        def inspect_node(node):
            if not node:
                return
                
            node_type = node.get("Node Type", "")
            relation = node.get("Relation Name", "")
            node_cost = float(node.get("Total Cost", 0.0))
            node_time = float(node.get("Actual Total Time", 0.0)) if node.get("Actual Total Time") is not None else 0.0
            node_rows = float(node.get("Plan Rows", 0.0))
            
            time_pct = (node_time / total_time * 100.0) if total_time > 0 else (node_cost / total_cost * 100.0)
            if time_pct >= 20.0 or (node_type == "Seq Scan" and node_rows > 1000):
                bottlenecks.append({
                    "node_type": node_type,
                    "relation": relation or "Intermediate",
                    "cost": round(node_cost, 2),
                    "time_ms": round(node_time, 2),
                    "percentage_of_total": round(time_pct, 1),
                    "severity": "CRITICAL" if time_pct >= 50.0 else "WARNING"
                })

            if node_type == "Seq Scan" and relation:
                filter_cond = node.get("Filter", "") or ""
                recheck_cond = node.get("Recheck Cond", "") or ""
                combined_cond = f"{filter_cond} {recheck_cond}"
                
                cols = self._extract_columns_from_cond(combined_cond, relation)
                table_rows = self.LARGE_TABLE_THRESHOLDS.get(relation, 0)
                
                if cols and table_rows > 500:
                    for col in cols:
                        existing = self.EXISTING_INDEXES.get(relation, [])
                        if col not in existing:
                            index_name = f"idx_{relation}_{col}"
                            recommendations.append({
                                "type": "INDEX_RECOMMENDATION",
                                "severity": "HIGH",
                                "table": relation,
                                "column": col,
                                "sql": f"CREATE INDEX {index_name} ON {relation}({col});",
                                "description": f"Sequential scan on '{relation}' table ({table_rows:,} rows) filtered by '{col}'. Adding a B-Tree index will convert this to an Index Scan.",
                                "estimated_speedup": "5x – 15x faster"
                            })
                elif not cols and node_rows > 10000 and "Join" not in query:
                    recommendations.append({
                        "type": "QUERY_FILTER_RECOMMENDATION",
                        "severity": "MEDIUM",
                        "table": relation,
                        "sql": f"-- Consider adding WHERE clause to filter {relation}",
                        "description": f"Full table sequential scan on {table_rows:,} rows without predicate filters.",
                        "estimated_speedup": "Variable"
                    })

            for child in node.get("Plans", []):
                inspect_node(child)

        inspect_node(plan)

        # 2. Query Anti-Pattern Analysis
        query_upper = query.upper()
        if "SELECT *" in query_upper and ("JOIN" in query_upper or features.get("number_of_tables", 0) > 1):
            anti_patterns.append({
                "type": "SELECT_ALL_JOIN",
                "title": "Avoid 'SELECT *' in multi-table queries",
                "description": "Fetching all columns increases network payload, plan width, and prevents Index-Only scans. Explicitly list only needed columns."
            })
            
        est_sort_rows = max(features.get("total_scanned_rows", 0), features.get("plan_rows", 0), features.get("max_intermediate_rows", 0))
        if "ORDER BY" in query_upper and "LIMIT" not in query_upper and est_sort_rows > 5000:
            anti_patterns.append({
                "type": "UNBOUNDED_SORT",
                "title": "Unbounded ORDER BY Sort",
                "description": "Sorting thousands of rows without a LIMIT clause forces an in-memory or on-disk quicksort. Add LIMIT if only top results are displayed."
            })

        if "LIKE '%" in query:
            anti_patterns.append({
                "type": "LEADING_WILDCARD",
                "title": "Leading wildcard in LIKE clause",
                "description": "Pattern 'LIKE %...' prevents B-tree index lookup and forces full table scans. Use full-text search or pg_trgm trigram index instead."
            })

        # 3. Buffer Cache Metrics (RAM vs Disk I/O)
        shared_hit = float(plan.get("Shared Hit Blocks", 0.0))
        shared_read = float(plan.get("Shared Read Blocks", 0.0))
        total_blocks = shared_hit + shared_read
        hit_ratio = round((shared_hit / total_blocks * 100.0), 1) if total_blocks > 0 else 100.0

        cache_metrics = {
            "shared_hit_blocks": int(shared_hit),
            "shared_read_blocks": int(shared_read),
            "cache_hit_ratio_percent": hit_ratio,
            "storage_source": "RAM Buffer Cache (Fast)" if hit_ratio >= 90 else "Disk I/O / Hybrid (Higher Latency)"
        }

        # 4. Cloud Cost Estimation ($)
        effective_time = total_time if total_time > 0 else float(features.get("total_cost", 10.0)) * 0.01
        run_sec = effective_time / 1000.0
        
        daily_100k_runs = 100000
        monthly_hours = (run_sec * daily_100k_runs * 30.0) / 3600.0
        monthly_cost = round(monthly_hours * 0.0416, 2)
        annual_cost = round(monthly_cost * 12.0, 2)
        
        optimized_time_ms = min(effective_time, 4.0)
        optimized_run_sec = optimized_time_ms / 1000.0
        optimized_monthly = round(((optimized_run_sec * daily_100k_runs * 30.0) / 3600.0) * 0.0416, 2)
        potential_savings = max(0.0, round(monthly_cost - optimized_monthly, 2))

        cost_estimation = {
            "monthly_cloud_cost_100k_daily": monthly_cost,
            "annual_cloud_cost": annual_cost,
            "potential_monthly_savings": potential_savings,
            "savings_percentage": round((potential_savings / monthly_cost * 100.0), 1) if monthly_cost > 0 else 0.0
        }

        return {
            "recommendations": recommendations,
            "bottlenecks": bottlenecks,
            "anti_patterns": anti_patterns,
            "cache_metrics": cache_metrics,
            "cost_estimation": cost_estimation
        }

    def simulate_index(self, query: str, index_sql: str, engine) -> Dict[str, Any]:
        """
        Executes a safe What-If index simulation inside a database transaction.
        Creates the index, runs EXPLAIN ANALYZE, and rolls back immediately so production is unaffected.
        """
        clean_index_sql = index_sql.strip().rstrip(";")
        if not re.match(r"^CREATE\s+INDEX\s+[a-zA-Z0-9_]+\s+ON\s+[a-zA-Z0-9_]+\s*\(.+\)$", clean_index_sql, re.IGNORECASE):
            raise ValueError("Invalid index command. Must match: CREATE INDEX <name> ON <table>(<column>);")

        with engine.connect() as conn:
            # Baseline execution
            res_before = conn.execute(text(f"EXPLAIN (ANALYZE, BUFFERS, FORMAT JSON) {query}")).scalar()
            plan_before = res_before[0]["Plan"] if not isinstance(res_before, str) else json.loads(res_before)[0]["Plan"]
            
            before_time = float(plan_before.get("Actual Total Time", 0.0))
            before_cost = float(plan_before.get("Total Cost", 0.0))
            before_rows = float(plan_before.get("Plan Rows", 0.0))
            before_node = plan_before.get("Node Type", "Root")

            # Rollback autobegin transaction from baseline execution
            conn.rollback()

            # Transactional simulation
            trans = conn.begin()
            try:
                conn.execute(text(clean_index_sql))
                res_after = conn.execute(text(f"EXPLAIN (ANALYZE, BUFFERS, FORMAT JSON) {query}")).scalar()
                plan_after = res_after[0]["Plan"] if not isinstance(res_after, str) else json.loads(res_after)[0]["Plan"]
            finally:
                trans.rollback()

            after_time = float(plan_after.get("Actual Total Time", 0.0))
            after_cost = float(plan_after.get("Total Cost", 0.0))
            after_rows = float(plan_after.get("Plan Rows", 0.0))
            after_node = plan_after.get("Node Type", "Root")

            diff_ms = max(0.0, before_time - after_time)
            speedup = (before_time / after_time) if after_time > 0 else 1.0
            pct_drop = ((before_time - after_time) / before_time * 100.0) if before_time > 0 else 0.0

            return {
                "index_sql": clean_index_sql + ";",
                "before_time_ms": round(before_time, 2),
                "after_time_ms": round(after_time, 2),
                "before_cost": round(before_cost, 2),
                "after_cost": round(after_cost, 2),
                "before_rows": round(before_rows, 0),
                "after_rows": round(after_rows, 0),
                "speedup_ratio": f"{speedup:.1f}x",
                "time_saved_ms": round(diff_ms, 2),
                "percentage_drop": round(pct_drop, 1),
                "before_node_type": before_node,
                "after_node_type": after_node,
                "before_plan": plan_before,
                "after_plan": plan_after,
                "status": "success"
            }

    def rewrite_query(self, query: str, engine=None) -> Dict[str, Any]:
        """
        AI SQL Rewriter & Rule-Based Query Optimizer.
        Applies SQL transformations to eliminate anti-patterns and optimize query structure.
        """
        optimized = query.strip()
        improvements = []

        # 1. Convert IN (SELECT ...) subqueries to correlated EXISTS
        in_subquery_pattern = r"WHERE\s+([a-zA-Z0-9_\.]+)\s+IN\s*\(\s*SELECT\s+([a-zA-Z0-9_\.]+)\s+FROM\s+([a-zA-Z0-9_]+)(?:\s+([a-zA-Z0-9_]+))?\s+WHERE\s+(.+?)\s*\)"
        match = re.search(in_subquery_pattern, optimized, re.IGNORECASE | re.DOTALL)
        if match:
            col_outer, col_inner, table_inner, alias_inner, inner_cond = match.groups()
            alias = alias_inner if alias_inner else table_inner
            exists_clause = f"WHERE EXISTS (SELECT 1 FROM {table_inner} {alias if alias_inner else ''} WHERE {alias}.{col_inner} = {col_outer} AND {inner_cond})"
            optimized = re.sub(in_subquery_pattern, exists_clause, optimized, flags=re.IGNORECASE | re.DOTALL)
            improvements.append({
                "rule": "Subquery to EXISTS Conversion",
                "impact": "HIGH",
                "description": "Converted 'IN (SELECT ...)' to correlated 'EXISTS'. Eliminates subquery table materialization and enables early termination evaluation."
            })

        # 2. Optimize SELECT * in multi-table queries
        if re.search(r"SELECT\s+\*\s+FROM", optimized, re.IGNORECASE) and re.search(r"\bJOIN\b", optimized, re.IGNORECASE):
            selected_cols = []
            if "customers" in optimized.lower():
                selected_cols.append("c.id AS customer_id, c.name, c.city")
            if "orders" in optimized.lower():
                selected_cols.append("o.id AS order_id, o.order_date, o.total_amount, o.status")
            if "order_items" in optimized.lower():
                selected_cols.append("oi.product_id, oi.quantity, oi.price")
            if "products" in optimized.lower():
                selected_cols.append("p.id AS product_id, p.name AS product_name, p.category")
            if "payments" in optimized.lower():
                selected_cols.append("pay.amount AS payment_amount, pay.method")

            if selected_cols:
                replacement = "SELECT " + ", ".join(selected_cols) + " FROM"
                optimized = re.sub(r"SELECT\s+\*\s+FROM", replacement, optimized, count=1, flags=re.IGNORECASE)
                improvements.append({
                    "rule": "Explicit Column Projection",
                    "impact": "MEDIUM",
                    "description": "Replaced unbounded 'SELECT *' with explicit business columns. Reduces network packet transfer, prevents buffer cache bloat, and unlocks Index-Only Scans."
                })

        # 3. Add LIMIT to unbounded ORDER BY
        if re.search(r"ORDER\s+BY", optimized, re.IGNORECASE) and not re.search(r"LIMIT\s+\d+", optimized, re.IGNORECASE):
            optimized = optimized.rstrip(";") + "\nLIMIT 100;"
            improvements.append({
                "rule": "Bounded Top-N Sort",
                "impact": "HIGH",
                "description": "Appended 'LIMIT 100' to unbounded ORDER BY. Allows PostgreSQL to use an in-memory bounded Top-N Heap Sort instead of spilling large work_mem quicksorts to disk."
            })

        # 4. Remove redundant DISTINCT if already grouped
        if re.search(r"SELECT\s+DISTINCT", optimized, re.IGNORECASE) and re.search(r"GROUP\s+BY", optimized, re.IGNORECASE):
            optimized = re.sub(r"SELECT\s+DISTINCT", "SELECT", optimized, count=1, flags=re.IGNORECASE)
            improvements.append({
                "rule": "Redundant DISTINCT Elimination",
                "impact": "LOW",
                "description": "Removed redundant 'DISTINCT' keyword. The 'GROUP BY' clause already guarantees unique key groups, so removing DISTINCT eliminates an extra deduplication pass."
            })

        # Calculate estimated cost comparison if engine is provided
        orig_cost = None
        opt_cost = None
        speedup = None
        has_changes = (optimized.strip() != query.strip())

        if has_changes and engine:
            try:
                with engine.connect() as conn:
                    p1 = conn.execute(text(f"EXPLAIN (FORMAT JSON) {query}")).scalar()
                    p2 = conn.execute(text(f"EXPLAIN (FORMAT JSON) {optimized}")).scalar()
                    c1 = float(p1[0]["Plan"].get("Total Cost", 0.0))
                    c2 = float(p2[0]["Plan"].get("Total Cost", 0.0))
                    orig_cost = round(c1, 2)
                    opt_cost = round(c2, 2)
                    if c2 > 0 and c1 > c2:
                        speedup = f"{c1 / c2:.1f}x lower planner cost"
            except Exception as e:
                logger.warning(f"Cost comparison failed: {e}")

        return {
            "original_query": query,
            "optimized_query": optimized,
            "improvements": improvements,
            "has_changes": has_changes,
            "original_cost": orig_cost,
            "optimized_cost": opt_cost,
            "estimated_speedup": speedup
        }

    def _extract_columns_from_cond(self, cond: str, table: str) -> List[str]:
        tokens = re.findall(r'[a-zA-Z_][a-zA-Z0-9_]*', cond)
        known_cols = {
            "customers": ["id", "name", "city", "email", "created_at"],
            "orders": ["id", "customer_id", "order_date", "total_amount", "status"],
            "order_items": ["id", "order_id", "product_id", "quantity", "price"],
            "products": ["id", "name", "category", "price", "stock"],
            "payments": ["id", "order_id", "payment_date", "amount", "method"]
        }
        table_cols = known_cols.get(table, [])
        return [tok for tok in set(tokens) if tok.lower() in table_cols]

optimizer_service = OptimizerService()
