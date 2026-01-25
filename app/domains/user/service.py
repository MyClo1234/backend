from sqlalchemy.orm import Session
from uuid import UUID
from .model import User
from .schema import UserUpdate


def update_user_profile(db: Session, user_id: UUID, update_data: UserUpdate):
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        return None

    # Update fields if provided
    if update_data.height is not None:
        user.height = update_data.height
    if update_data.weight is not None:
        user.weight = update_data.weight
    if update_data.gender is not None:
        user.gender = update_data.gender
    if update_data.body_shape is not None:
        user.body_shape = update_data.body_shape

    db.commit()
    db.refresh(user)
    return user
