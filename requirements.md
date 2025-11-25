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

* **RDBMS:** PostgreSQL 18 (Primary Data)  
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

## **5\. Functional Requirements & Business Logic**

### **5.1 Authentication (AMMS)**

* **Google OAuth:** Primary login method. Checks email uniqueness. Creates USER \+ CUSTOMER records automatically.  
* **Roles:**  
  * Customer: Can manage SAVED\_ADDRESS, Cart, Orders.  
  * Employee: Can access Dashboard, assign tasks to self.  
  * Admin: Manage Global Discounts, Shipping Options, Materials.

### **5.2 Model Management (MFMS & ASIS)**

* **Async Slicing:**  
  1. User uploads STL \-\> API streams to Alist \-\> Creates MODEL (status=PENDING) \-\> Enqueues Task.  
  2. **Worker** downloads from Alist \-\> Runs prusa-slicer-console \-\> Parses output \-\> Updates DB.  
* **Review Flow:** User requests review \-\> PENDING\_REVIEW \-\> Employee Approves/Rejects \-\> Log in MODEL\_REVIEW\_LOG.

### **5.3 Checkout & Snapshots (OPMS)**

* **Immutable History:**  
  * When an Order is placed, CART\_ITEM data is copied to ORDER\_ITEM.  
  * price\_snapshot \= MATERIAL.price \* slicing\_info.weight.  
  * **Shipping Snapshot:** System combines selected SHIPPING\_OPTION (fee, name) and SAVED\_ADDRESS (details) into a single JSON object and saves it to ORDER.ship\_snapshot.  
* **Discounts:**  
  * **Global:** Applied automatically (can stack).  
  * **Coupon:** Applied manually (max 1). Enforced by COUPON\_REDEMPTION unique constraint on order\_id.

## **6\. Development Guidelines**

### **6.1 Backend (Django)**

* **App Structure:** Split into apps/users, apps/models, apps/orders, apps/shipping.  
* **Settings:** Use django-storages. Configure AWS\_S3\_ENDPOINT\_URL to the **Host IP** (e.g., http://192.168.1.100:5244), NOT localhost.  
* **Serializers:** Heavy use of ModelSerializer. For Order, the write-serializer should handle the snapshot logic (create method).

### **6.2 Frontend (Vue)**

* **Routing:** Use Vue Router.  
* **API:** Point Axios to /api.  
* **UI:** Create components for "Address Selector" and "Shipping Option Selector".

### **6.3 Deployment**

* **Internal Nginx:** Serves Vue dist/ on port 80, proxies /api to Django:8000.  
* **Expose:** Only expose the Internal Nginx port (e.g., 8080\) to the host machine.  
* **Caddy:** Configure host Caddy to reverse proxy the domain to localhost:8080.