import enum

from sqlalchemy import Column, Integer, Float, String, Date, DateTime, Boolean, Enum, ForeignKey, func
from sqlalchemy.orm import declarative_base, relationship


Base = declarative_base()


class Role(enum.Enum):
    admin: str = "admin"
    moderator: str = "moderator"
    user: str = "user"


class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True)
    username = Column(String(50), unique=True)
    email = Column(String(150), nullable=False, unique=True)
    password = Column(String(255), nullable=False, unique=True)
    refresh_token = Column(String(255), nullable=True)
    roles = Column("roles", Enum(Role), default=Role.user)
    confirmed = Column(Boolean, default=False)
    created_at = Column(DateTime, default=func.now())
    updated_at = Column(DateTime, default=func.now(), onupdate=func.now())


class Account(Base):
    __tablename__ = "accounts"

    id = Column(Integer, primary_key=True)
    username = Column(String, ForeignKey("users.username"))
    first_name = Column(String(30), nullable=False)
    last_name = Column(String(60), nullable=False)
    location = Column(String(40), nullable=True)
    company = Column(String(50), nullable=True)
    position = Column(String(30), nullable=True)
    avatar = Column(String(255), nullable=True)
    email = Column(String(150), unique=True, nullable=False)
    phone_number = Column(String, unique=True, nullable=True)
    birth_date = Column(Date, nullable=True)
    images_quantity = Column(Integer, nullable=True)
    created_at = Column(DateTime, default=func.now())
    updated_at = Column(DateTime, default=func.now(), onupdate=func.now())


class Image(Base):
    __tablename__ = "images"

    id = Column(Integer, primary_key=True)
    user_id = Column(Integer, ForeignKey("users.id"))
    description = Column(String(50), nullable=False)
    origin_path = Column(String(255), nullable=False)
    public_id = Column(String, nullable=False)
    transformed_path = Column(String(255), nullable=True)
    qr_path = Column(String(255), nullable=True)
    rating = Column(Float(2), default=0)
    comments = relationship("Comment", secondary="comment_images", backref="images")
    tags = relationship("Tag", secondary="tag_images", backref="images")
    created_at = Column(DateTime, default=func.now())
    updated_at = Column(DateTime, default=func.now(), onupdate=func.now())


class Comment(Base):
    __tablename__ = "comments"

    id = Column(Integer, primary_key=True)
    comment = Column(String(100), nullable=False)
    created_at = Column(DateTime, default=func.now())
    updated_at = Column(DateTime, default=func.now(), onupdate=func.now())


class Tag(Base):
    __tablename__ = "tags"

    id = Column(Integer, primary_key=True)
    tag = Column(String(50), nullable=False, unique=True)
    created_at = Column(DateTime, default=func.now())


class CommentToImage(Base):
    __tablename__ = "comment_images"

    id = Column(Integer, primary_key=True)
    user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    image_id = Column(Integer, ForeignKey("images.id", ondelete="CASCADE"), nullable=False)
    comment_id = Column(Integer, ForeignKey("comments.id", ondelete="CASCADE"), nullable=False)


class TagToImage(Base):
    __tablename__ = "tag_images"

    id = Column(Integer, primary_key=True)
    tag_id = Column(Integer, ForeignKey("tags.id", ondelete="CASCADE"), nullable=False)
    image_id = Column(Integer, ForeignKey("images.id", ondelete="CASCADE"), nullable=False)


class Rating(Base):
    __tablename__ = "ratings"

    id = Column(Integer, primary_key=True)
    image_id = Column(Integer, ForeignKey("images.id"))
    rate = Column(Integer)
    user_id = Column(Integer, ForeignKey("users.id"))


class BanList(Base):
    __tablename__ = "ban_lists"

    id = Column(Integer, primary_key=True)
    access_token = Column(String(255), nullable=False)
    reason = Column(String(50), default="logout")
