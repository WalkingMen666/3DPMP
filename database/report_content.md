# Database System Term Project - Report Content

## 1. Functional Dependencies (FDs)

Based on our schema, here are the key Functional Dependencies:

**User Table (`users_user`)**
*   `id` -> `email`, `password`, `first_name`, `last_name`, `date_joined`, `auth_provider`, `display_name`, `avatar_type`
    *   *Rationale*: The `id` (UUID) uniquely identifies a user row. `email` is also a candidate key (UNIQUE).

**Model Table (`model`)**
*   `id` -> `owner_id`, `model_name`, `visibility_status`, `stl_file_path`, `created_at`, `slicing_status`, `category`, `price`
    *   *Rationale*: `id` is the primary key.

**Material Table (`material`)**
*   `id` -> `name`, `density_g_cm3`, `price_twd_g`
*   `name` -> `id`, `density_g_cm3`, `price_twd_g`
    *   *Rationale*: `name` is UNIQUE and can distinctively identify a material.

**Order Table (`order`)**
*   `id` -> `customer_id`, `status`, `total_price`, `creation_date`
    *   *Rationale*: `id` is the primary key.

**Order Item Table (`order_item`)**
*   `id` -> `order_id`, `model_id`, `material_id`, `quantity`
*   (`order_id`, `item_number`) -> `id`, `model_id`, `material_id`
    *   *Rationale*: `id` is PK. The composite (`order_id`, `item_number`) is also unique.

## 2. Normalization Analysis

The database schema is designed to be in **Third Normal Form (3NF)** (and effectively BCNF).

*   **1NF (First Normal Form)**:
    *   All attributes are atomic. For example, we do not store "list of model identifiers" in the User table. Instead, we use a separate `model` table with a foreign key `owner_id`.
    *   There are no repeating groups.

*   **2NF (Second Normal Form)**:
    *   Every non-prime attribute is fully functionally dependent on the primary key.
    *   In tables with single-column keys (User, Model, Material, Order), this is automatically identical to 1NF.
    *   In tables that might have had composite keys (e.g., if `CartItem` didn't have its own UUID), we ensured that attributes like `quantity` depend on the *entire* key (Customer+Model+Material), not just part of it. However, we use surrogate UUID keys for all tables, which simplifies 2NF compliance.

*   **3NF (Third Normal Form)**:
    *   No transitive dependencies for non-prime attributes.
    *   *Example of avoiding violation*: In `order_item`, we store `price_snapshot`. If we relied on `material_id` -> `price`, that would be a transitive dependency (`order_item` -> `material` -> `price`). However, since `material.price` changes over time, the `price_snapshot` in `order_item` is logically a distinct attribute (the price *at that moment*), not just a copy of the current material price. Thus, 3NF is preserved.
    *   *Address Handling*: We separated `saved_address` from `users_customer`. If address fields (City, Street) were columns in `users_customer`, and `ZipCode` determined `City`, that would be a 3NF violation. By isolating addresses or treating the address blob as an atomic "destination", we maintain good design.

## 3. Database Tuning Suggestions

### Index Structures
We have implemented B-Tree indexes on frequently queried columns:
*   **Foreign Keys**: `owner_id` (Model), `customer_id` (Order), etc., to speed up Joins.
*   **Status Fields**: `visibility_status` (Model), `status` (Order) for filtering active items.
*   **Dates**: `created_at` to optimize "Latest Items" or "Recent Orders" queries.

**Suggestions for Future Tuning:**
1.  **Composite Indexes**:
    *   For the "Marketplace" view which filters by `visibility_status='PUBLIC'` AND sorts by `created_at`, a composite index `(visibility_status, created_at DESC)` would reduce lookup time compared to separate indexes.
2.  **Full Text Search (GIN Index)**:
    *   For `model_name` or `description`, standard B-Tree LIKE queries are slow (`%term%`). Implementing a PostgreSQL GIN index with `to_tsvector` would allow efficient keyword search.
3.  **Partial Indexes**:
    *   `CREATE INDEX idx_active_orders ON "order" (created_at) WHERE status NOT IN ('COMPLETED', 'CANCELLED');`
    *   This keeps the index small and fast for the "Active Orders" dashboard used by admins.

