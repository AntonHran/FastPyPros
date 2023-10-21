import enum

from sqlalchemy import Column, Integer, String, Date, DateTime, Boolean, Enum, ForeignKey, func
from sqlalchemy.ext.hybrid import hybrid_property
from sqlalchemy.orm import declarative_base, relationship

from src.database.connection import SessionLocal


Base = declarative_base()


class BaseModel(Base):
    __abstract__ = True

    id = Column(Integer, primary_key=True)
    created_at = Column(DateTime, default=func.now())
    updated_at = Column(DateTime, default=func.now(), onupdate=func.now())


class UserRole(enum.Enum):
    admin: str = "admin"
    moderator: str = "moderator"
    user: str = "user"


class User(BaseModel):
    __tablename__ = "users"

    # id = Column(Integer, primary_key=True)
    username = Column(String(50), unique=True)
    email = Column(String(150), nullable=False, unique=True)
    password = Column(String(255), nullable=False, unique=True)
    access_token = Column(String(255), nullable=True)
    refresh_token = Column(String(255), nullable=True)
    roles = Column("roles", Enum(UserRole), default=UserRole.user)
    confirmed = Column(Boolean, default=False)
    # created_at = Column(DateTime, default=func.now())
    # updated_at = Column(DateTime, default=func.now(), onupdate=func.now())
    images = relationship("Image", backref="users")
    rates_ = relationship("Rating", backref="users")
    comments_ = relationship("Comment", backref="users")


class Account(BaseModel):
    __tablename__ = "accounts"

    # id = Column(Integer, primary_key=True)
    username = Column(String, ForeignKey("users.username", ondelete="CASCADE"))
    first_name = Column(String(30), nullable=False)
    last_name = Column(String(60), nullable=False)
    location = Column(String(40), nullable=True)
    company = Column(String(50), nullable=True)
    position = Column(String(30), nullable=True)
    avatar = Column(String(255), nullable=True)
    email = Column(String(150), unique=True, nullable=False)
    phone_number = Column(String, unique=True, nullable=True)
    birth_date = Column(Date, nullable=True)
    # created_at = Column(DateTime, default=func.now())
    # updated_at = Column(DateTime, default=func.now(), onupdate=func.now())

    @hybrid_property
    def images_quantity(self):
        db = SessionLocal()
        user = db.query(User).filter(User.username == self.username).first()
        if user:
            quantity = db.query(func.count(Image.user_id)).filter(Image.user_id == user.id)
            return quantity.scalar()


class Image(BaseModel):
    __tablename__ = "images"

    # id = Column(Integer, primary_key=True)
    user_id = Column(Integer, ForeignKey("users.id"))
    description = Column(String(50), nullable=False)
    public_id = Column(String(255), nullable=False)
    origin_path = Column(String(255), nullable=False)
    transformed_path = Column(String(255), nullable=True)
    slug = Column(String(255), nullable=True)
    # created_at = Column(DateTime, default=func.now())
    # updated_at = Column(DateTime, default=func.now(), onupdate=func.now())
    comments = relationship("Comment", secondary="comment_images", backref="images")
    tags = relationship("Tag", secondary="tag_images", backref="images")
    rates = relationship("Rating", backref="images")

    @hybrid_property
    def rating(self):
        db = SessionLocal()
        query = func.sum(Rating.rate) / func.count(Rating.user_id)
        result = db.query(query).filter(Rating.image_id == self.id).first()
        if result[0]:
            return float(result[0])


class Comment(BaseModel):
    __tablename__ = "comments"

    # id = Column(Integer, primary_key=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    comment = Column(String(100), nullable=False)
    # created_at = Column(DateTime, default=func.now())
    # updated_at = Column(DateTime, default=func.now(), onupdate=func.now())


class Tag(BaseModel):
    __tablename__ = "tags"

    # id = Column(Integer, primary_key=True)
    tag = Column(String(50), nullable=False, unique=True)
    # created_at = Column(DateTime, default=func.now())


class CommentToImage(BaseModel):
    __tablename__ = "comment_images"

    # id = Column(Integer, primary_key=True)
    image_id = Column(Integer, ForeignKey("images.id", ondelete="CASCADE"), nullable=False)
    comment_id = Column(Integer, ForeignKey("comments.id", ondelete="CASCADE"), nullable=False)


class TagToImage(BaseModel):
    __tablename__ = "tag_images"

    # id = Column(Integer, primary_key=True)
    tag_id = Column(Integer, ForeignKey("tags.id", ondelete="CASCADE"), nullable=False)
    image_id = Column(Integer, ForeignKey("images.id", ondelete="CASCADE"), nullable=False)


class Rating(BaseModel):
    __tablename__ = "ratings"

    # id = Column(Integer, primary_key=True)
    image_id = Column(Integer, ForeignKey("images.id"))
    rate = Column(Integer)
    user_id = Column(Integer, ForeignKey("users.id"))
    # created_at = Column(DateTime, default=func.now())


class BanList(BaseModel):
    __tablename__ = "ban_lists"

    access_token = Column(String(255), nullable=False)
    reason = Column(String(50), default="logout")
