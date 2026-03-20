"""
Module: api/services/notification.py
Description: Notification service for citizen status updates.
             Creates and manages notifications when application
             status changes throughout the review workflow.
"""

from datetime import datetime
from sqlalchemy.orm import Session

from api.models.entities import Notification
from api.config import AppStatus, SCHEME_LABELS


# ─── Notification Messages ────────────────────────────────────
# Templates for each status transition.
# {scheme} and {remarks} are replaced at runtime.

MESSAGES = {
    AppStatus.PENDING: (
        "Your application has been submitted successfully. "
        "It is currently being processed by our system."
    ),
    AppStatus.AUTO_APPROVED: (
        "Our system has reviewed your application and recommended "
        "you for {scheme}. An officer will complete the final review shortly."
    ),
    AppStatus.NEEDS_REVIEW: (
        "Your application has been forwarded to an officer for "
        "detailed review. You will be notified once a decision is made."
    ),
    AppStatus.APPROVED: (
        "Congratulations! Your application has been approved for {scheme}. "
        "Please visit your nearest NSAP office with your documents to "
        "complete the enrollment process."
    ),
    AppStatus.REJECTED: (
        "We regret to inform you that your application has been rejected. "
        "Reason: {remarks}. You may re-apply after addressing the concerns "
        "or visit your nearest NSAP office for assistance."
    ),
}


# ─── Create Notification ──────────────────────────────────────
def create_notification(
    db:             Session,
    user_id:        str,
    application_id: str,
    status:         str,
    scheme:         str  = None,
    remarks:        str  = None,
) -> Notification:
    """
    Create a notification for a citizen when application status changes.

    Args:
        db             (Session): Database session.
        user_id        (str):     Citizen user ID.
        application_id (str):     Application UUID.
        status         (str):     New application status from AppStatus.
        scheme         (str):     Predicted/approved scheme code (optional).
        remarks        (str):     Officer remarks for rejection (optional).

    Returns:
        Notification: Created notification ORM object.
    """
    # Get message template for this status
    template = MESSAGES.get(status, "Your application status has been updated.")

    # Fill in scheme name if provided
    scheme_name = SCHEME_LABELS.get(scheme, scheme or "")
    message     = template.format(
        scheme  = scheme_name,
        remarks = remarks or "No reason provided",
    )

    notification = Notification(
        user_id        = user_id,
        application_id = application_id,
        message        = message,
        is_read        = False,
    )

    db.add(notification)
    db.commit()
    db.refresh(notification)

    return notification


# ─── Mark As Read ─────────────────────────────────────────────
def mark_as_read(
    db:              Session,
    notification_id: str,
    user_id:         str,
) -> bool:
    """
    Mark a single notification as read.
    Verifies notification belongs to the requesting user.

    Args:
        db              (Session): Database session.
        notification_id (str):     Notification UUID.
        user_id         (str):     Requesting user ID for ownership check.

    Returns:
        bool: True if marked successfully, False if not found.
    """
    notification = db.query(Notification).filter(
        Notification.id      == notification_id,
        Notification.user_id == user_id,
    ).first()

    if not notification:
        return False

    notification.is_read = True
    db.commit()
    return True


# ─── Mark All As Read ─────────────────────────────────────────
def mark_all_as_read(db: Session, user_id: str) -> int:
    """
    Mark all unread notifications as read for a user.

    Args:
        db      (Session): Database session.
        user_id (str):     User ID.

    Returns:
        int: Number of notifications marked as read.
    """
    updated = db.query(Notification).filter(
        Notification.user_id == user_id,
        Notification.is_read == False,
    ).all()

    count = len(updated)
    for n in updated:
        n.is_read = True

    db.commit()
    return count


# ─── Get Notifications ────────────────────────────────────────
def get_user_notifications(
    db:          Session,
    user_id:     str,
    unread_only: bool = False,
    limit:       int  = 20,
) -> list:
    """
    Fetch notifications for a user ordered by newest first.

    Args:
        db          (Session): Database session.
        user_id     (str):     User ID.
        unread_only (bool):    If True, return only unread notifications.
        limit       (int):     Maximum notifications to return.

    Returns:
        list: List of Notification ORM objects.
    """
    query = db.query(Notification).filter(
        Notification.user_id == user_id
    )

    if unread_only:
        query = query.filter(Notification.is_read == False)

    return (
        query
        .order_by(Notification.created_at.desc())
        .limit(limit)
        .all()
    )


# ─── Unread Count ─────────────────────────────────────────────
def get_unread_count(db: Session, user_id: str) -> int:
    """
    Get count of unread notifications for a user.
    Used for notification badge in frontend.

    Args:
        db      (Session): Database session.
        user_id (str):     User ID.

    Returns:
        int: Number of unread notifications.
    """
    return db.query(Notification).filter(
        Notification.user_id == user_id,
        Notification.is_read == False,
    ).count()


# ─── Notify Status Change ─────────────────────────────────────
def notify_status_change(
    db:             Session,
    application,
    new_status:     str,
    remarks:        str = None,
) -> Notification:
    """
    Convenience function to notify citizen when application
    status changes. Extracts all required fields from application object.

    Args:
        db          (Session):     Database session.
        application (Application): Application ORM object.
        new_status  (str):         New status from AppStatus.
        remarks     (str):         Officer remarks (for rejection).

    Returns:
        Notification: Created notification object.
    """
    # Get scheme from prediction if available
    scheme = None
    if application.prediction:
        scheme = application.prediction.predicted_scheme

    return create_notification(
        db             = db,
        user_id        = application.citizen_id,
        application_id = application.id,
        status         = new_status,
        scheme         = scheme,
        remarks        = remarks,
    )