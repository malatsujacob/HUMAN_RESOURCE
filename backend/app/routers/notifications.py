from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from uuid import UUID

from app.models.notification import Notification
from app.models.user import User
from app.routers.attendance import get_current_user, get_db

router = APIRouter()
HR_ROLES = {"HR", "HR_ADMIN", "ADMIN", "MANAGEMENT", "DEVELOPER"}


def require_hr(user: User = Depends(get_current_user)) -> User:
    if (user.role or "").upper() not in HR_ROLES:
        raise HTTPException(status_code=403, detail="HR access is required.")
    return user


@router.get("/hr")
def list_hr_notifications(db: Session = Depends(get_db), user: User = Depends(require_hr)):
    rows = db.query(Notification).filter(Notification.recipient_user_id == user.id).order_by(Notification.created_at.desc()).limit(100).all()
    return [{"id": str(row.id), "type": row.type, "title": row.title, "message": row.message,
             "is_read": row.is_read, "created_at": row.created_at, "details": row.details} for row in rows]


@router.post("/hr/{notification_id}/read")
def mark_hr_notification_read(notification_id: UUID, db: Session = Depends(get_db), user: User = Depends(require_hr)):
    row = db.query(Notification).filter(Notification.id == notification_id, Notification.recipient_user_id == user.id).first()
    if row is None:
        raise HTTPException(status_code=404, detail="Notification not found.")
    row.is_read = True
    db.commit()
    return {"message": "Notification marked as read."}
