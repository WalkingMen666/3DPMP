-- ============================================================================
-- 3DPMP Database Report Queries (Active Implementation)
-- ============================================================================
-- This file contains the SQL Views and Complex Queries currently active in
-- the 3DPMP application (see backend/apps/stats/views.py).
--
-- Contents:
--   1. View: model_popularity_view (Used for Public Stats)
--   2. View: customer_order_summary_view (Database Structure)
--   3. Query: Monthly Order Trends (Admin Stats)
--   4. Query: VIP Customers Analysis (Admin Stats)
--   5. Query: Material Revenue Analysis (Admin Stats)
--   6. Query: Hesitant Buyers / Cart Abandonment (Admin Stats)
--   7. Query: Employee Performance Review (Admin Stats)
--   8. Query: Order Status Distribution (Admin Stats)
-- ============================================================================

-- ============================================================================
-- 1. VIEW: model_popularity_view
-- ============================================================================
-- Purpose: Calculates a weighted popularity score for models based on views,
-- downloads, and actual printed orders.
-- Used in: Public Stats (Top Models)
-- ============================================================================
CREATE OR REPLACE VIEW model_popularity_view AS
SELECT
    m.id AS model_id,
    m.model_name,
    m.category,
    m.visibility_status,
    u.email AS owner_email,
    m.view_count,
    m.download_count,
    COALESCE(cart_stats.cart_count, 0) AS cart_count,
    COALESCE(cart_stats.cart_quantity, 0) AS total_cart_quantity,
    COALESCE(order_stats.order_count, 0) AS order_count,
    COALESCE(
        order_stats.total_ordered_quantity,
        0
    ) AS total_ordered_quantity,
    -- Weighted Score Formula:
    -- View (1pt) + Download (5pts) + Print Order (10pts)
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
    LEFT JOIN (
        SELECT
            model_id,
            COUNT(*) AS cart_count,
            SUM(quantity) AS cart_quantity
        FROM cart_item
        GROUP BY
            model_id
    ) cart_stats ON m.id = cart_stats.model_id
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
-- 2. VIEW: customer_order_summary_view
-- ============================================================================
-- Purpose: Aggregates total spending, average order value, and order counts per customer.
-- Note: Logic similar to this is used in the VIP Customers query.
-- ============================================================================
CREATE OR REPLACE VIEW customer_order_summary_view AS
SELECT
    u.id AS customer_id,
    u.email AS customer_email,
    u.display_name AS customer_name,
    COUNT(o.id) AS total_orders,
    COALESCE(SUM(o.total_price), 0) AS total_spent,
    COALESCE(AVG(o.total_price), 0) AS avg_order_amount,
    MAX(o.creation_date) AS last_order_date,
    COUNT(
        CASE
            WHEN o.status = 'COMPLETED' THEN 1
        END
    ) AS completed_orders,
    COUNT(
        CASE
            WHEN o.status = 'CANCELLED' THEN 1
        END
    ) AS cancelled_orders
FROM
    users_user u
    INNER JOIN users_customer c ON u.id = c.user_id
    LEFT JOIN "order" o ON c.user_id = o.customer_id
GROUP BY
    u.id,
    u.email,
    u.display_name;

-- ============================================================================
-- 3. COMPLEX QUERY: Monthly Order Trends
-- ============================================================================
-- Demonstrates: Date Truncation, Aggregation (SUM, AVG, COUNT), CASE Expressions
-- Used in: Admin Dashboard (Monthly Trends)
-- ============================================================================
SELECT
    TO_CHAR(DATE_TRUNC('month', o.creation_date), 'YYYY-MM') AS month,
    COUNT(o.id) AS total_orders,
    COUNT(DISTINCT o.customer_id) AS unique_customers,
    SUM(o.total_price) AS total_revenue,
    AVG(o.total_price) AS avg_order_value,
    ROUND(
        (SUM(CASE WHEN o.status = 'CANCELLED' THEN 1 ELSE 0 END)::DECIMAL / NULLIF(COUNT(o.id), 0)) * 100,
        2
    ) AS cancellation_rate
FROM "order" o
GROUP BY DATE_TRUNC('month', o.creation_date)
ORDER BY DATE_TRUNC('month', o.creation_date) DESC
LIMIT 12;

