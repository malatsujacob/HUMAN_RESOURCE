from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from pydantic import BaseModel, EmailStr, Field
from app.database import SessionLocal, verify_password, get_password_hash, create_access_token
from app.models.user import User
from app.models.notification import Notification
from app.routers.attendance import get_current_user

router = APIRouter()

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

class LoginRequest(BaseModel):
    email: EmailStr
    password: str


class ChangePasswordRequest(BaseModel):
    current_password: str
    new_password: str = Field(min_length=10, max_length=128)
    confirm_password: str

@router.post("/login")
def login(request: LoginRequest, db: Session = Depends(get_db)):
    user = db.query(User).filter(User.email == request.email).first()
    
    if not user or not verify_password(request.password, user.password_hash):
        raise HTTPException(status_code=401, detail="Invalid email or password")
    
    token = create_access_token({"sub": user.email, "role": user.role, "emp_id": str(user.employee_id)})
    return {"access_token": token, "token_type": "bearer", "role": user.role, "email": user.email,
            "must_change_password": bool(user.must_change_password)}


@router.post("/change-password")
def change_password(
    request: ChangePasswordRequest,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    account = db.query(User).filter(User.id == user.id).with_for_update().first()
    if account is None:
        raise HTTPException(status_code=401, detail="Account not found.")
    if not verify_password(request.current_password, account.password_hash):
        raise HTTPException(status_code=400, detail="Current password is incorrect.")
    if request.new_password != request.confirm_password:
        raise HTTPException(status_code=422, detail="New password and confirmation do not match.")
    if verify_password(request.new_password, account.password_hash):
        raise HTTPException(status_code=422, detail="Choose a password different from your current password.")

    completing_first_login = bool(account.must_change_password)
    account.password_hash = get_password_hash(request.new_password)
    account.must_change_password = False
    if completing_first_login:
        recipients = db.query(User).filter(
            User.role.in_(["HR", "HR_ADMIN", "ADMIN", "MANAGEMENT", "DEVELOPER"]),
            User.is_active.is_(True), User.id != account.id,
        ).all()
        employee_name = "An employee"
        if account.employee:
            employee_name = " ".join(part for part in [account.employee.first_name, account.employee.middle_name, account.employee.last_name] if part)
        for recipient in recipients:
            db.add(Notification(
                recipient_user_id=recipient.id,
                sender_user_id=account.id,
                type="EMPLOYEE_PASSWORD_CHANGED",
                title="Employee completed first login",
                message=f"{employee_name} changed their temporary password and activated their account.",
                is_read=False,
            ))
    db.commit()
    return {"message": "Password changed successfully.", "must_change_password": False}
