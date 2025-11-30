# **Project Requirements: 3D Printing and Model-sharing Platform (3DPMP)**

## **1\. Project Overview**

**3DPMP** is a web-based platform that combines a 3D model sharing community with professional 3D printing services.

* **Users** can upload STL files, view auto-generated slicing estimates (price/material), manage personal address books, and place printing orders.  
* **Employees** can manage orders, review public models, and update printing status.  
* **System** features asynchronous slicing integration (PrusaSlicer), immutable order snapshots (shipping/pricing), and a complex discount system.

## **2\. Tech Stack & Infrastructure**

### **Backend**

* **Language:** Python 3.10+  
* **Framework:** Django 5.x  
* **API:** Django REST Framework (DRF)  
* **Task Queue:** Celery (for async slicing tasks)  
* **Broker/Cache:** Redis  
* **Slicing Engine:** PrusaSlicer CLI (installed in the worker container)

### **Frontend**

* **Framework:** Vue.js 3 (Vite)  
* **State Management:** Pinia  
* **UI Library:** TailwindCSS or Element Plus (Agent's choice based on standard boilerplate)  
* **HTTP Client:** Axios

### **Database & Storage**

* **RDBMS:** PostgreSQL 16 (Primary Data)  
* **File Storage:** **Alist** (Existing S3 Service on Host) via django-storages \+ boto3.  
  * *Configuration:* Django connects to Host IP (e.g., port 5244). Backed by **Local Storage** mount in Alist (avoid using Cloud Drives to prevent latency).

### **Infrastructure (Proxmox Deployment)**

* **Containerization:** Docker & Docker Compose.  
* **Routing:**  
  * **Host Level:** Caddy (Reverse Proxy, HTTPS management).  
  * **Container Level:** Internal Nginx (Serves Vue static files and proxies /api to Django).

## **3\. System Architecture**

The system follows a **Shared Database** pattern with separated API and Worker services.

graph LR  
    FE\[Vue.js Frontend\] \--\> NGINX\[Internal Nginx\]  
    NGINX \-- /api \--\> API\[Django API Server\]  
    NGINX \-- / \--\> STATIC\[Vue Static Files\]  
      
    API \-- Enqueue Task \--\> REDIS\[Redis Broker\]  
    REDIS \-- Consume Task \--\> WORKER\[Celery Worker / Slicer Wrapper\]  
      
    WORKER \-- Call \--\> PRUSA\[PrusaSlicer CLI\]  
      
    API \<--\> DB\[(PostgreSQL)\]  
    WORKER \<--\> DB  
      
    API \<--\> ALIST\[(Alist S3 API)\]  
    WORKER \<--\> ALIST

## **4\. Database Schema (Relation Schema)**

The database design strictly follows EER-to-Relational mapping rules, including **Specialization**, **Snapshots**, and **Associative Entities**. Use the following DBML as the **Source of Truth** for creating Django Models.

//// \--- User & Auth (Specialization) \---  
Table USER {  
  user\_id varchar \[pk\] // UUID  
  email varchar \[unique, not null\]  
  password\_hash varchar \[null\] // Nullable for OAuth  
  auth\_provider varchar \[not null\] // 'local' or 'google'  
  creation\_date timestamp \[not null\]  
}

Table CUSTOMER {  
  user\_id varchar \[pk, ref: \- USER.user\_id\] // IS-A User  
}

Table EMPLOYEE {  
  user\_id varchar \[pk, ref: \- USER.user\_id\] // IS-A User  
  employee\_name varchar \[not null\]  
  is\_admin bool \[not null, default: false\]  
}

//// \--- Models & Files \---  
Table MODEL {  
  model\_id varchar \[pk\] // UUID  
  owner\_id varchar \[not null, ref: \> USER.user\_id\]  
  model\_name varchar \[not null\]  
  visibility\_status varchar \[not null, default: 'PRIVATE'\] // PRIVATE, PENDING, PUBLIC, REJECTED  
  stl\_file\_path varchar \[not null\] // Relative path in Alist  
  gcode\_file\_path varchar \[null\]  
  slicing\_info jsonb \[null\] // Stores material usage, print time  
}

Table MODEL\_IMAGE {  
  image\_id varchar \[pk\]  
  model\_id varchar \[not null, ref: \> MODEL.model\_id\]  
  image\_path varchar \[not null\]  
}

Table MODEL\_REVIEW\_LOG {  
  log\_id varchar \[pk\]  
  model\_id varchar \[not null, ref: \> MODEL.model\_id\]  
  reviewer\_id varchar \[not null, ref: \> EMPLOYEE.user\_id\]  
  previous\_status varchar \[null\]  
  new\_status varchar \[not null\]  
  reason text \[null\]  
  timestamp timestamp \[not null\]  
}

//// \--- Materials & Cart \---  
Table MATERIAL {  
  material\_id varchar \[pk\]  
  name varchar \[unique, not null\]  
  density\_g\_cm2 decimal(10, 5\) \[not null\]  
  price\_twd\_g decimal(10, 2\) \[not null\]  
}

Table CART\_ITEM {  
  cart\_item\_id varchar \[pk\]  
  customer\_id varchar \[not null, ref: \> CUSTOMER.user\_id\]  
  model\_id varchar \[not null, ref: \> MODEL.model\_id\]  
  material\_id varchar \[not null, ref: \> MATERIAL.material\_id\]  
  quantity int \[not null, default: 1\]  
  notes text \[null\]  
}

//// \--- Shipping \---  
// Global options defined by Admin  
Table SHIPPING\_OPTION {  
  option\_id varchar \[pk\]  
  name varchar \[not null\] // e.g., 'Black Cat Delivery'  
  type varchar \[not null\] // e.g., 'HOME\_DELIVERY'  
  base\_fee decimal(10, 2\) \[not null\]  
  is\_active bool \[not null, default: true\]  
}

// Personal address book for Customers  
Table SAVED\_ADDRESS {  
  address\_id varchar \[pk\]  
  customer\_id varchar \[not null, ref: \> CUSTOMER.user\_id\]  
  name varchar \[not null\] // e.g., 'My Home'  
  address\_type varchar \[not null\] // Matches SHIPPING\_OPTION.type  
  address\_details text \[not null\]  
}

//// \--- Orders (Immutable Snapshots) \---  
Table "ORDER" {  
  order\_id varchar \[pk\]  
  customer\_id varchar \[not null, ref: \> CUSTOMER.user\_id\]  
  assignee\_id varchar \[null, ref: \> EMPLOYEE.user\_id\]  
  status varchar \[not null, default: 'PENDING'\]  
    
  // Shipping Snapshot: Stores JSON {service\_name, fee, address\_details}  
  // CRITICAL: No Foreign Keys to SHIPPING\_OPTION or SAVED\_ADDRESS here.  
  ship\_snapshot jsonb \[not null\] 

  total\_price decimal(10, 2\) \[not null\]  
  creation\_date timestamp \[not null\]  
}

Table ORDER\_ITEM {  
  order\_item\_id varchar \[pk\]  
  order\_id varchar \[not null, ref: \> "ORDER".order\_id\]  
  model\_id varchar \[not null, ref: \> MODEL.model\_id\]  
  material\_id varchar \[not null, ref: \> MATERIAL.material\_id\]  
  item\_number int \[not null\]  
  quantity int \[not null\]  
  // Price Snapshot: Price at time of purchase  
  price\_snapshot decimal(10, 2\) \[not null\]   
  slicing\_info\_snapshot jsonb \[null\]  
}

Table ORDER\_LOG {  
  log\_id varchar \[pk\]  
  order\_id varchar \[not null, ref: \> "ORDER".order\_id\]  
  updated\_by varchar \[not null, ref: \> EMPLOYEE.user\_id\]  
  new\_status varchar \[not null\]  
  timestamp timestamp \[not null\]  
}

//// \--- Discounts (Superclass/Subclass) \---  
Table DISCOUNT {  
  discount\_id varchar \[pk\]  
  name varchar \[not null\]  
  start\_date timestamp \[not null\]  
  due\_date timestamp \[null\]  
  min\_price decimal(10, 2\) \[not null, default: 0\]  
  max\_discount decimal(10, 2\) \[null\]  
  works\_on varchar \[not null, default: 'ORDER\_SUBTOTAL'\]  
  is\_fixed bool \[not null, default: false\]  
  dis\_value decimal(10, 2\) \[not null\]  
}

Table GLOBAL\_DISCOUNT {  
  discount\_id varchar \[pk, ref: \- DISCOUNT.discount\_id\]  
}

Table COUPON {  
  discount\_id varchar \[pk, ref: \- DISCOUNT.discount\_id\]  
  coupon\_code varchar \[unique, not null\]  
  max\_uses\_total int \[null\]  
  max\_uses\_per\_customer int \[null, default: 1\]  
}

// M:N Link for Global Discounts (Multiple allowed)  
Table IS\_AFFECTED {  
  order\_id varchar \[not null, ref: \> "ORDER".order\_id\]  
  global\_discount\_id varchar \[not null, ref: \> GLOBAL\_DISCOUNT.discount\_id\]  
  discount\_snapshot\_info jsonb \[not null\] // Snapshot of discount rules  
}

// 1:1 Link for Coupon (Max 1 per order) via Unique Constraint  
Table COUPON\_REDEMPTION {  
  redemption\_id varchar \[pk\]  
  customer\_id varchar \[not null, ref: \> CUSTOMER.user\_id\]  
  coupon\_id varchar \[not null, ref: \> COUPON.discount\_id\]  
  order\_id varchar \[not null, unique, ref: \> "ORDER".order\_id\]   
  timestamp timestamp \[not null\]  
}

## **5\. Functional Requirements & Detailed Business Logic**

### **5.1 Authentication & Roles (AMMS)**

* **Sign Up / Login:**  
  * **Google OAuth:** Primary method. On first login, automatically creates a USER record and a CUSTOMER profile record. auth\_provider set to 'google'.  
  * **Local Auth:** Standard email/password registration.  
* **Role-Based Access Control (RBAC):**  
  * **Guest:** Can browse PUBLIC models only.  
  * **Customer:** Can upload models, manage SAVED\_ADDRESS, use Cart, place Orders, view own Order history.  
  * **Employee:** Can access the Employee Dashboard to view PENDING\_REVIEW models and PENDING orders.  
  * **Admin:** Has all Employee permissions \+ management of SHIPPING\_OPTION, GLOBAL\_DISCOUNT, MATERIAL, and Employee accounts.

### **5.2 Model Management (MFMS & ASIS)**

* **Upload & Slicing Flow:**  
  1. User uploads .stl file.  
  2. Backend saves file to Alist (S3), creates MODEL record with visibility\_status='PRIVATE' and slicing\_info=NULL.  
  3. Backend triggers async Celery task.  
  4. **Worker** downloads file, runs PrusaSlicer CLI, calculates filament usage/time.  
  5. **Worker** updates MODEL.slicing\_info (JSONB) with results.  
  6. Frontend polls for status change to display price estimate.  
* **Public Review Workflow:**  
  * **Submission:** User changes status from PRIVATE to PENDING\_REVIEW.  
  * **Review:** Employee views list of PENDING\_REVIEW models.  
  * **Approval:** Employee sets status to PUBLIC.  
  * **Rejection:** Employee sets status to REJECTED. **Mandatory:** Employee must enter a reason.  
  * **Logging:** Every status change by an Employee MUST create a MODEL\_REVIEW\_LOG entry containing reviewer\_id, old\_status, new\_status, and reason.

### **5.3 Order & Shipping System (OPMS)**

* **Cart (Mutable):** CART\_ITEM is a temporary holding area. Prices here are "estimates" based on current material prices.  
* **Order Creation (Immutable Snapshot):**  
  * When an Order is created, CART\_ITEMs are converted to ORDER\_ITEMs.  
  * **Price Snapshot:** ORDER\_ITEM.price\_snapshot is calculated and saved permanently (current MATERIAL.price \* slicing\_info.weight).  
  * **Shipping Snapshot:** The system takes the selected SHIPPING\_OPTION (e.g., "Black Cat", $100) and the user's SAVED\_ADDRESS details. These are combined into a JSON object (e.g., { "service": "Black Cat", "fee": 100, "address": "Taipei City..." }) and saved to ORDER.ship\_snapshot.  
  * *Constraint:* ORDER table MUST NOT have foreign keys to mutable shipping/address tables.

### **5.4 Discount System Logic**

* **Global Discounts (M:N):**  
  * Admin configures auto-apply rules (e.g., "Summer Sale: 10% off").  
  * On checkout, system finds ALL applicable GLOBAL\_DISCOUNTs.  
  * Records are created in IS\_AFFECTED table linking Order to Discounts, storing the discount snapshot (value at time of purchase).  
* **Coupons (1:1):**  
  * User manually enters a code (e.g., "WELCOME2025").  
  * System validates: Code exists, is active, usage limit not reached.  
  * **Constraint:** Max **1** Coupon per Order.  
  * Record is created in COUPON\_REDEMPTION table. The unique constraint on order\_id in this table enforces the "one coupon per order" rule at the database level.

## **6\. Development Guidelines**

### **6.1 Backend (Django)**

* **App Structure:** Split into apps/users, apps/models, apps/orders, apps/shipping, apps/discounts.  
* **Snapshot Implementation:** Override the perform\_create or create method in OrderSerializer to handle the logic of fetching current shipping/material data and saving them as JSON snapshots.  
* **Admin Panel:** Register all models to Django Admin for easy management during development.

### **6.2 Frontend (Vue)**

* **Polling:** Implement a polling mechanism (e.g., every 3s) on the Model Detail page to check if slicing\_info has been populated by the worker.  
* **State:** Use Pinia to manage the Cart state locally before syncing with the backend.

### **6.3 Deployment**

* **Environment Variables:** All secrets (DB credentials, Alist keys, Google OAuth Client ID) must be loaded from .env file.  
* **Volumes:** Ensure Alist container (if running separately) or the Alist service on host has persistent storage mounted.