-- ============================================================================
-- 4. COMPLEX QUERY: VIP Customers (Above Average Spending)
-- ============================================================================
-- Demonstrates: Nested Query in HAVING clause, filtering out cancelled orders
-- Used in: Admin Dashboard (VIP Customers)
-- ============================================================================
SELECT
    u.email,
    u.display_name,
    COUNT(o.id) AS total_orders,
    SUM(o.total_price) AS total_spent
FROM
    users_user u
    INNER JOIN users_customer c ON u.id = c.user_id
    INNER JOIN "order" o ON c.user_id = o.customer_id
WHERE
    o.status NOT IN('CANCELLED', 'REFUNDED')
GROUP BY
    u.id,
    u.email,
    u.display_name
HAVING
    SUM(o.total_price) > (
        SELECT AVG(customer_total)
        FROM (
                SELECT SUM(o2.total_price) AS customer_total
                FROM "order" o2
                WHERE
                    o2.status NOT IN('CANCELLED', 'REFUNDED')
                GROUP BY
                    o2.customer_id
            ) AS customer_totals
    )
ORDER BY total_spent DESC
LIMIT 10;

-- ============================================================================
-- 5. COMPLEX QUERY: Material Revenue Analysis
-- ============================================================================
-- Demonstrates: Nested Query for Total Calculation (Percentage), Joins
-- Used in: Admin Dashboard (Material Revenue)
-- ============================================================================
SELECT
    mat.name AS material_name,
    COUNT(DISTINCT oi.order_id) AS orders_count,
    SUM(oi.quantity) AS total_quantity,
    SUM(
        oi.price_snapshot * oi.quantity
    ) AS revenue,
    ROUND(
        (
            SUM(
                oi.price_snapshot * oi.quantity
            ) / NULLIF(
                (
                    SELECT SUM(price_snapshot * quantity)
                    FROM order_item
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
    AND o.status NOT IN('CANCELLED', 'REFUNDED')
WHERE
    mat.is_active = TRUE
GROUP BY
    mat.id,
    mat.name
ORDER BY revenue DESC NULLS LAST;

-- ============================================================================
-- 6. COMPLEX QUERY: Hesitant Buyers (Cart Abandonment)
-- ============================================================================
-- Demonstrates: NOT EXISTS Subquery
-- Used in: Admin Dashboard (Hesitant Buyers)
-- ============================================================================
SELECT
    u.email,
    MAX(ci.updated_at) AS last_cart_activity,
    COUNT(ci.id) AS cart_items_count
FROM
    users_user u
    INNER JOIN users_customer c ON u.id = c.user_id
    INNER JOIN cart_item ci ON c.user_id = ci.customer_id
WHERE
    NOT EXISTS (
        SELECT 1
        FROM "order" o
        WHERE
            o.customer_id = c.user_id
    )
GROUP BY
    u.id,
    u.email
ORDER BY last_cart_activity DESC
LIMIT 10;

-- ============================================================================
-- 7. COMPLEX QUERY: Employee Performance Review
-- ============================================================================
-- Demonstrates: Conditional Aggregation (Approval Rate Calculation)
-- Used in: Admin Dashboard (Employee Stats)
-- ============================================================================
SELECT
    e.employee_name,
    COUNT(mrl.id) AS total_reviews,
    SUM(CASE WHEN mrl.new_status = 'PUBLIC' THEN 1 ELSE 0 END) AS approved_count,
    SUM(CASE WHEN mrl.new_status = 'REJECTED' THEN 1 ELSE 0 END) AS rejected_count,
    ROUND(
        CASE
            WHEN COUNT(mrl.id) > 0 THEN (SUM(CASE WHEN mrl.new_status = 'PUBLIC' THEN 1 ELSE 0 END)::DECIMAL / COUNT(mrl.id)) * 100
            ELSE 0
        END, 2
    ) AS approval_rate
FROM
    users_employee e
    LEFT JOIN model_review_log mrl ON e.user_id = mrl.reviewer_id
GROUP BY e.user_id, e.employee_name
ORDER BY total_reviews DESC;

-- ============================================================================
-- 8. QUERY: Order Status Distribution
-- ============================================================================
-- Demonstrates: Simple GROUP BY and Aggregation
-- Used in: Admin Dashboard (Order Status)
-- ============================================================================
SELECT status, COUNT(*) as count
FROM "order"
GROUP BY
    status
ORDER BY count DESC;