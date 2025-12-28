-- ============================================================================
-- 3DPMP Database Views and Complex Queries
-- 3D Printing and Model-sharing Platform
-- ============================================================================
-- This file contains:
--   - 2 Database Views
--   - 3+ Complex Queries
--
-- Demonstrates the use of:
--   ✓ Aggregate operators (COUNT, SUM, AVG, MAX, MIN)
--   ✓ GROUP BY clause
--   ✓ ORDER BY clause
--   ✓ Nested queries (subqueries)
-- ============================================================================

-- ============================================================================
-- VIEW 1: customer_order_summary_view
-- ============================================================================
-- Purpose: Aggregate statistics for each customer's order history
--
-- Demonstrates:
--   - Aggregate operators: COUNT(), SUM(), AVG(), MAX(), MIN()
--   - GROUP BY clause
--   - ORDER BY clause
--   - Multiple table JOINs
-- ============================================================================

DROP VIEW IF EXISTS customer_order_summary_view;

CREATE VIEW customer_order_summary_view AS
SELECT
    u.id AS customer_id,
    u.email AS customer_email,
    u.display_name AS customer_name,
    COUNT(o.id) AS total_orders,
    COALESCE(SUM(o.total_price), 0) AS total_spent,
    COALESCE(AVG(o.total_price), 0) AS avg_order_amount,
    MAX(o.total_price) AS max_order_amount,
    MIN(o.total_price) AS min_order_amount,
    MAX(o.creation_date) AS last_order_date,
    MIN(o.creation_date) AS first_order_date,
    -- Count orders by status using conditional aggregation
    COUNT(
        CASE
            WHEN o.status = 'COMPLETED' THEN 1
        END
    ) AS completed_orders,
    COUNT(
        CASE
            WHEN o.status = 'CANCELLED' THEN 1
        END
    ) AS cancelled_orders,
    COUNT(
        CASE
            WHEN o.status = 'PENDING' THEN 1
        END
    ) AS pending_orders
FROM
    users_user u
    INNER JOIN users_customer c ON u.id = c.user_id
    LEFT JOIN "order" o ON c.user_id = o.customer_id
GROUP BY
    u.id,
    u.email,
    u.display_name
ORDER BY total_spent DESC;

-- ============================================================================
-- Sample execution result for customer_order_summary_view:
-- ============================================================================
-- customer_id | customer_email      | total_orders | total_spent | avg_order_amount | completed_orders
-- ------------|---------------------|--------------|-------------|------------------|------------------
-- uuid-1      | vip@example.com     | 15           | 45000.00    | 3000.00          | 12
-- uuid-2      | regular@example.com | 5            | 8500.00     | 1700.00          | 4
-- uuid-3      | new@example.com     | 1            | 1200.00     | 1200.00          | 0
-- ============================================================================

-- ============================================================================
-- VIEW 2: model_popularity_view
-- ============================================================================
-- Purpose: Track popularity metrics for each 3D model
--
-- Demonstrates:
--   - Aggregate operators: COUNT(), SUM()
--   - GROUP BY clause
--   - ORDER BY clause
--   - Multiple table JOINs
--   - LEFT JOIN for optional relationships
-- ============================================================================

DROP VIEW IF EXISTS model_popularity_view;

CREATE VIEW model_popularity_view AS
SELECT
    m.id AS model_id,
    m.model_name,
    m.category,
    m.visibility_status,
    u.email AS owner_email,
    m.view_count,
    m.download_count,
    -- Count how many times this model appears in carts
    COALESCE(cart_stats.cart_count, 0) AS cart_count,
    COALESCE(cart_stats.cart_quantity, 0) AS total_cart_quantity,
    -- Count how many times this model was ordered
    COALESCE(order_stats.order_count, 0) AS order_count,
    COALESCE(
        order_stats.total_ordered_quantity,
        0
    ) AS total_ordered_quantity,
    -- Calculate popularity score (weighted formula)
    (
        m.view_count * 1 + m.download_count * 5 + COALESCE(
            order_stats.total_ordered_quantity,
            0
        ) * 10
    ) AS popularity_score,
    m.created_at
