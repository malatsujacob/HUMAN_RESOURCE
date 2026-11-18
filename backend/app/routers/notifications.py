from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel, Field
from sqlalchemy import or_
from sqlalchemy.orm import Session
from uuid import UUID

from app.models.employee import Employee
from app.models.notification import Notification
from app.models.user import User
from app.routers.attendance import get_current_user, get_db

router = APIRouter()
HR_ROLES = {"HR", "HR_ADMIN", "ADMIN", "MANAGEMENT", "DEVELOPER"}


def require_hr(user: User = Depends(get_current_user)) -> User:
    if (user.role or "").upper() not in HR_ROLES:
        raise HTTPException(status_code=403, detail="HR access is required.")
    return user


class NotificationReply(BaseModel):
    message: str = Field(min_length=1, max_length=2000)


def find_employee_user(db: Session, employee_id: str | None, employee_number: str | None = None):
    query = db.query(User)
    if employee_id:
        try:
            return query.filter(User.employee_id == UUID(employee_id)).first()
        except ValueError:
            return None
    if employee_number:
        return query.join(Employee, User.employee_id == Employee.id).filter(
            Employee.employee_number == employee_number
        ).first()
    return None


def notification_sender(db: Session, item: Notification):
    if item.sender_user_id:
        return db.query(User).filter(User.id == item.sender_user_id).first()
    if item.type == "CONTRACT_EXPIRY_REMINDER":
        return None
    details = item.details if isinstance(item.details, dict) else {}
    return find_employee_user(
        db,
        details.get("employee_id"),
        details.get("employee_number"),
    )


def notification_recipient(db: Session, item: Notification):
    if item.recipient_user_id:
        return db.query(User).filter(User.id == item.recipient_user_id).first()
    if item.recipient_employee_id:
        return db.query(User).filter(User.employee_id == item.recipient_employee_id).first()
    return None


def thread_root(db: Session, notification_id: UUID):
    item = db.query(Notification).filter(Notification.id == notification_id).first()
    if item is None:
        raise HTTPException(status_code=404, detail="Notification not found.")
    if item.in_reply_to_id:
        root = db.query(Notification).filter(Notification.id == item.in_reply_to_id).first()
        if root is None:
            raise HTTPException(status_code=404, detail="Notification thread not found.")
        return root
    return item


def user_name(user: User | None) -> str:
    if user is None:
        return "Former user"
    if user.employee:
        employee = user.employee
        name = " ".join(
            part for part in (employee.first_name, employee.middle_name, employee.last_name) if part
        )
        if name:
            return name
    return user.email


def notification_sender_name(db: Session, item: Notification) -> str:
    sender = notification_sender(db, item)
    return user_name(sender) if sender else "HR system"


def notification_payload(db: Session, item: Notification, user: User) -> dict:
    sender = notification_sender(db, item)
    root = item
    if item.in_reply_to_id:
        root = db.query(Notification).filter(Notification.id == item.in_reply_to_id).first()
        if root is None:
            raise HTTPException(status_code=404, detail="Notification thread not found.")
    root_sender = notification_sender(db, root)
    root_recipient = notification_recipient(db, root)
    participants = {participant.id for participant in (root_sender, root_recipient) if participant}
    details = item.details if isinstance(item.details, dict) else {}
    return {
        "id": str(item.id),
        "thread_id": str(root.id),
        "type": item.type,
        "title": item.title,
        "message": details.get("reply_text") or item.message,
        "sender_name": user_name(sender) if sender else "HR system",
        "is_read": bool(item.is_read),
        "created_at": item.created_at,
        "details": details,
        "can_reply": user.id in participants and len(participants) == 2,
    }


def require_thread_participant(db: Session, root: Notification, user: User):
    sender = notification_sender(db, root)
    recipient = notification_recipient(db, root)
    participant_ids = {participant.id for participant in (sender, recipient) if participant}
    if user.id not in participant_ids:
        raise HTTPException(status_code=403, detail="You cannot access this notification thread.")
    if len(participant_ids) != 2:
        raise HTTPException(status_code=409, detail="This notification does not have a reply destination.")
    return sender, recipient


@router.get("/mine")
def list_my_notifications(
    offset: int = Query(default=0, ge=0),
    limit: int = Query(default=50, ge=1, le=100),
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
):
    recipient_filter = [Notification.recipient_user_id == user.id]
    if user.employee_id:
        recipient_filter.append(Notification.recipient_employee_id == user.employee_id)
    query = db.query(Notification).filter(or_(*recipient_filter))
    total = query.count()
    unread_count = query.filter(Notification.is_read.is_(False)).count()
    rows = query.order_by(Notification.created_at.desc()).offset(offset).limit(limit).all()
    return {
        "items": [notification_payload(db, item, user) for item in rows],
        "total": total,
        "unread_count": unread_count,
    }


@router.post("/{notification_id}/read")
def mark_notification_read(
    notification_id: UUID,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
):
    recipient_filter = [Notification.recipient_user_id == user.id]
    if user.employee_id:
        recipient_filter.append(Notification.recipient_employee_id == user.employee_id)
    item = db.query(Notification).filter(
        Notification.id == notification_id,
        or_(*recipient_filter),
    ).first()
    if item is None:
        raise HTTPException(status_code=404, detail="Notification not found.")
    item.is_read = True
    db.commit()
    return {"message": "Notification marked as read."}


@router.get("/{notification_id}/thread")
def get_notification_thread(
    notification_id: UUID,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
):
    root = thread_root(db, notification_id)
    require_thread_participant(db, root, user)
    replies = db.query(Notification).filter(
        Notification.in_reply_to_id == root.id
    ).order_by(Notification.created_at.asc()).all()
    return [
        {
            "id": str(item.id),
            "sender_name": notification_sender_name(db, item),
            "message": (
                (item.details or {}).get("reply_text", item.message)
                if isinstance(item.details, dict) else item.message
            ),
            "created_at": item.created_at,
        }
        for item in [root, *replies]
    ]


@router.post("/{notification_id}/reply")
def reply_to_notification(
    notification_id: UUID,
    request: NotificationReply,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
):
    message = request.message.strip()
    if not message:
        raise HTTPException(status_code=422, detail="Reply cannot be blank.")
    root = thread_root(db, notification_id)
    sender, recipient = require_thread_participant(db, root, user)
    target = sender if user.id == recipient.id else recipient
    if target.id == user.id:
        raise HTTPException(status_code=409, detail="A reply cannot be sent to yourself.")

    reply = Notification(
        recipient_user_id=target.id,
        sender_user_id=user.id,
        in_reply_to_id=root.id,
        type="NOTIFICATION_REPLY",
        title=f"Reply: {root.title or 'Notification'}"[:100],
        message=message[:255],
        details={"reply_text": message, "thread_id": str(root.id), "original_title": root.title},
        is_read=False,
    )
    db.add(reply)
    if root.sender_user_id is None and sender.id != user.id:
        root.sender_user_id = sender.id
    db.commit()
    db.refresh(reply)
    return notification_payload(db, reply, user)


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
