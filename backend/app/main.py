from fastapi import FastAPI
from app.database import engine, Base
from app.models import department, user, employee, employee_document, audit_log, leave, contract, attendance, recruitment, performance, notification, disciplinary, payroll, exit, training
from app.routers import (
    auth,
    contracts,
    employees,
    leave as leave_api,
    modules,
    attendance,
    payroll as payroll_api,
    performance as performance_api,
    disciplinary as disciplinary_api,
    exit as exit_api,
    onboarding,
    recruitment,
    notifications,
    training as training_api,
)
from app.services.migrations import (
    upgrade_department_catalog,
    upgrade_notification_center,
    upgrade_leave_approval,
    upgrade_onboarding_contracts,
    upgrade_recruitment_pipeline,
    upgrade_recruitment_workflow,
    upgrade_recruitment_onboarding,
    upgrade_monthly_performance,
    upgrade_employee_profile_auth,
    upgrade_leave_audit,
    upgrade_legacy_employee_profile,
    upgrade_employee_profile_photo,
    upgrade_contract_workflow,
    upgrade_hr_action_queues,
    upgrade_payroll_controls,

    upgrade_performance_nominations,
    upgrade_disciplinary_enhancements,
    upgrade_disciplinary_payroll_deduction,
    upgrade_exit_clearance_items,
    upgrade_exit_full,)
from fastapi.middleware.cors import CORSMiddleware

Base.metadata.create_all(bind=engine)
upgrade_department_catalog()
upgrade_notification_center()
upgrade_recruitment_pipeline()
upgrade_recruitment_workflow()
upgrade_recruitment_onboarding()
upgrade_monthly_performance()
upgrade_performance_nominations()
upgrade_employee_profile_auth()
upgrade_onboarding_contracts()
upgrade_leave_approval()
upgrade_leave_audit()
upgrade_legacy_employee_profile()
upgrade_employee_profile_photo()
upgrade_contract_workflow()
upgrade_hr_action_queues()
upgrade_payroll_controls()
upgrade_disciplinary_enhancements()
upgrade_exit_clearance_items()
upgrade_exit_full()
upgrade_disciplinary_payroll_deduction()

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
app.include_router(attendance.router, prefix="/api/attendance", tags=["4. Attendance"])
app.include_router(recruitment.router, prefix="/api/recruitment", tags=["5. Recruitment"])
app.include_router(notifications.router, prefix="/api/notifications", tags=["12. Notifications"])
app.include_router(onboarding.router, prefix="/api/onboarding", tags=["6. Onboarding"])
app.include_router(contracts.router, prefix="/api/contracts", tags=["7. Contracts"])
app.include_router(payroll_api.router, prefix="/api/payroll", tags=["8. Payroll"])
app.include_router(performance_api.router, prefix="/api/performance", tags=["9. Performance"])
app.include_router(disciplinary_api.router, prefix="/api/disciplinary", tags=["10. Disciplinary"])
app.include_router(exit_api.router, prefix="/api/exit", tags=["11. Exit & Clearance"])
app.include_router(modules.router, prefix="/api", tags=["4. HR Modules"])
app.include_router(training_api.router, prefix="/api/training", tags=["13. Training"])

@app.get("/")
def home():
    return {"status": "Success", "security": "JWT & Bcrypt Hashing Active"}