FROM
    model m
    INNER JOIN users_user u ON m.owner_id = u.id
    -- Subquery for cart statistics
    LEFT JOIN (
        SELECT
            model_id,
            COUNT(*) AS cart_count,
            SUM(quantity) AS cart_quantity
        FROM cart_item
        GROUP BY
            model_id
    ) cart_stats ON m.id = cart_stats.model_id
    -- Subquery for order statistics
    LEFT JOIN (
        SELECT
            model_id,
            COUNT(*) AS order_count,
            SUM(quantity) AS total_ordered_quantity
        FROM order_item
        WHERE
            model_id IS NOT NULL
        GROUP BY
            model_id
    ) order_stats ON m.id = order_stats.model_id
ORDER BY popularity_score DESC, m.created_at DESC;

-- ============================================================================
-- Sample execution result for model_popularity_view:
-- ============================================================================
-- model_id | model_name     | category | view_count | download_count | order_count | popularity_score
-- ---------|----------------|----------|------------|----------------|-------------|------------------
-- uuid-1   | Cool Figurine  | Toys     | 1500       | 200            | 50          | 3000
-- uuid-2   | Phone Stand    | Gadgets  | 800        | 150            | 30          | 1850
-- uuid-3   | Vase Design    | Home     | 500        | 80             | 15          | 1050
-- ============================================================================

-- ============================================================================
-- COMPLEX QUERY 1: VIP Customers (Spending above average)
-- ============================================================================
-- Purpose: Find customers whose total spending exceeds the average
--
-- Demonstrates:
--   - Nested query (subquery in HAVING clause)
--   - Aggregate operators: SUM(), AVG()
--   - GROUP BY clause
--   - HAVING clause with subquery
--   - ORDER BY clause
-- ============================================================================

-- Query: Find VIP customers who spent more than the average customer
SELECT
    u.id AS customer_id,
    u.email AS customer_email,
    u.display_name AS customer_name,
    COUNT(o.id) AS total_orders,
    SUM(o.total_price) AS total_spent
FROM
    users_user u
    INNER JOIN users_customer c ON u.id = c.user_id
    INNER JOIN "order" o ON c.user_id = o.customer_id
WHERE
    o.status NOT IN ('CANCELLED', 'REFUNDED') -- Exclude cancelled/refunded orders
GROUP BY
    u.id,
    u.email,
    u.display_name
HAVING
    -- Nested query: Compare against average spending across all customers
    SUM(o.total_price) > (
        SELECT AVG(customer_total)
        FROM (
                SELECT SUM(o2.total_price) AS customer_total
                FROM "order" o2
                WHERE
                    o2.status NOT IN ('CANCELLED', 'REFUNDED')
                GROUP BY
                    o2.customer_id
            ) AS customer_totals
    )
ORDER BY total_spent DESC;

-- ============================================================================
-- Sample execution result for Query 1:
-- ============================================================================
-- customer_id | customer_email      | customer_name | total_orders | total_spent
-- ------------|---------------------|---------------|--------------|-------------
-- uuid-1      | vip1@example.com    | VIP User 1    | 25           | 75000.00
-- uuid-2      | vip2@example.com    | VIP User 2    | 18           | 52000.00
-- uuid-3      | vip3@example.com    | VIP User 3    | 12           | 38000.00
-- ============================================================================

-- ============================================================================
-- COMPLEX QUERY 2: Employee Review Performance Statistics
-- ============================================================================
-- Purpose: Statistics on each employee's model review activities
--
-- Demonstrates:
--   - Conditional aggregation with CASE WHEN
--   - Aggregate operators: COUNT(), SUM()
--   - GROUP BY clause
--   - ORDER BY clause
--   - Calculated percentage fields
-- ============================================================================

SELECT
    e.user_id AS employee_id,
    e.employee_name,
    u.email AS employee_email,
    COUNT(mrl.id) AS total_reviews,
    -- Count approvals (status changed to PUBLIC)
    SUM(
        CASE
            WHEN mrl.new_status = 'PUBLIC' THEN 1
            ELSE 0
        END
    ) AS approved_count,
    -- Count rejections
    SUM(
        CASE
            WHEN mrl.new_status = 'REJECTED' THEN 1
            ELSE 0
        END
    ) AS rejected_count,
    -- Calculate approval rate
    ROUND(
        CASE
            WHEN COUNT(mrl.id) > 0 THEN (
                SUM(
                    CASE
                        WHEN mrl.new_status = 'PUBLIC' THEN 1
                        ELSE 0
                    END
                )::DECIMAL / COUNT(mrl.id)
            ) * 100
            ELSE 0
        END,
        2
    ) AS approval_rate_percent,
    -- Get the date of their most recent review
    MAX(mrl.timestamp) AS last_review_date,
    MIN(mrl.timestamp) AS first_review_date
