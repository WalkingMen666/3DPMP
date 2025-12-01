# Database SQL Files

This directory contains SQL statements for database construction and data population.

## Files

| File | Description |
|------|-------------|
| [schema.sql](schema.sql) | Database schema definition (CREATE TABLE statements) |
| [seed_data.sql](seed_data.sql) | Sample data for development and testing |

## Usage

### Option 1: Using Django Migrations (Recommended)

Django automatically manages the database schema. Use Django commands:

```bash
# Create migrations from models
podman-compose exec backend python manage.py makemigrations

# Apply migrations to database
podman-compose exec backend python manage.py migrate

# Load seed data (if using Django fixtures)
podman-compose exec backend python manage.py loaddata seed_data
```

### Option 2: Direct SQL Execution

For manual database setup or documentation purposes:

```bash
# Connect to PostgreSQL
podman-compose exec db psql -U postgres -d 3dpmp

# Execute schema
\i /path/to/schema.sql

# Execute seed data
\i /path/to/seed_data.sql
```

Or from host:

```bash
# Schema
cat database/schema.sql | podman-compose exec -T db psql -U postgres -d 3dpmp

# Seed data
cat database/seed_data.sql | podman-compose exec -T db psql -U postgres -d 3dpmp
```

## Schema Overview

### Entity Relationship Summary

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                           USER AUTHENTICATION                                │
├─────────────────────────────────────────────────────────────────────────────┤
│  users_user ──┬── users_customer (1:1 Specialization)                       │
│               └── users_employee (1:1 Specialization)                       │
└─────────────────────────────────────────────────────────────────────────────┘

┌─────────────────────────────────────────────────────────────────────────────┐
│                              3D MODELS                                       │
├─────────────────────────────────────────────────────────────────────────────┤
│  model ──┬── model_image (1:N)                                              │
│          └── model_review_log (1:N, by employee)                            │
└─────────────────────────────────────────────────────────────────────────────┘

┌─────────────────────────────────────────────────────────────────────────────┐
│                           MATERIALS & CART                                   │
├─────────────────────────────────────────────────────────────────────────────┤
│  material ◄── cart_item ──► model                                           │
│                    │                                                         │
│                    ▼                                                         │
│              users_customer                                                  │
└─────────────────────────────────────────────────────────────────────────────┘

┌─────────────────────────────────────────────────────────────────────────────┐
│                              SHIPPING                                        │
├─────────────────────────────────────────────────────────────────────────────┤
│  shipping_option (Global options, no FK from order)                         │
│  saved_address ──► users_customer                                           │
└─────────────────────────────────────────────────────────────────────────────┘

┌─────────────────────────────────────────────────────────────────────────────┐
│                         ORDERS (Immutable Snapshots)                         │
├─────────────────────────────────────────────────────────────────────────────┤
│  order ──┬── order_item (1:N, with price_snapshot)                          │
│          ├── order_log (1:N, status history)                                │
│          ├── is_affected (M:N to global_discount)                           │
│          └── coupon_redemption (1:1 to coupon)                              │
│                                                                              │
│  NOTE: order.ship_snapshot is JSON, NOT a FK to shipping tables!            │
└─────────────────────────────────────────────────────────────────────────────┘

┌─────────────────────────────────────────────────────────────────────────────┐
│                         DISCOUNTS (EER Specialization)                       │
├─────────────────────────────────────────────────────────────────────────────┤
│  discount ──┬── global_discount (1:1 Specialization, auto-apply)            │
│             └── coupon (1:1 Specialization, user-entered code)              │
└─────────────────────────────────────────────────────────────────────────────┘
```

## Sample Data Summary

The seed data includes:

### Users
- 1 Admin user (`admin@3dpmp.com`)
- 2 Employee users
- 3 Customer users (1 with Google OAuth)

### Materials
- 12 materials (PLA, PETG, ABS, TPU variants)

### Shipping Options
- 6 options (Home delivery, Convenience store, Self-pickup)

### 3D Models
- 7 models with various visibility statuses

### Discounts
- 3 Global discounts (auto-apply)
- 3 Coupons (user-entered)

### Orders
- 3 sample orders in different states (COMPLETED, PRINTING, PENDING)

## Notes

1. **Password Hashing**: The seed data uses placeholder password hashes. In production, use Django's `createsuperuser` command or the registration API to create users with properly hashed passwords.

2. **UUID Generation**: PostgreSQL's `uuid-ossp` extension is used for UUID generation. Django uses Python's `uuid4()` by default.

3. **Timestamps**: All timestamp columns use `TIMESTAMP WITH TIME ZONE` for proper timezone handling.

4. **JSON Columns**: `ship_snapshot`, `slicing_info`, `discount_snapshot_info` use PostgreSQL's `JSONB` type for efficient JSON storage and querying.
