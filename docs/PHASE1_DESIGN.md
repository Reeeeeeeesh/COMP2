# Phase 1: Project Setup & Core Architecture

## 1. Requirements & Scope

### Required Features
- **Model A**: Base salary adjustment based on revenue delta and adjustment factor, with caps (+20%) and floors (-10%).
- **Model B**:  
  - *Pool method*: bonus = pool_share × adjusted revenue  
  - *Target method*: bonus = target_bonus × performance_score (capped at 100%)
- **Data Input**: CSV upload and manual entry UI
- **Scenario Controls**: revenue_delta, adjustment_factor sliders; toggle for pool vs target method
- **Regulatory Guardrails**: deferral thresholds, malus/clawback flags, ratio alerts
- **Backtesting**: year‑on‑year historical simulation
- **Dashboard**: upload, controls, results table & charts

### MVP vs Deferred
**MVP (Phases 1–3) :**
- CSV/manual data import
- Model A & B calculation engine
- Basic backend API endpoints (/ping/, upload, calculate)
- Frontend: React + MUI for upload, controls, results table
- PostgreSQL schema & migrations

**Deferred (Phases 4+):**
- Regulatory rules & UI display
- Historical backtesting & charting
- Advanced error handling, performance tuning, deployment scripts

## 2. Tech Stack
- **Backend**: Python, Django, Django REST Framework, django-cors-headers
- **Database**: PostgreSQL (via psycopg2-binary)
- **Frontend**: React, Material‑UI, Axios
- **Testing**: Django test framework / pytest, Jest & React Testing Library

## 3. High‑Level Architecture
- **Frontend (React SPA):** communicates with backend via REST API
- **Backend (Django REST API):**  
  - `compensation_tool` project  
  - `employees` app for models & serializers  
  - `compensation_engine` module for business logic
- **Database (PostgreSQL):** stores Employee & HistoricalPerformance
- **Data flow:**
  1. User uploads CSV / submits manual form → POST to `/api/upload-data/` or `/api/employees/`
  2. Data persisted to DB
  3. User sets scenario → POST `/api/calculate/` → engine runs Model A/B → JSON results
  4. Frontend renders table & charts

## 4. Database Schema

### Employee
| Field               | Type          | Notes                        |
|---------------------|---------------|------------------------------|
| id                  | AutoField PK  |                              |
| name                | CharField(100)|                              |
| base_salary         | DecimalField  | max_digits=12, decimal_places=2 |
| pool_share          | DecimalField  | % of revenue (0–1)           |
| target_bonus        | DecimalField  | currency amount              |
| performance_score   | DecimalField  | 0–1                          |
| last_year_revenue   | DecimalField  |                              |
| created_at, updated_at | DateTime   | auto timestamps              |

### HistoricalPerformance
| Field               | Type          | Notes                        |
|---------------------|---------------|------------------------------|
| id                  | AutoField PK  |                              |
| employee            | ForeignKey    | → Employee                   |
| year                | IntegerField  |                              |
| revenue             | DecimalField  |                              |
| performance_score   | DecimalField  |                              |
| (additional metrics)|               | as needed                    |

*Constants* (caps/floors, deferral thresholds) will be maintained in a config module.