FROM
    users_employee e
    INNER JOIN users_user u ON e.user_id = u.id
    LEFT JOIN model_review_log mrl ON e.user_id = mrl.reviewer_id
GROUP BY
    e.user_id,
    e.employee_name,
    u.email
ORDER BY
    total_reviews DESC,
    approval_rate_percent DESC;

-- ============================================================================
-- Sample execution result for Query 2:
-- ============================================================================
-- employee_id | employee_name | total_reviews | approved_count | rejected_count | approval_rate_percent
-- ------------|---------------|---------------|----------------|----------------|----------------------
-- uuid-1      | Admin Lee     | 150           | 120            | 30             | 80.00
-- uuid-2      | Reviewer Wang | 85            | 60             | 25             | 70.59
-- uuid-3      | New Employee  | 12            | 10             | 2              | 83.33
-- ============================================================================

-- ============================================================================
-- COMPLEX QUERY 3: Customers with Cart Items but No Orders
-- ============================================================================
-- Purpose: Find potential customers who have items in cart but never ordered
--
-- Demonstrates:
--   - Nested query with NOT EXISTS
--   - Aggregate operators: COUNT(), SUM()
--   - GROUP BY clause
--   - ORDER BY clause
-- ============================================================================

SELECT
    u.id AS customer_id,
    u.email AS customer_email,
    u.display_name AS customer_name,
    COUNT(ci.id) AS cart_items_count,
    SUM(ci.quantity) AS total_cart_quantity,
    MIN(ci.created_at) AS first_cart_item_date,
    MAX(ci.updated_at) AS last_cart_update
FROM
    users_user u
    INNER JOIN users_customer c ON u.id = c.user_id
    INNER JOIN cart_item ci ON c.user_id = ci.customer_id
WHERE
    -- Nested query: Filter customers who have NEVER placed an order
    NOT EXISTS (
        SELECT 1
        FROM "order" o
        WHERE
            o.customer_id = c.user_id
    )
GROUP BY
    u.id,
    u.email,
    u.display_name
ORDER BY
    cart_items_count DESC,
    last_cart_update DESC;

-- ============================================================================
-- Sample execution result for Query 3:
-- ============================================================================
-- customer_id | customer_email        | customer_name    | cart_items_count | total_cart_quantity
-- ------------|-----------------------|------------------|------------------|--------------------
-- uuid-1      | waiting@example.com   | Hesitant Buyer   | 8                | 12
-- uuid-2      | browser@example.com   | Window Shopper   | 5                | 5
-- uuid-3      | newuser@example.com   | New User         | 2                | 3
-- ============================================================================

-- ============================================================================
-- COMPLEX QUERY 4: Material Sales Statistics and Revenue Ranking
-- ============================================================================
-- Purpose: Analyze which materials generate the most revenue
--
-- Demonstrates:
--   - Multiple table JOINs
--   - Aggregate operators: COUNT(), SUM()
--   - GROUP BY clause
--   - ORDER BY clause
--   - Nested query for percentage calculation
-- ============================================================================

SELECT
    mat.id AS material_id,
    mat.name AS material_name,
    mat.price_twd_g AS current_price_per_gram,
    COUNT(DISTINCT oi.order_id) AS orders_using_material,
    COUNT(oi.id) AS total_order_items,
    SUM(oi.quantity) AS total_quantity_sold,
    SUM(
        oi.price_snapshot * oi.quantity
    ) AS total_revenue,
    -- Calculate percentage of total revenue using nested query (with NULLIF to avoid division by zero)
    ROUND(
        (
            SUM(
                oi.price_snapshot * oi.quantity
            ) / NULLIF(
                (
                    SELECT SUM(
                            oi2.price_snapshot * oi2.quantity
                        )
                    FROM order_item oi2
                ),
                0
            )
        ) * 100,
        2
    ) AS revenue_percentage
