CREATE TABLE products (
    id SERIAL PRIMARY KEY,
    name VARCHAR(255) NOT NULL,
    category VARCHAR(100),
    price NUMERIC(10, 2) NOT NULL,
    stock INT DEFAULT 0
);

CREATE TABLE customers (
    id SERIAL PRIMARY KEY,
    name VARCHAR(255) NOT NULL,
    city VARCHAR(100),
    email VARCHAR(255) UNIQUE NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE orders (
    id SERIAL PRIMARY KEY,
    customer_id INT REFERENCES customers(id),
    order_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    total_amount NUMERIC(12, 2) NOT NULL,
    status VARCHAR(50) DEFAULT 'PENDING'
);

CREATE TABLE order_items (
    id SERIAL PRIMARY KEY,
    order_id INT REFERENCES orders(id),
    product_id INT REFERENCES products(id),
    quantity INT NOT NULL,
    price NUMERIC(10, 2) NOT NULL
);

CREATE TABLE payments (
    id SERIAL PRIMARY KEY,
    order_id INT REFERENCES orders(id),
    payment_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    amount NUMERIC(12, 2) NOT NULL,
    method VARCHAR(50)
);

CREATE TABLE query_history (
    id SERIAL PRIMARY KEY,
    query_text TEXT NOT NULL,
    query_type VARCHAR(50),
    postgres_estimated_cost NUMERIC,
    postgres_estimated_rows NUMERIC,
    ml_predicted_time_ms NUMERIC,
    actual_execution_time_ms NUMERIC,
    prediction_error_percent NUMERIC,
    performance_category VARCHAR(50),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Create indexes to make query performance vary
CREATE INDEX idx_customers_city ON customers(city);
CREATE INDEX idx_orders_customer_id ON orders(customer_id);
CREATE INDEX idx_orders_order_date ON orders(order_date);
CREATE INDEX idx_order_items_order_id ON order_items(order_id);
CREATE INDEX idx_order_items_product_id ON order_items(product_id);
CREATE INDEX idx_products_category ON products(category);
CREATE INDEX idx_payments_order_id ON payments(order_id);

-- Create read-only user for executing analyzed queries safely
-- Since this is executed as postgres, we can create the user here.
-- Wait, creating a user and granting privileges might require handling passwords.
-- Instead, we will restrict SQL types in the backend (e.g. only allow SELECT/WITH).
-- I'll create an app_readonly user anyway.
CREATE ROLE app_readonly WITH LOGIN PASSWORD 'readonly_password';
GRANT CONNECT ON DATABASE query_db TO app_readonly;
GRANT USAGE ON SCHEMA public TO app_readonly;
GRANT SELECT ON ALL TABLES IN SCHEMA public TO app_readonly;
ALTER DEFAULT PRIVILEGES IN SCHEMA public GRANT SELECT ON TABLES TO app_readonly;
