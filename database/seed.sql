-- Seed products
INSERT INTO products (name, category, price, stock)
SELECT
    'Product ' || i,
    CASE WHEN i % 5 = 0 THEN 'Electronics'
         WHEN i % 5 = 1 THEN 'Clothing'
         WHEN i % 5 = 2 THEN 'Books'
         WHEN i % 5 = 3 THEN 'Home'
         ELSE 'Toys' END,
    (random() * 900 + 10)::NUMERIC(10,2),
    (random() * 500)::INT
FROM generate_series(1, 1000) AS i;

-- Seed customers
INSERT INTO customers (name, city, email, created_at)
SELECT
    'Customer ' || i,
    CASE WHEN i % 7 = 0 THEN 'New York'
         WHEN i % 7 = 1 THEN 'Los Angeles'
         WHEN i % 7 = 2 THEN 'Chicago'
         WHEN i % 7 = 3 THEN 'Houston'
         WHEN i % 7 = 4 THEN 'Phoenix'
         WHEN i % 7 = 5 THEN 'Philadelphia'
         ELSE 'San Antonio' END,
    'customer' || i || '@example.com',
    NOW() - (random() * interval '3 years')
FROM generate_series(1, 50000) AS i;

-- Seed orders
INSERT INTO orders (customer_id, order_date, total_amount, status)
SELECT
    (random() * 49999 + 1)::INT,
    NOW() - (random() * interval '2 years'),
    (random() * 5000 + 20)::NUMERIC(12,2),
    CASE WHEN i % 10 = 0 THEN 'PENDING'
         WHEN i % 10 = 1 THEN 'CANCELLED'
         ELSE 'COMPLETED' END
FROM generate_series(1, 200000) AS i;

-- Seed order_items
INSERT INTO order_items (order_id, product_id, quantity, price)
SELECT
    (random() * 199999 + 1)::INT,
    (random() * 999 + 1)::INT,
    (random() * 5 + 1)::INT,
    (random() * 900 + 10)::NUMERIC(10,2)
FROM generate_series(1, 500000) AS i;

-- Seed payments
INSERT INTO payments (order_id, payment_date, amount, method)
SELECT
    o.id,
    o.order_date + (random() * interval '10 days'),
    o.total_amount,
    CASE WHEN o.id % 3 = 0 THEN 'CREDIT_CARD'
         WHEN o.id % 3 = 1 THEN 'PAYPAL'
         ELSE 'BANK_TRANSFER' END
FROM orders o
WHERE o.status = 'COMPLETED';
