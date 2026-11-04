from fastapi import FastAPI
from app.database import engine, Base
from app.models import department, user, employee, audit_log, leave, contract, attendance, recruitment, performance, disciplinary, payroll
from app.api import auth, employees, leave as leave_api, modules
from fastapi.middleware.cors import CORSMiddleware

Base.metadata.create_all(bind=engine)

app = FastAPI(title="Chap Chap HRMS - Secure Backend")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(auth.router, prefix="/api/auth", tags=["1. Authentication"])
app.include_router(employees.router, prefix="/api/employees", tags=["2. Employee Directory"])
app.include_router(leave_api.router, prefix="/api/leave", tags=["3. Leave Management"])
app.include_router(modules.router, prefix="/api", tags=["4. HR Modules"])

@app.get("/")
def home():
    return {"status": "Success", "security": "JWT & Bcrypt Hashing Active"}
