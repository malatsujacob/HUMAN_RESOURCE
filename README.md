# Chap Chap Africa HRMS

HR management system with a React/Vite frontend, FastAPI backend, and PostgreSQL database.

## Run with Docker Compose

1. Copy `.env.example` to `.env` and set a unique database password and secret key.
2. Start the application with `docker compose up --build`.
3. Open the frontend at <http://localhost:3000> and the API docs at <http://localhost:8000/docs>.

The compose file persists PostgreSQL data in a named volume and candidate CV uploads in `uploads/`.

## Run locally

Set `DATABASE_URL` and `SECRET_KEY` in the environment, then install the backend dependencies from `backend/requirements.txt`. Start the API from `backend/` with `uvicorn app.main:app --reload`.

In another terminal, install the frontend dependencies from `frontend/` and run `npm run dev`. Set `VITE_API_BASE_URL` when the API is not available at `http://localhost:8000/api`.

## Project layout

- `backend/app/main.py` registers the API routers and startup migrations.
- `backend/app/routers/` contains FastAPI route modules.
- `backend/app/models/` contains SQLAlchemy models.
- `backend/migrations/` contains SQL migration files.
- `frontend/src/` contains the React application.
- Department selectors use one canonical catalog: Tech, Finance, Sales, Customer Support, Security, Catering, Marketing, and Administration/Management. The backend normalizes known legacy department aliases at startup; unknown legacy mappings remain visible for correction and are excluded from payroll totals.

## Payroll control center

The Payroll page provides cycle totals, cost allocation, compliance and overtime exceptions, payroll-register reconciliations, stage approvals, audit search, pay-period trends, and employee payslip/payment-election views. HR and Finance roles can review organization-wide payroll; HOD access is restricted to their department; employee payslips and payment elections are employee-scoped.

Bank-disbursement and tax-funding reconciliation files are parsed in the browser as CSV. Use `employee_id` or `employee_number` plus an `amount`, `net_salary`, or `paye_tax` column. The saved reconciliation includes source totals, file name, and employee-level discrepancies; the original CSV is not uploaded or retained.

Payroll cycle and reconciliation records are stored in PostgreSQL. Existing records are migrated at backend startup. Cost-center, jurisdiction verification, tax-form verification, employer contribution, bonus, overtime-pay, and retro-pay fields are available for the control views; amounts are not inferred when source records do not supply them.

**Production security prerequisites:** this application currently authenticates with its built-in JWT/password login, not an external SSO provider. The deployment also needs an HTTPS reverse proxy and encrypted PostgreSQL storage/backups; the current Compose example does not configure either, and employee bank account values are stored in the employee record. Do not treat the payroll area as meeting SSO or encryption-at-rest requirements until those infrastructure and data-protection changes are completed.
