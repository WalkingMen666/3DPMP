-- ============================================================================
-- 3DPMP Database Schema
-- 3D Printing and Model-sharing Platform
-- ============================================================================
-- This file contains SQL statements for database construction.
-- Compatible with PostgreSQL 18+
-- 
-- Note: In production, Django migrations handle schema creation.
-- This file serves as documentation and for manual database setup if needed.
-- ============================================================================

-- Enable UUID extension
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";

-- ============================================================================
-- 1. USER & AUTHENTICATION (EER Specialization)
-- ============================================================================

-- Base User table (extends Django's AbstractUser)
CREATE TABLE IF NOT EXISTS users_user (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    password VARCHAR(128) NOT NULL,
    last_login TIMESTAMP WITH TIME ZONE,
    is_superuser BOOLEAN NOT NULL DEFAULT FALSE,
    first_name VARCHAR(150) NOT NULL DEFAULT '',
    last_name VARCHAR(150) NOT NULL DEFAULT '',
    email VARCHAR(254) NOT NULL UNIQUE,
    is_staff BOOLEAN NOT NULL DEFAULT FALSE,
    is_active BOOLEAN NOT NULL DEFAULT TRUE,
    date_joined TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT CURRENT_TIMESTAMP,
    auth_provider VARCHAR(20) NOT NULL DEFAULT 'local' 
        CHECK (auth_provider IN ('local', 'google'))
);

CREATE INDEX idx_users_user_email ON users_user(email);

-- Customer (IS-A User) - Specialization
-- user_id is both PK and FK (standard Django OneToOneField with primary_key=True)
CREATE TABLE IF NOT EXISTS users_customer (
    user_id UUID PRIMARY KEY REFERENCES users_user(id) ON DELETE CASCADE
);

-- Employee (IS-A User) - Specialization
-- user_id is both PK and FK (standard Django OneToOneField with primary_key=True)
CREATE TABLE IF NOT EXISTS users_employee (
    user_id UUID PRIMARY KEY REFERENCES users_user(id) ON DELETE CASCADE,
    employee_name VARCHAR(255) NOT NULL,
    is_admin BOOLEAN NOT NULL DEFAULT FALSE
);

-- ============================================================================
-- 2. 3D MODELS & FILES
-- ============================================================================

-- 3D Model entity
CREATE TABLE IF NOT EXISTS model (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    owner_id UUID NOT NULL REFERENCES users_user(id) ON DELETE CASCADE,
    model_name VARCHAR(255) NOT NULL,
    visibility_status VARCHAR(20) NOT NULL DEFAULT 'PRIVATE'
        CHECK (visibility_status IN ('PRIVATE', 'PENDING', 'PUBLIC', 'REJECTED')),
    stl_file_path VARCHAR(500) NOT NULL,
    gcode_file_path VARCHAR(500),
    slicing_info JSONB,
    created_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX idx_model_owner_id ON model(owner_id);
CREATE INDEX idx_model_visibility_status ON model(visibility_status);
CREATE INDEX idx_model_created_at ON model(created_at DESC);

-- Model Images (multiple per model)
CREATE TABLE IF NOT EXISTS model_image (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    model_id UUID NOT NULL REFERENCES model(id) ON DELETE CASCADE,
    image_path VARCHAR(500) NOT NULL,
    created_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX idx_model_image_model_id ON model_image(model_id);

-- Model Review Log (audit trail for status changes)
CREATE TABLE IF NOT EXISTS model_review_log (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    model_id UUID NOT NULL REFERENCES model(id) ON DELETE CASCADE,
    reviewer_id UUID NOT NULL REFERENCES users_employee(user_id) ON DELETE RESTRICT,
    previous_status VARCHAR(20) CHECK (previous_status IN ('PRIVATE', 'PENDING', 'PUBLIC', 'REJECTED')),
    new_status VARCHAR(20) NOT NULL CHECK (new_status IN ('PRIVATE', 'PENDING', 'PUBLIC', 'REJECTED')),
    reason TEXT,
    timestamp TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX idx_model_review_log_model_id ON model_review_log(model_id);
CREATE INDEX idx_model_review_log_reviewer_id ON model_review_log(reviewer_id);

-- ============================================================================
-- 3. MATERIALS & CART
-- ============================================================================

-- Material definitions
CREATE TABLE IF NOT EXISTS material (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    name VARCHAR(100) NOT NULL UNIQUE,
    density_g_cm3 DECIMAL(10, 5) NOT NULL CHECK (density_g_cm3 >= 0),
    price_twd_g DECIMAL(10, 2) NOT NULL CHECK (price_twd_g >= 0),
    is_active BOOLEAN NOT NULL DEFAULT TRUE,
    created_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX idx_material_name ON material(name);
CREATE INDEX idx_material_is_active ON material(is_active);

-- Shopping Cart Items
CREATE TABLE IF NOT EXISTS cart_item (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    customer_id UUID NOT NULL REFERENCES users_customer(user_id) ON DELETE CASCADE,
    model_id UUID NOT NULL REFERENCES model(id) ON DELETE CASCADE,
    material_id UUID NOT NULL REFERENCES material(id) ON DELETE RESTRICT,
    quantity INTEGER NOT NULL DEFAULT 1 CHECK (quantity >= 1),
    notes TEXT,
    created_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT CURRENT_TIMESTAMP,
    -- Prevent duplicate model+material combinations per customer
    CONSTRAINT unique_cart_item_per_customer UNIQUE (customer_id, model_id, material_id)
);

CREATE INDEX idx_cart_item_customer_id ON cart_item(customer_id);

-- ============================================================================
-- 4. SHIPPING
-- ============================================================================

-- Global Shipping Options (defined by Admin)
CREATE TABLE IF NOT EXISTS shipping_option (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    name VARCHAR(100) NOT NULL,
    type VARCHAR(30) NOT NULL DEFAULT 'HOME_DELIVERY'
        CHECK (type IN ('HOME_DELIVERY', 'CONVENIENCE_STORE', 'SELF_PICKUP')),
    base_fee DECIMAL(10, 2) NOT NULL CHECK (base_fee >= 0),
    is_active BOOLEAN NOT NULL DEFAULT TRUE,
    created_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX idx_shipping_option_is_active ON shipping_option(is_active);

-- Customer Saved Addresses
CREATE TABLE IF NOT EXISTS saved_address (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    customer_id UUID NOT NULL REFERENCES users_customer(user_id) ON DELETE CASCADE,
    name VARCHAR(100) NOT NULL,
    address_type VARCHAR(30) NOT NULL
        CHECK (address_type IN ('HOME_DELIVERY', 'CONVENIENCE_STORE', 'SELF_PICKUP')),
    address_details TEXT NOT NULL,
    is_default BOOLEAN NOT NULL DEFAULT FALSE,
    created_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX idx_saved_address_customer_id ON saved_address(customer_id);

-- ============================================================================
-- 5. ORDERS (Immutable Snapshots)
-- ============================================================================

-- Order table
-- CRITICAL: No foreign keys to mutable shipping/address tables!
CREATE TABLE IF NOT EXISTS "order" (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    customer_id UUID NOT NULL REFERENCES users_customer(user_id) ON DELETE RESTRICT,
    assignee_id UUID REFERENCES users_employee(user_id) ON DELETE SET NULL,
    status VARCHAR(20) NOT NULL DEFAULT 'PENDING'
        CHECK (status IN ('PENDING', 'CONFIRMED', 'PROCESSING', 'PRINTING', 
                          'QUALITY_CHECK', 'READY_TO_SHIP', 'SHIPPED', 
                          'DELIVERED', 'COMPLETED', 'CANCELLED', 'REFUNDED')),
    -- Shipping Snapshot: JSON {service_name, fee, address_details}
    ship_snapshot JSONB NOT NULL,
    total_price DECIMAL(10, 2) NOT NULL CHECK (total_price >= 0),
    notes TEXT,
    tracking_number VARCHAR(100),
    creation_date TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX idx_order_customer_id ON "order"(customer_id);
CREATE INDEX idx_order_assignee_id ON "order"(assignee_id);
CREATE INDEX idx_order_status ON "order"(status);
CREATE INDEX idx_order_creation_date ON "order"(creation_date DESC);

-- Order Items with Price Snapshot
CREATE TABLE IF NOT EXISTS order_item (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    order_id UUID NOT NULL REFERENCES "order"(id) ON DELETE CASCADE,
    model_id UUID NOT NULL REFERENCES model(id) ON DELETE RESTRICT,
    material_id UUID NOT NULL REFERENCES material(id) ON DELETE RESTRICT,
    item_number INTEGER NOT NULL,
    quantity INTEGER NOT NULL DEFAULT 1 CHECK (quantity >= 1),
    -- Price at time of purchase (immutable)
    price_snapshot DECIMAL(10, 2) NOT NULL CHECK (price_snapshot >= 0),
    slicing_info_snapshot JSONB,
    notes TEXT,
    -- Ensure unique item numbers per order
    CONSTRAINT unique_item_number_per_order UNIQUE (order_id, item_number)
);

CREATE INDEX idx_order_item_order_id ON order_item(order_id);

-- Order Status Change Log
CREATE TABLE IF NOT EXISTS order_log (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    order_id UUID NOT NULL REFERENCES "order"(id) ON DELETE CASCADE,
    updated_by_id UUID NOT NULL REFERENCES users_employee(user_id) ON DELETE RESTRICT,
    previous_status VARCHAR(20) CHECK (previous_status IN ('PENDING', 'CONFIRMED', 'PROCESSING', 
                                        'PRINTING', 'QUALITY_CHECK', 'READY_TO_SHIP', 
                                        'SHIPPED', 'DELIVERED', 'COMPLETED', 'CANCELLED', 'REFUNDED')),
    new_status VARCHAR(20) NOT NULL CHECK (new_status IN ('PENDING', 'CONFIRMED', 'PROCESSING', 
                                        'PRINTING', 'QUALITY_CHECK', 'READY_TO_SHIP', 
                                        'SHIPPED', 'DELIVERED', 'COMPLETED', 'CANCELLED', 'REFUNDED')),
    notes TEXT,
    timestamp TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX idx_order_log_order_id ON order_log(order_id);
CREATE INDEX idx_order_log_timestamp ON order_log(timestamp DESC);

-- ============================================================================
-- 6. DISCOUNTS (EER Superclass/Subclass)
-- ============================================================================

-- Base Discount (Superclass)
CREATE TABLE IF NOT EXISTS discount (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    name VARCHAR(255) NOT NULL,
    description TEXT,
    start_date TIMESTAMP WITH TIME ZONE NOT NULL,
    due_date TIMESTAMP WITH TIME ZONE,
    min_price DECIMAL(10, 2) NOT NULL DEFAULT 0 CHECK (min_price >= 0),
    max_discount DECIMAL(10, 2) CHECK (max_discount >= 0),
    works_on VARCHAR(20) NOT NULL DEFAULT 'ORDER_SUBTOTAL'
        CHECK (works_on IN ('ORDER_SUBTOTAL', 'SHIPPING', 'TOTAL')),
    is_fixed BOOLEAN NOT NULL DEFAULT FALSE,
    dis_value DECIMAL(10, 2) NOT NULL CHECK (dis_value >= 0),
    is_active BOOLEAN NOT NULL DEFAULT TRUE,
    created_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT CURRENT_TIMESTAMP,
    -- Percentage discounts cannot exceed 100%
    CONSTRAINT valid_percentage CHECK (is_fixed = TRUE OR dis_value <= 100)
);

CREATE INDEX idx_discount_is_active ON discount(is_active);
CREATE INDEX idx_discount_start_date ON discount(start_date);
CREATE INDEX idx_discount_due_date ON discount(due_date);

-- Global Discount (IS-A Discount) - Auto-applied
CREATE TABLE IF NOT EXISTS global_discount (
    discount_id UUID PRIMARY KEY REFERENCES discount(id) ON DELETE CASCADE,
    priority INTEGER NOT NULL DEFAULT 0
);

CREATE INDEX idx_global_discount_priority ON global_discount(priority DESC);

-- Coupon (IS-A Discount) - User-entered code
CREATE TABLE IF NOT EXISTS coupon (
    discount_id UUID PRIMARY KEY REFERENCES discount(id) ON DELETE CASCADE,
    coupon_code VARCHAR(50) NOT NULL UNIQUE,
    max_uses_total INTEGER CHECK (max_uses_total > 0),
    max_uses_per_customer INTEGER NOT NULL DEFAULT 1 CHECK (max_uses_per_customer >= 1)
);

CREATE INDEX idx_coupon_code ON coupon(coupon_code);

-- M:N Link: Order <-> GlobalDiscount
CREATE TABLE IF NOT EXISTS is_affected (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    order_id UUID NOT NULL REFERENCES "order"(id) ON DELETE CASCADE,
    global_discount_id UUID NOT NULL REFERENCES global_discount(discount_id) ON DELETE RESTRICT,
    discount_snapshot_info JSONB NOT NULL,
    discount_amount DECIMAL(10, 2) NOT NULL CHECK (discount_amount >= 0),
    created_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT CURRENT_TIMESTAMP,
    -- Prevent same discount applied twice to same order
    CONSTRAINT unique_global_discount_per_order UNIQUE (order_id, global_discount_id)
);

CREATE INDEX idx_is_affected_order_id ON is_affected(order_id);

-- 1:1 Link: Order <-> Coupon (max 1 coupon per order)
CREATE TABLE IF NOT EXISTS coupon_redemption (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    customer_id UUID NOT NULL REFERENCES users_customer(user_id) ON DELETE RESTRICT,
    coupon_id UUID NOT NULL REFERENCES coupon(discount_id) ON DELETE RESTRICT,
    -- UNIQUE constraint enforces max 1 coupon per order
    order_id UUID NOT NULL UNIQUE REFERENCES "order"(id) ON DELETE CASCADE,
    discount_snapshot_info JSONB,
    discount_amount DECIMAL(10, 2) NOT NULL CHECK (discount_amount >= 0),
    timestamp TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX idx_coupon_redemption_customer_id ON coupon_redemption(customer_id);
CREATE INDEX idx_coupon_redemption_coupon_id ON coupon_redemption(coupon_id);

-- ============================================================================
-- 7. DJANGO REQUIRED TABLES (created by Django, shown for reference)
-- ============================================================================

-- Note: The following tables are auto-created by Django migrations:
-- - django_migrations
-- - django_content_type
-- - django_admin_log
-- - django_session
-- - django_site
-- - auth_permission
-- - auth_group
-- - auth_group_permissions
-- - users_user_groups
-- - users_user_user_permissions
-- - account_emailaddress
-- - account_emailconfirmation
-- - authtoken_token
-- - socialaccount_* tables

-- ============================================================================
-- 8. HELPER FUNCTIONS
-- ============================================================================

-- Function to auto-update updated_at timestamp
CREATE OR REPLACE FUNCTION update_updated_at_column()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = CURRENT_TIMESTAMP;
    RETURN NEW;
END;
$$ language 'plpgsql';

-- Apply trigger to tables with updated_at column
CREATE TRIGGER update_model_updated_at BEFORE UPDATE ON model
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER update_material_updated_at BEFORE UPDATE ON material
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER update_cart_item_updated_at BEFORE UPDATE ON cart_item
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER update_shipping_option_updated_at BEFORE UPDATE ON shipping_option
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER update_saved_address_updated_at BEFORE UPDATE ON saved_address
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER update_order_updated_at BEFORE UPDATE ON "order"
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER update_discount_updated_at BEFORE UPDATE ON discount
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();
