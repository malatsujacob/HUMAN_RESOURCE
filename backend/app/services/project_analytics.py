from collections import Counter, defaultdict
from datetime import date, datetime, timezone

from fastapi import HTTPException
from sqlalchemy.orm import Session

from app.models.attendance import Attendance
from app.models.contract import Contract
from app.models.department import Department
from app.models.disciplinary import DisciplinaryCase
from app.models.employee import Employee
from app.models.employee_document import EmployeeDocument
from app.models.exit import EmployeeExit
from app.models.leave import LeaveRequest
from app.models.performance import PerformanceReview
from app.models.payroll import PayrollCycle, Payslip
from app.models.recruitment import Candidate, JobRequisition
from app.models.training import TrainingCourse, TrainingEnrollment, TrainingSession
from app.models.user import User

HR_ROLES = {"HR", "HR_ADMIN", "ADMIN", "MANAGEMENT", "DEVELOPER"}
FINANCE_ROLES = {"FINANCE"}


def _number(value) -> float:
    return round(float(value or 0), 2)


def _distribution(rows, key):
    counts = Counter(str(key(row) or "Not recorded") for row in rows)
    return [
        {"label": label, "value": value}
        for label, value in sorted(counts.items(), key=lambda item: (-item[1], item[0].casefold()))
    ]


def _period(value) -> str | None:
    if value is None:
        return None
    return value.strftime("%Y-%m") if hasattr(value, "strftime") else str(value)[:7]


def _monthly_counts(rows, date_key):
    counts = Counter()
    for row in rows:
        label = _period(date_key(row))
        if label:
            counts[label] += 1
    return [{"label": label, "value": counts[label]} for label in sorted(counts)]


def _metric(label: str, value, format_type: str = "number") -> dict:
    formatted = _number(value) if format_type in {"currency", "hours", "rating"} else int(value or 0)
    return {"label": label, "value": formatted, "format": format_type}


def _module(title: str, description: str, metrics: list, distribution: list, chart_title: str, trend=None) -> dict:
    return {
        "title": title,
        "description": description,
        "metrics": metrics,
        "distribution": distribution,
        "chart_title": chart_title,
        "trend": trend or [],
    }


def _payroll_report(db: Session) -> dict:
    payslips = db.query(Payslip).all()
    cycles = db.query(PayrollCycle).all()
    by_period = defaultdict(lambda: {"gross": 0.0, "net": 0.0, "tax": 0.0, "employees": 0})
    for payslip in payslips:
        row = by_period[payslip.pay_period]
        row["gross"] += _number(payslip.gross_salary)
        row["net"] += _number(payslip.net_salary)
        row["tax"] += _number(payslip.paye_tax)
        row["employees"] += 1
    periods = sorted(by_period)
    trend = [
        {
            "label": period,
            "gross": _number(by_period[period]["gross"]),
            "net": _number(by_period[period]["net"]),
            "tax": _number(by_period[period]["tax"]),
            "employees": by_period[period]["employees"],
        }
        for period in periods
    ]
    latest = by_period[periods[-1]] if periods else {}
    return _module(
        "Payroll",
        "Gross, net, and tax totals from recorded payslips by pay cycle.",
        [
            _metric("Gross payroll recorded", sum(row["gross"] for row in by_period.values()), "currency"),
            _metric("Net pay recorded", sum(row["net"] for row in by_period.values()), "currency"),
            _metric("Payslips", len(payslips)),
            _metric("Payroll cycles", len(set(by_period) | {item.pay_period for item in cycles})),
            _metric("Latest cycle gross", latest.get("gross", 0), "currency"),
        ],
        [{"label": period, "value": _number(by_period[period]["gross"])} for period in periods],
        "Gross payroll by pay cycle",
        trend,
    )


