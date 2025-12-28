from django.db import connection
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from rest_framework import status

class StatsView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        user = request.user
        print(f"DEBUG STATS: User={user}, IsAuth={user.is_authenticated}, IsStaff={user.is_staff}, IsSuper={getattr(user, 'is_superuser', False)}")
        if hasattr(user, 'employee_profile'):
             print(f"DEBUG STATS: Employee Profile Found, IsAdmin={user.employee_profile.is_admin}")
        else:
             print("DEBUG STATS: No Employee Profile")
             
        data = {}

        with connection.cursor() as cursor:
            # 1. PUBLIC: Top Models (using model_popularity_view)
            cursor.execute("""
                SELECT 
                    model_name,
                    owner_email AS creator,
                    total_ordered_quantity AS units_sold,
                    popularity_score
                FROM model_popularity_view
                WHERE visibility_status = 'PUBLIC'
                ORDER BY popularity_score DESC
                LIMIT 5;
            """)
            columns = [col[0] for col in cursor.description]
            data['top_models'] = [dict(zip(columns, row)) for row in cursor.fetchall()]

            # 2. PUBLIC: Trending Materials (Using usage count)
            cursor.execute("""
                SELECT 
                    mat.name,
                    COUNT(oi.id) as usage_count
                FROM material mat
                JOIN order_item oi ON mat.id = oi.material_id
                JOIN "order" o ON oi.order_id = o.id
                WHERE o.status NOT IN ('CANCELLED', 'REFUNDED')
                GROUP BY mat.id, mat.name
                ORDER BY usage_count DESC
                LIMIT 5;
            """)
            columns = [col[0] for col in cursor.description]
            data['trending_materials'] = [dict(zip(columns, row)) for row in cursor.fetchall()]



            # --- ADMIN ONLY SECTIONS ---
            is_admin = False
            if user.is_authenticated:
                if user.is_staff or getattr(user, 'is_superuser', False):
                    is_admin = True
                else:
                    try:
                        if hasattr(user, 'employee_profile') and user.employee_profile.is_admin:
                            is_admin = True
                    except:
                        pass

            if is_admin:
                # 4. ADMIN: Monthly Trends (Complex Query 5)
                cursor.execute("""
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
                """)
                columns = [col[0] for col in cursor.description]
                data['monthly_trends'] = [dict(zip(columns, row)) for row in cursor.fetchall()]

                # 5. ADMIN: VIP Customers (Complex Query 1)
                cursor.execute("""
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
                        o.status NOT IN ('CANCELLED', 'REFUNDED')
                    GROUP BY
                        u.id, u.email, u.display_name
                    HAVING
                        SUM(o.total_price) > (
                            SELECT AVG(customer_total)
                            FROM (
                                    SELECT SUM(o2.total_price) AS customer_total
                                    FROM "order" o2
                                    WHERE o2.status NOT IN ('CANCELLED', 'REFUNDED')
                                    GROUP BY o2.customer_id
                                ) AS customer_totals
                        )
                    ORDER BY total_spent DESC
                    LIMIT 10;
                """)
                columns = [col[0] for col in cursor.description]
                data['vip_customers'] = [dict(zip(columns, row)) for row in cursor.fetchall()]

                # 6. ADMIN: Material Revenue (Complex Query 4)
                cursor.execute("""
                    SELECT
                        mat.name AS material_name,
                        COUNT(DISTINCT oi.order_id) AS orders_count,
                        SUM(oi.quantity) AS total_quantity,
                        SUM(oi.price_snapshot * oi.quantity) AS revenue,
                        ROUND(
                            (SUM(oi.price_snapshot * oi.quantity) / NULLIF((SELECT SUM(price_snapshot * quantity) FROM order_item), 0)) * 100,
                            2
                        ) AS revenue_percentage
                    FROM
                        material mat
                        LEFT JOIN order_item oi ON mat.id = oi.material_id
                        LEFT JOIN "order" o ON oi.order_id = o.id AND o.status NOT IN ('CANCELLED', 'REFUNDED')
                    WHERE mat.is_active = TRUE
                    GROUP BY mat.id, mat.name
                    ORDER BY revenue DESC NULLS LAST;
                """)
                columns = [col[0] for col in cursor.description]
                data['material_revenue'] = [dict(zip(columns, row)) for row in cursor.fetchall()]

                # 7. ADMIN: Hesitant Buyers (Complex Query 3)
                cursor.execute("""
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
                            SELECT 1 FROM "order" o WHERE o.customer_id = c.user_id
                        )
                    GROUP BY u.id, u.email
                    ORDER BY last_cart_activity DESC
                    LIMIT 10;
                """)
                columns = [col[0] for col in cursor.description]
                data['hesitant_buyers'] = [dict(zip(columns, row)) for row in cursor.fetchall()]

                # 8. ADMIN: Employee Performance (Complex Query 2)
                cursor.execute("""
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
                """)
                columns = [col[0] for col in cursor.description]
                data['employee_stats'] = [dict(zip(columns, row)) for row in cursor.fetchall()]
                
                # 9. ADMIN: Order Status Distribution
                cursor.execute("""
                    SELECT status, COUNT(*) as count
                    FROM "order"
                    GROUP BY status
                    ORDER BY count DESC;
                """)
                columns = [col[0] for col in cursor.description]
                data['order_status_distribution'] = [dict(zip(columns, row)) for row in cursor.fetchall()]

        data['is_admin'] = is_admin
        return Response(data, status=status.HTTP_200_OK)
