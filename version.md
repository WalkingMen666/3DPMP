# **Software Version Matrix**

Target Base Image: ubuntu:25.04 (Plucky Puffin)  
Deployment Strategy: Use default system packages (apt) where possible to minimize external dependencies.

## **Core Runtime**

| Component | Version (Approx.) | Package Name | Notes |
| :---- | :---- | :---- | :---- |
| **OS Kernel** | Linux 6.14+ | linux-image-generic | Base system kernel. |
| **Python** | **3.13.x** | python3 | Ubuntu 25.04 defaults to Python 3.13. |
| **Node.js** | **20.x or 22.x** | nodejs | System repo usually provides the latest LTS (20 or 22). |

## **Database & Caching**

| Component | Version | Package Name | Notes |
| :---- | :---- | :---- | :---- |
| **PostgreSQL** | **18.x** | postgresql-18 | xxx |
| **Redis** | **7.4.x** | redis-server | Standard stable release provided by Ubuntu. |

## **Web Server & Routing**

| Component | Version | Package Name | Notes |
| :---- | :---- | :---- | :---- |
| **Nginx** | **1.26.x** | nginx | Internal router for the container setup. |
| **Caddy** | **2.9.x** | caddy | *Note: Caddy usually needs the external repo, but 25.04 may include a recent version in universe.* |

## **3D Printing Core**

| Component | Version | Package Name | Notes |
| :---- | :---- | :---- | :---- |
| **PrusaSlicer** | **2.8.x / 2.9.x** | prusaslicer | *Critical:* If the repo version is too old (\< 2.6) for Arachne engine support, we may need to switch to AppImage. Assuming 25.04 updates this to a recent stable build. |

## **Python Dependencies (Pip)**

*Managed by requirements.txt, not system apt*

* **Django:** 5.1+ (Compatible with Python 3.13)  
* **Django REST Framework:** 3.15+  
* **Celery:** 5.5+