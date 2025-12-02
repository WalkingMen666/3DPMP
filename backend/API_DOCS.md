# 3DPMP Backend API Documentation

## Authentication
All API endpoints (except public models and materials) require authentication using Token Authentication.

Include the token in the Authorization header:
```
Authorization: Token <your-token>
```

### Auth Endpoints
- `POST /api/auth/login/` - Login with email and password
- `POST /api/auth/registration/` - Register new user
- `POST /api/auth/logout/` - Logout current user

---

## Materials API

### List Materials
```
GET /api/materials/
```
Returns all active materials. No authentication required.

**Response:**
```json
[
  {
    "id": "uuid",
    "name": "PLA",
    "density_g_cm3": "1.24",
    "price_twd_g": "0.05",
    "is_active": true
  }
]
```

---

## Cart API

### List Cart Items
```
GET /api/cart/
```
Returns all cart items for the authenticated user.

### Add to Cart
```
POST /api/cart/
```
**Body:**
```json
{
  "model": "model-uuid",
  "material": "material-uuid",
  "quantity": 1,
  "notes": "optional notes"
}
```

### Update Cart Item
```
PATCH /api/cart/{id}/
```
**Body:**
```json
{
  "quantity": 2,
  "notes": "updated notes"
}
```

### Remove Cart Item
```
DELETE /api/cart/{id}/
```

### Clear Cart
```
DELETE /api/cart/clear/
```

### Cart Summary
```
GET /api/cart/summary/
```
Returns cart summary with estimated total.

---

## Models API

### Public Models (Marketplace)
```
GET /api/public-models/
```
Returns all PUBLIC visibility models. No authentication required.

Query parameters:
- `is_featured=true` - Filter featured models only
- `category=Art` - Filter by category

### Get Model Detail
```
GET /api/public-models/{id}/
```

### My Models (Owner)
```
GET /api/models/
```
Returns all models owned by the authenticated user.

### Upload Model
```
POST /api/models/
```
**Body (multipart/form-data):**
```
model_name: "My Model"
description: "Description"
visibility: "PUBLIC" | "PRIVATE" | "UNLISTED"
file: <file upload>
```

### Update Model
```
PATCH /api/models/{id}/
```

### Delete Model
```
DELETE /api/models/{id}/
```

---

## Orders API

### List Orders
```
GET /api/orders/
```
Returns all orders for the authenticated customer.

### Get Order Detail
```
GET /api/orders/{id}/
```

### Create Order
```
POST /api/orders/
```
**Body:**
```json
{
  "shipping_option_id": "uuid",
  "saved_address_id": "uuid",
  "notes": "optional order notes",
  "coupon_code": "optional coupon"
}
```
Creates an order from current cart items. Clears cart after successful order.

### Cancel Order
```
POST /api/orders/{id}/cancel/
```
Only works for PENDING orders.

---

## Shipping API

### List Shipping Options
```
GET /api/shipping-options/
```
Returns all active shipping options.

### Saved Addresses
```
GET /api/addresses/
POST /api/addresses/
PATCH /api/addresses/{id}/
DELETE /api/addresses/{id}/
```

---

## API Documentation (Swagger/OpenAPI)
- Swagger UI: `/api/docs/`
- ReDoc: `/api/redoc/`
- OpenAPI Schema: `/api/schema/`
