-- ============================================================================
-- 3DPMP Database Schema (Updated to match Actual Production Schema)
-- 3D Printing and Model-sharing Platform
-- ============================================================================
-- This file contains SQL statements for database construction based on the
-- actual running PostgreSQL instance and Django migrations.
-- Compatible with PostgreSQL 18+
-- ============================================================================

-- Enable UUID extension
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";

-- ============================================================================
-- 1. USER & AUTHENTICATION
-- ============================================================================

-- Base User table (extends Django's AbstractUser)
CREATE TABLE IF NOT EXISTS users_user (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4 (),
    password VARCHAR(128) NOT NULL,
    last_login TIMESTAMP
    WITH
        TIME ZONE,
        is_superuser BOOLEAN NOT NULL DEFAULT FALSE,
        first_name VARCHAR(150) NOT NULL DEFAULT '',
        last_name VARCHAR(150) NOT NULL DEFAULT '',
        email VARCHAR(254) NOT NULL UNIQUE,
        is_staff BOOLEAN NOT NULL DEFAULT FALSE,
        is_active BOOLEAN NOT NULL DEFAULT TRUE,
        date_joined TIMESTAMP
    WITH
        TIME ZONE NOT NULL DEFAULT CURRENT_TIMESTAMP,
        auth_provider VARCHAR(20) NOT NULL DEFAULT 'local' CHECK (
            auth_provider IN ('local', 'google')
        ),
        avatar_image VARCHAR(100),
        avatar_type VARCHAR(20) NOT NULL DEFAULT 'default',
        display_name VARCHAR(100)
);

CREATE INDEX idx_users_user_email ON users_user (email);

-- Customer (OneToOne with User)
CREATE TABLE IF NOT EXISTS users_customer (
    user_id UUID PRIMARY KEY REFERENCES users_user (id) ON DELETE CASCADE
);

-- Employee (OneToOne with User)
CREATE TABLE IF NOT EXISTS users_employee (
    user_id UUID PRIMARY KEY REFERENCES users_user (id) ON DELETE CASCADE,
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
    description TEXT,
    category VARCHAR(50) NOT NULL DEFAULT 'Other',
    tags JSONB DEFAULT '[]', -- JSON array of tags
    visibility_status VARCHAR(20) NOT NULL DEFAULT 'PRIVATE'
        CHECK (visibility_status IN ('PRIVATE', 'PENDING', 'PUBLIC', 'REJECTED')),
    price DECIMAL(10, 2), -- Nullable, if null/0 then free

-- File Paths & Metadata
stl_file VARCHAR(100), -- Relative path for Django FileField
stl_file_path VARCHAR(500), -- Absolute path or storage path
gcode_file_path VARCHAR(500),
thumbnail VARCHAR(100), -- Path to auto-generated thumbnail

-- Stats
view_count INTEGER NOT NULL DEFAULT 0,
download_count INTEGER NOT NULL DEFAULT 0,
is_featured BOOLEAN NOT NULL DEFAULT FALSE,

-- Slicing Data
slicing_info JSONB,
    slicing_status VARCHAR(20) DEFAULT 'PENDING', -- PENDING, COMPLETED, FAILED
    slicing_error TEXT,

    created_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX idx_model_owner_id ON model (owner_id);

CREATE INDEX idx_model_visibility_status ON model (visibility_status);

CREATE INDEX idx_model_created_at ON model (created_at DESC);

-- Model Images
CREATE TABLE IF NOT EXISTS model_image (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4 (),
    model_id UUID NOT NULL REFERENCES model (id) ON DELETE CASCADE,
    image VARCHAR(100), -- Django ImageField path
    image_path VARCHAR(500), -- Legacy/Backup path
    is_primary BOOLEAN NOT NULL DEFAULT FALSE,
    "order" INTEGER NOT NULL DEFAULT 0,
    created_at TIMESTAMP
    WITH
        TIME ZONE NOT NULL DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX idx_model_image_model_id ON model_image (model_id);

-- Model Review Log
CREATE TABLE IF NOT EXISTS model_review_log (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4 (),
    model_id UUID NOT NULL REFERENCES model (id) ON DELETE CASCADE,
    reviewer_id UUID NOT NULL REFERENCES users_employee (user_id) ON DELETE RESTRICT,
    previous_status VARCHAR(20),
    new_status VARCHAR(20) NOT NULL,
    reason TEXT,
    timestamp TIMESTAMP
    WITH
        TIME ZONE NOT NULL DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX idx_model_review_log_model_id ON model_review_log (model_id);

-- ============================================================================
-- 3. MATERIALS & CART
-- ============================================================================

-- Material definitions
CREATE TABLE IF NOT EXISTS material (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4 (),
    name VARCHAR(100) NOT NULL UNIQUE,
    density_g_cm3 DECIMAL(10, 5) NOT NULL,
    price_twd_g DECIMAL(10, 2) NOT NULL,
    is_active BOOLEAN NOT NULL DEFAULT TRUE,
    created_at TIMESTAMP
    WITH
        TIME ZONE NOT NULL DEFAULT CURRENT_TIMESTAMP,
        updated_at TIMESTAMP
    WITH
        TIME ZONE NOT NULL DEFAULT CURRENT_TIMESTAMP
);

-- Shopping Cart Items
CREATE TABLE IF NOT EXISTS cart_item (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4 (),
    customer_id UUID NOT NULL REFERENCES users_customer (user_id) ON DELETE CASCADE,
    model_id UUID NOT NULL REFERENCES model (id) ON DELETE CASCADE,
    material_id UUID NOT NULL REFERENCES material (id) ON DELETE RESTRICT,
    quantity INTEGER NOT NULL DEFAULT 1 CHECK (quantity >= 1),
    notes TEXT,
    created_at TIMESTAMP
    WITH
        TIME ZONE NOT NULL DEFAULT CURRENT_TIMESTAMP,
        updated_at TIMESTAMP
    WITH
        TIME ZONE NOT NULL DEFAULT CURRENT_TIMESTAMP,
        CONSTRAINT unique_cart_item_per_customer UNIQUE (
            customer_id,
            model_id,
            material_id
        )
);

-- ============================================================================
-- 4. SHIPPING
-- ============================================================================

-- Global Shipping Options
CREATE TABLE IF NOT EXISTS shipping_option (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4 (),
    name VARCHAR(100) NOT NULL,
    type VARCHAR(30) NOT NULL DEFAULT 'HOME_DELIVERY',
    base_fee DECIMAL(10, 2) NOT NULL,
    is_active BOOLEAN NOT NULL DEFAULT TRUE,
    created_at TIMESTAMP
    WITH
        TIME ZONE NOT NULL DEFAULT CURRENT_TIMESTAMP,
        updated_at TIMESTAMP
    WITH
        TIME ZONE NOT NULL DEFAULT CURRENT_TIMESTAMP
);

-- Customer Saved Addresses
CREATE TABLE IF NOT EXISTS saved_address (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4 (),
    customer_id UUID NOT NULL REFERENCES users_customer (user_id) ON DELETE CASCADE,
    name VARCHAR(100) NOT NULL,
    address_type VARCHAR(30) NOT NULL,
    address_details TEXT NOT NULL,
    is_default BOOLEAN NOT NULL DEFAULT FALSE,
    created_at TIMESTAMP
    WITH
        TIME ZONE NOT NULL DEFAULT CURRENT_TIMESTAMP,
        updated_at TIMESTAMP
    WITH
        TIME ZONE NOT NULL DEFAULT CURRENT_TIMESTAMP
);

-- ============================================================================
-- 5. ORDERS
-- ============================================================================

-- Order table
CREATE TABLE IF NOT EXISTS "order" (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4 (),
    customer_id UUID NOT NULL REFERENCES users_customer (user_id) ON DELETE RESTRICT,
    assignee_id UUID REFERENCES users_employee (user_id) ON DELETE SET NULL,
    status VARCHAR(20) NOT NULL DEFAULT 'PENDING',
    ship_snapshot JSONB NOT NULL,
    total_price DECIMAL(10, 2) NOT NULL,
    notes TEXT,
    tracking_number VARCHAR(100),
    creation_date TIMESTAMP
    WITH
        TIME ZONE NOT NULL DEFAULT CURRENT_TIMESTAMP,
        updated_at TIMESTAMP
    WITH
        TIME ZONE NOT NULL DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX idx_order_customer_id ON "order" (customer_id);

CREATE INDEX idx_order_status ON "order" (status);

-- Order Items
CREATE TABLE IF NOT EXISTS order_item (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4 (),
    order_id UUID NOT NULL REFERENCES "order" (id) ON DELETE CASCADE,
    model_id UUID REFERENCES model (id) ON DELETE SET NULL, -- Model could be deleted, but record remains
    material_id UUID REFERENCES material (id) ON DELETE RESTRICT,
    item_number INTEGER NOT NULL,
    quantity INTEGER NOT NULL DEFAULT 1,
    price_snapshot DECIMAL(10, 2) NOT NULL,
    slicing_info_snapshot JSONB,
    notes TEXT,
    CONSTRAINT unique_item_number_per_order UNIQUE (order_id, item_number)
);

-- Order Status Log
CREATE TABLE IF NOT EXISTS order_log (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4 (),
    order_id UUID NOT NULL REFERENCES "order" (id) ON DELETE CASCADE,
    updated_by_id UUID REFERENCES users_employee (user_id) ON DELETE SET NULL,
    previous_status VARCHAR(20),
    new_status VARCHAR(20) NOT NULL,
    notes TEXT,
    timestamp TIMESTAMP
    WITH
        TIME ZONE NOT NULL DEFAULT CURRENT_TIMESTAMP
);

-- ============================================================================
-- 6. DISCOUNTS
-- ============================================================================

-- Base Discount
CREATE TABLE IF NOT EXISTS discount (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4 (),
    name VARCHAR(255) NOT NULL,
    description TEXT,
    start_date TIMESTAMP
    WITH
        TIME ZONE NOT NULL,
        due_date TIMESTAMP
    WITH
        TIME ZONE,
        min_price DECIMAL(10, 2) NOT NULL DEFAULT 0,
        max_discount DECIMAL(10, 2),
        works_on VARCHAR(20) NOT NULL DEFAULT 'ORDER_SUBTOTAL',
        is_fixed BOOLEAN NOT NULL DEFAULT FALSE,
        dis_value DECIMAL(10, 2) NOT NULL,
        is_active BOOLEAN NOT NULL DEFAULT TRUE,
        created_at TIMESTAMP
    WITH
        TIME ZONE NOT NULL DEFAULT CURRENT_TIMESTAMP,
        updated_at TIMESTAMP
    WITH
        TIME ZONE NOT NULL DEFAULT CURRENT_TIMESTAMP
);

-- Global Discount
CREATE TABLE IF NOT EXISTS global_discount (
    discount_id UUID PRIMARY KEY REFERENCES discount (id) ON DELETE CASCADE,
    priority INTEGER NOT NULL DEFAULT 0
);

-- Coupon
CREATE TABLE IF NOT EXISTS coupon (
    discount_id UUID PRIMARY KEY REFERENCES discount (id) ON DELETE CASCADE,
    coupon_code VARCHAR(50) NOT NULL UNIQUE,
    max_uses_total INTEGER,
    max_uses_per_customer INTEGER NOT NULL DEFAULT 1,
    is_stackable BOOLEAN NOT NULL DEFAULT FALSE
);

-- Order <-> Global Discount (M:N)
CREATE TABLE IF NOT EXISTS is_affected (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4 (),
    order_id UUID NOT NULL REFERENCES "order" (id) ON DELETE CASCADE,
    global_discount_id UUID NOT NULL REFERENCES global_discount (discount_id) ON DELETE RESTRICT,
    discount_snapshot_info JSONB NOT NULL,
    discount_amount DECIMAL(10, 2) NOT NULL,
    created_at TIMESTAMP
    WITH
        TIME ZONE NOT NULL DEFAULT CURRENT_TIMESTAMP,
        CONSTRAINT unique_global_discount_per_order UNIQUE (order_id, global_discount_id)
);

-- Order <-> Coupon (1:1)
CREATE TABLE IF NOT EXISTS coupon_redemption (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4 (),
    customer_id UUID NOT NULL REFERENCES users_customer (user_id) ON DELETE RESTRICT,
    coupon_id UUID NOT NULL REFERENCES coupon (discount_id) ON DELETE RESTRICT,
    order_id UUID NOT NULL UNIQUE REFERENCES "order" (id) ON DELETE CASCADE,
    discount_snapshot_info JSONB,
    discount_amount DECIMAL(10, 2) NOT NULL,
    timestamp TIMESTAMP
    WITH
        TIME ZONE NOT NULL DEFAULT CURRENT_TIMESTAMP
);

-- Trigger Function for updated_at
CREATE OR REPLACE FUNCTION update_updated_at_column()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = CURRENT_TIMESTAMP;
    RETURN NEW;
END;
$$ language 'plpgsql';

-- Triggers
CREATE TRIGGER update_model_updated_at BEFORE UPDATE ON model FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER update_material_updated_at BEFORE UPDATE ON material FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER update_cart_item_updated_at BEFORE UPDATE ON cart_item FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER update_shipping_option_updated_at BEFORE UPDATE ON shipping_option FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER update_saved_address_updated_at BEFORE UPDATE ON saved_address FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER update_order_updated_at BEFORE UPDATE ON "order" FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER update_discount_updated_at BEFORE UPDATE ON discount FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();