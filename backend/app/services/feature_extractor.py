def extract_features_from_plan(plan: dict) -> dict:
    """
    Extracts deep numerical features from a PostgreSQL query plan tree.
    Captures root cost estimates, child node data volume, execution modifiers (LIMIT),
    and table scan selectivity.
    """
    features = {
        # Root node estimates
        "startup_cost": float(plan.get("Startup Cost", 0.0)),
        "total_cost": float(plan.get("Total Cost", 0.0)),
        "plan_rows": float(plan.get("Plan Rows", 0.0)),
        "plan_width": float(plan.get("Plan Width", 0.0)),
        "parallel_aware": 1.0 if plan.get("Parallel Aware") else 0.0,
        "plan_depth": 0.0,
        "number_of_plan_nodes": 0.0,
        "number_of_tables": 0.0,
        "number_of_joins": 0.0,
        "number_of_filters": 0.0,
        "number_of_sort_nodes": 0.0,
        "number_of_aggregate_nodes": 0.0,
        "number_of_seq_scans": 0.0,
        "number_of_index_scans": 0.0,
        "number_of_nested_loop_joins": 0.0,
        "number_of_hash_joins": 0.0,
        "number_of_merge_joins": 0.0,
        
        # Deep Plan Tree & Data Volume Features
        "total_scanned_rows": 0.0,
        "max_intermediate_rows": float(plan.get("Plan Rows", 0.0)),
        "total_tree_cost": 0.0,
        "has_hash_join": 0.0,
        "has_bitmap_scan": 0.0,
        "number_of_bitmap_scans": 0.0,
        "max_plan_width": float(plan.get("Plan Width", 0.0)),
        
        # Execution Modifiers & Early Termination (Critical for distinguishing 10ms vs 100ms scans)
        "has_limit": 0.0,
        "number_of_limit_nodes": 0.0,
        "has_materialize": 0.0,
        "output_to_scanned_ratio": 1.0,
        "is_unbounded_scan": 0.0
    }

    def traverse(node, depth):
        if not node:
            return
            
        features["number_of_plan_nodes"] += 1.0
        features["plan_depth"] = max(features["plan_depth"], float(depth))
        
        node_cost = float(node.get("Total Cost", 0.0))
        node_rows = float(node.get("Plan Rows", 0.0))
        node_width = float(node.get("Plan Width", 0.0))
        
        features["total_tree_cost"] += node_cost
        features["max_intermediate_rows"] = max(features["max_intermediate_rows"], node_rows)
        features["max_plan_width"] = max(features["max_plan_width"], node_width)
        
        node_type = node.get("Node Type", "")
        
        # Early termination & limit detection
        if node_type == "Limit":
            features["has_limit"] = 1.0
            features["number_of_limit_nodes"] += 1.0
        elif node_type == "Materialize":
            features["has_materialize"] = 1.0
            
        if "Scan" in node_type:
            features["number_of_tables"] += 1.0
            features["total_scanned_rows"] += node_rows
            
            if node_type == "Seq Scan":
                features["number_of_seq_scans"] += 1.0
            elif "Index Scan" in node_type or node_type == "Index Only Scan":
                features["number_of_index_scans"] += 1.0
            elif "Bitmap" in node_type:
                features["has_bitmap_scan"] = 1.0
                features["number_of_bitmap_scans"] += 1.0
                
        if "Join" in node_type:
            features["number_of_joins"] += 1.0
            if node_type == "Nested Loop":
                features["number_of_nested_loop_joins"] += 1.0
            elif node_type == "Hash Join":
                features["number_of_hash_joins"] += 1.0
                features["has_hash_join"] = 1.0
            elif node_type == "Merge Join":
                features["number_of_merge_joins"] += 1.0
                
        if node_type == "Sort":
            features["number_of_sort_nodes"] += 1.0
            
        if node_type == "Aggregate":
            features["number_of_aggregate_nodes"] += 1.0
            
        if "Filter" in node:
            features["number_of_filters"] += 1.0
            
        for child in node.get("Plans", []):
            traverse(child, depth + 1)

    traverse(plan, 1)
    
    # Calculate selectivity and unbounded status
    scanned = max(1.0, features["total_scanned_rows"])
    features["output_to_scanned_ratio"] = min(1.0, features["plan_rows"] / scanned)
    if features["has_limit"] == 0.0 and features["number_of_seq_scans"] > 0:
        features["is_unbounded_scan"] = 1.0
        
    return features
