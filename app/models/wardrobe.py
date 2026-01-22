from sqlalchemy import Column, Integer, String, ForeignKey
from sqlalchemy.dialects.postgresql import ARRAY, JSONB
from sqlalchemy.orm import relationship
from app.database import Base


class ClosetItem(Base):
    __tablename__ = "closet_items"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    image_path = Column(String, nullable=False)
    category = Column(String, nullable=False)  # TOP, BOTTOM, etc.
    sub_category = Column(String, nullable=True)  # HOODIE, PARKA, etc.

    # Flexible features (includes color, material, thickness, etc.)
    features = Column(
        JSONB, nullable=True
    )  # {"color": "red", "material": "cotton", "thickness": 3}

    # PostgreSQL Array types
    season = Column(ARRAY(String), nullable=True)  # ['SPRING', 'FALL']
    mood_tags = Column(ARRAY(String), nullable=True)  # ['CASUAL', 'STREET']

    # Relationships
    owner = relationship("User", back_populates="closet_items")
    outfit_associations = relationship("OutfitItem", back_populates="item")
