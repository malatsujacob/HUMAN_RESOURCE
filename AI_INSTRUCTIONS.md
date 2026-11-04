# SYSTEM INSTRUCTIONS: CHAP CHAP AFRICA "HUMAN_RESOURCE" HRMS

## 1. AI AGENT DIRECTIVES & RULES
You are an expert full-stack developer tasked with completing the "HUMAN_RESOURCE" HRMS dashboard for Chap Chap Africa. 
- **DO NOT** use Next.js, Tailwind CSS, or Docker.
- **DO NOT** rewrite the entire backend from scratch. Only add missing endpoints.
- **MUST USE:** FastAPI (Python), PostgreSQL (via SQLAlchemy), React (Vite), Vanilla CSS, Axios, and Lucide-React for icons.
- **SECURITY:** JWT authentication. Passwords hashed with Bcrypt. Role-based access (HR sees all, HOD sees department, Employee sees self).
- **DATABASE NAME:** HUMAN_RESOURCE.

## 2. STRICT FILE STRUCTURE
Maintain this exact directory structure. If a file is missing, create it.
HUMAN_RESOURCE/
├── app/
│   ├── api/          (auth.py, employees.py, leave.py, contracts.py, attendance.py, recruitment.py, payroll.py, performance.py, disciplinary.py)
│   ├── models/       (user.py, employee.py, department.py, leave.py, contract.py, attendance.py, recruitment.py, payroll.py, performance.py, disciplinary.py)
│   ├── database.py   (Engine, SessionLocal, hash_password, verify_password)
│   └── main.py       (FastAPI app, CORS, router registration)
├── frontend/
│   ├── src/
│   │   ├── components/ (Layout.jsx, Sidebar.jsx, Header.jsx, Modals)
│   │   ├── pages/      (Home.jsx, Employees.jsx, Leave.jsx, Payroll.jsx, etc.)
│   │   ├── App.jsx     (React Router setup)
│   │   ├── main.jsx
│   │   └── index.css   (Global styles, grid, tables, cards)
│   └── package.json
└── seed.py             (Populates 7 departments and Admin user)

## 3. WHAT IS ALREADY BUILT (THE BACKEND)
The backend is running on http://localhost:8000.
- Database connection and hashing are complete in database.py.
- POST /api/auth/login works and returns a JWT.
- GET and POST /api/employees/ works.
- POST /api/leave/request works.
- Models for all 13 modules have been created in pp/models/.
- **Seed data:** 7 departments (TECH, FINANCE, CUSTOMER_SUPPORT, SALES, CATERING, SECURITY, ADMINISTRATION) and an admin user (dmin@chapchapafrica.com / dmin123).

## 4. THE 13 MODULES & ROLE RULES
- **Roles:** EMPLOYEE, HOD, HR, FINANCE, MANAGEMENT.
- **Employee Directory:** HR creates, HODs view own dept, Employees view self.
- **Leave:** Employee requests, HOD approves/rejects, HR oversees.
- **Payroll:** FINANCE prepares, MANAGEMENT approves. HR cannot run payroll.
- **Disciplinary:** HR-only access. HODs only see department cases.
- **ESS (Self-Service):** Every employee logs in to see their own Payslips, Leave, Contracts, and Attendance.