def build_project_analytics(db: Session, user: User) -> dict:
    role = (user.role or "").upper()
    if role in FINANCE_ROLES:
        payroll = _payroll_report(db)
        return {
            "generated_at": datetime.now(timezone.utc).isoformat(),
            "scope": "payroll",
            "summary": {
                "gross_payroll_recorded": payroll["metrics"][0]["value"],
                "payslips": payroll["metrics"][2]["value"],
                "payroll_cycles": payroll["metrics"][3]["value"],
            },
            "modules": {"payroll": payroll},
        }
    if role not in HR_ROLES:
        raise HTTPException(status_code=403, detail="HR analytics access is required.")

    today = date.today()
    departments = {item.id: item.name for item in db.query(Department).all()}
    employees = db.query(Employee).all()
    active_employees = [item for item in employees if item.status == "ACTIVE"]
    attendance = db.query(Attendance).all()
    leaves = db.query(LeaveRequest).all()
    reviews = db.query(PerformanceReview).all()
    requisitions = db.query(JobRequisition).all()
    candidates = db.query(Candidate).all()
    contracts = db.query(Contract).all()
    documents = db.query(EmployeeDocument).all()
    disciplinary = db.query(DisciplinaryCase).all()
    exits = db.query(EmployeeExit).all()
    courses = db.query(TrainingCourse).all()
    sessions = db.query(TrainingSession).all()
    enrollments = db.query(TrainingEnrollment).all()
    payroll = _payroll_report(db)

    department_distribution = _distribution(
        active_employees,
        lambda item: departments.get(item.department_id) or item.legacy_department or "Unassigned",
    )
    attendance_statuses = _distribution(attendance, lambda item: item.status)
    leave_statuses = _distribution(leaves, lambda item: item.status)
    performance_periods = _monthly_counts(reviews, lambda item: item.review_period)
    candidate_statuses = _distribution(candidates, lambda item: item.status)
    requisition_statuses = _distribution(requisitions, lambda item: item.status)
    document_statuses = _distribution(documents, lambda item: item.status)
    contract_statuses = _distribution(contracts, lambda item: item.status)
    disciplinary_statuses = _distribution(disciplinary, lambda item: item.status)
    exit_statuses = _distribution(exits, lambda item: item.clearance_status)
    enrollment_statuses = _distribution(enrollments, lambda item: item.status)

    review_ratings = [item.hod_rating for item in reviews if item.hod_rating is not None]
    pending_onboarding = [
        item for item in employees if item.status == "ONBOARDING"
    ]
    missing_documents = [
        item for item in documents if item.status.upper() in {"MISSING", "REJECTED"}
    ]
    active_contracts = [
        item for item in contracts if item.status in {"SIGNED", "ACTIVE"}
    ]
    expiring_contracts = [
        item for item in active_contracts
        if item.end_date and 0 <= (item.end_date - today).days <= 30
    ]
    pending_clearance = [
        item for item in exits if item.clearance_status != "CLEARED"
    ]
    open_requisitions = [
        item for item in requisitions if item.status in {"PENDING_HR", "APPROVED"}
    ]
    pending_leave = [item for item in leaves if item.status == "PENDING_HOD"]
    pending_reviews = [
        item for item in reviews if item.self_rating is not None and item.hod_rating is None
    ]
    today_attendance = [item for item in attendance if item.date == today]
    upcoming_sessions = [
        item for item in sessions if item.scheduled_date and item.scheduled_date >= today
    ]
    payroll_cycles = db.query(PayrollCycle).all()
    attendance_periods = _monthly_counts(attendance, lambda item: item.date)
    leave_periods = _monthly_counts(leaves, lambda item: item.start_date)
    recruitment_flow = [
        {"label": row["label"], "value": row["value"]} for row in candidate_statuses
    ]
    lifecycle_flow = [
        {"label": "Applicants in pipeline", "value": sum(
            item.status in {"IN_PIPELINE", "INTERVIEW_SCHEDULED", "PASSED", "OFFERED"}
            for item in candidates
        )},
        {"label": "Hired candidates", "value": sum(item.status == "HIRED" for item in candidates)},
        {"label": "Onboarding", "value": len(pending_onboarding)},
        {"label": "Active employees", "value": len(active_employees)},
        {"label": "Payroll records", "value": sum(row["employees"] for row in payroll["trend"])},
        {"label": "Exit clearances", "value": len(pending_clearance)},
    ]

    modules = {
        "employees": _module(
            "Employee directory",
            "Current active headcount and its distribution across recorded departments.",
            [_metric("Active employees", len(active_employees)), _metric("All employee records", len(employees))],
            department_distribution,
            "Active employees by department",
        ),
        "attendance": _module(
            "Attendance",
            "Recorded attendance statuses and monthly activity.",
            [
                _metric("Attendance records", len(attendance)),
                _metric("Present today", sum(item.status == "PRESENT" for item in today_attendance)),
                _metric("Overtime hours", sum((_number(item.overtime_hours) for item in attendance)), "hours"),
            ],
            attendance_statuses,
            "Records by attendance status",
            attendance_periods,
        ),
        "leave": _module(
            "Leave management",
            "Leave requests grouped by approval status.",
            [_metric("Total requests", len(leaves)), _metric("Awaiting HOD", len(pending_leave))],
            leave_statuses,
            "Requests by status",
            leave_periods,
        ),
        "performance": _module(
            "Performance",
            "Monthly reviews, outstanding HOD ratings, and completed rating averages.",
            [
                _metric("Reviews", len(reviews)),
                _metric("Awaiting HOD rating", len(pending_reviews)),
                _metric("Average HOD rating", sum(review_ratings) / len(review_ratings) if review_ratings else 0, "rating"),
            ],
            performance_periods,
            "Reviews by period",
        ),
        "recruitment": _module(
            "Recruitment",
            "Requisition decisions and candidate pipeline stages.",
            [
                _metric("Open requisitions", len(open_requisitions)),
                _metric("Candidates", len(candidates)),
                _metric("Candidates in pipeline", sum(
                    item.status in {"IN_PIPELINE", "INTERVIEW_SCHEDULED", "PASSED", "OFFERED"}
                    for item in candidates
                )),
            ],
            candidate_statuses,
            "Candidates by pipeline stage",
        ),
        "onboarding": _module(
            "Onboarding",
            "New employee setup and employee document review status.",
            [
                _metric("Employees onboarding", len(pending_onboarding)),
                _metric("Missing or rejected documents", len(missing_documents)),
                _metric("Documents awaiting review", sum(item.status.upper() == "SUBMITTED" for item in documents)),
            ],
            document_statuses,
            "Documents by review status",
        ),
        "contracts": _module(
            "Contracts",
            "Contract status, including active contracts reaching their configured expiry window.",
            [
                _metric("Active or signed", len(active_contracts)),
                _metric("Expiring within 30 days", len(expiring_contracts)),
                _metric("Expired", sum(item.status == "EXPIRED" for item in contracts)),
            ],
            contract_statuses,
            "Contracts by status",
        ),
        "payroll": payroll,
        "disciplinary": _module(
            "Disciplinary",
            "Open and resolved case counts.",
            [
                _metric("Open cases", sum(item.status == "OPEN" for item in disciplinary)),
                _metric("Resolved cases", sum(item.status == "RESOLVED" for item in disciplinary)),
                _metric("Total cases", len(disciplinary)),
            ],
            disciplinary_statuses,
            "Cases by status",
        ),
        "exit": _module(
            "Exit and clearance",
            "Clearance progress for employee exit records.",
            [
                _metric("Exit records", len(exits)),
                _metric("Clearance pending", len(pending_clearance)),
                _metric("Cleared", sum(item.clearance_status == "CLEARED" for item in exits)),
            ],
            exit_statuses,
            "Exit records by clearance status",
        ),
        "training": _module(
            "Training",
            "Active courses, scheduled sessions, and assigned employee training.",
            [
                _metric("Active courses", sum(item.is_active for item in courses)),
                _metric("Upcoming sessions", len(upcoming_sessions)),
                _metric("Completed enrollments", sum(item.status == "COMPLETED" for item in enrollments)),
                _metric("Total enrollments", len(enrollments)),
            ],
            enrollment_statuses,
            "Enrollments by status",
        ),
    }
    pending_payroll_cycles = sum(item.stage != "POSTED" for item in payroll_cycles)
    summary = {
        "active_employees": len(active_employees),
        "gross_payroll_recorded": payroll["metrics"][0]["value"],
        "open_requisitions": len(open_requisitions),
        "candidates_in_pipeline": modules["recruitment"]["metrics"][2]["value"],
        "employees_onboarding": len(pending_onboarding),
        "pending_leave": len(pending_leave),
        "pending_performance_reviews": len(pending_reviews),
        "contracts_expiring_30d": len(expiring_contracts),
        "open_disciplinary_cases": modules["disciplinary"]["metrics"][0]["value"],
        "pending_exit_clearances": len(pending_clearance),
        "pending_payroll_cycles": pending_payroll_cycles,
        "upcoming_training_sessions": len(upcoming_sessions),
    }
    return {
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "scope": "organization",
        "summary": summary,
        "workflow": lifecycle_flow,
        "modules": modules,
    }