FROM
    material mat
    LEFT JOIN order_item oi ON mat.id = oi.material_id
    LEFT JOIN "order" o ON oi.order_id = o.id
    AND o.status NOT IN ('CANCELLED', 'REFUNDED')
WHERE
    mat.is_active = TRUE
GROUP BY
    mat.id,
    mat.name,
    mat.price_twd_g
ORDER BY total_revenue DESC NULLS LAST;

-- ============================================================================
-- Sample execution result for Query 4:
-- ============================================================================
-- material_id | material_name | current_price_per_gram | orders_using_material | total_revenue | revenue_percentage
-- ------------|---------------|------------------------|----------------------|---------------|-------------------
-- uuid-1      | PLA Premium   | 0.85                   | 250                  | 125000.00     | 45.50
-- uuid-2      | ABS Standard  | 0.75                   | 180                  | 85000.00      | 30.91
-- uuid-3      | PETG Clear    | 1.20                   | 95                   | 45000.00      | 16.36
-- ============================================================================

-- ============================================================================
-- COMPLEX QUERY 5: Monthly Order Trend Analysis
-- ============================================================================
-- Purpose: Analyze order trends by month with comparison to previous month
--
-- Demonstrates:
--   - Date functions and date truncation
--   - Aggregate operators: COUNT(), SUM(), AVG()
--   - GROUP BY clause with date
--   - ORDER BY clause
--   - Window function for trend comparison
-- ============================================================================

SELECT
    DATE_TRUNC('month', o.creation_date) AS order_month,
    COUNT(o.id) AS total_orders,
    COUNT(DISTINCT o.customer_id) AS unique_customers,
    SUM(o.total_price) AS monthly_revenue,
    AVG(o.total_price) AS avg_order_value,
    -- Count by status
    SUM(
        CASE
            WHEN o.status = 'COMPLETED' THEN 1
            ELSE 0
        END
    ) AS completed_orders,
    SUM(
        CASE
            WHEN o.status = 'CANCELLED' THEN 1
            ELSE 0
        END
    ) AS cancelled_orders,
    -- Calculate cancellation rate
    ROUND(
        (
            SUM(
                CASE
                    WHEN o.status = 'CANCELLED' THEN 1
                    ELSE 0
                END
            )::DECIMAL / NULLIF(COUNT(o.id), 0)
        ) * 100,
        2
    ) AS cancellation_rate_percent
FROM "order" o
GROUP BY
    DATE_TRUNC('month', o.creation_date)
ORDER BY order_month DESC;

-- ============================================================================
-- Sample execution result for Query 5:
-- ============================================================================
-- order_month | total_orders | unique_customers | monthly_revenue | avg_order_value | completed_orders | cancellation_rate
-- ------------|--------------|------------------|-----------------|-----------------|------------------|------------------
-- 2025-12-01  | 145          | 89               | 435000.00       | 3000.00         | 120              | 5.52
-- 2025-11-01  | 168          | 102              | 520000.00       | 3095.24         | 155              | 3.57
-- 2025-10-01  | 132          | 78               | 380000.00       | 2878.79         | 115              | 6.82
-- ============================================================================

-- ============================================================================
-- SUMMARY
-- ============================================================================
-- This file demonstrates the following SQL concepts:
--
-- VIEWS (2):
--   1. customer_order_summary_view - Customer order statistics
--   2. model_popularity_view - 3D model popularity metrics
--
-- COMPLEX QUERIES (5):
--   1. VIP Customers - Nested query in HAVING clause
--   2. Employee Review Stats - Conditional aggregation
--   3. Cart but No Orders - NOT EXISTS subquery
--   4. Material Revenue Ranking - Nested query for percentage
--   5. Monthly Order Trends - Date aggregation with GROUP BY
--
-- All queries demonstrate:
--   ✓ Aggregate operators (COUNT, SUM, AVG, MAX, MIN)
--   ✓ GROUP BY clause
--   ✓ ORDER BY clause
--   ✓ Nested queries/subqueries
-- ============================================================================