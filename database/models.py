from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship
from sqlalchemy import Column, Integer, String, ForeignKey, Table, DateTime

Base = declarative_base()

tag_post = Table(
    "tag_post",
    Base.metadata,
    Column("post_id", Integer, ForeignKey("post.id")),
    Column("tag_id", Integer, ForeignKey("tag.id")),
)


class Post(Base):
    __tablename__ = "post"
    id = Column(Integer, primary_key=True, autoincrement=False)
    url = Column(String, nullable=False, unique=True)
    title = Column(String, nullable=False, unique=False)
    image = Column(String, nullable=False, unique=False)
    date_post = Column(DateTime, nullable=False, unique=False)
    writer_id = Column(Integer, ForeignKey("writer.id"))
    writer = relationship("Writer")
    comments = relationship("Comment")
    tags = relationship("Tag", secondary=tag_post)


class Writer(Base):
    __tablename__ = "writer"
    id = Column(Integer, primary_key=True, autoincrement=True)
    url = Column(String, nullable=False, unique=True)
    name = Column(String, nullable=False, unique=False)
    posts = relationship(Post)


class Comment(Base):
    __tablename__ = "comment"
    id = Column(Integer, primary_key=True)
    content = Column(String, nullable=False, unique=False)
    reply_to_comment_id = Column(Integer, ForeignKey("comment.id"), nullable=True)
    commentator_id = Column(Integer, ForeignKey("writer.id"))
    commentator = relationship("Writer")
    post_id = Column(Integer, ForeignKey("post.id"))
    post = relationship(Post)

    def __init__(self, **kwargs):
        self.id = kwargs["id"]
        self.content = kwargs["body"]
        self.reply_to_comment_id = kwargs["parent_id"]
        self.commentator = kwargs["writer"]


class Tag(Base):
    __tablename__ = "tag"
    id = Column(Integer, primary_key=True, autoincrement=True)
    url = Column(String, nullable=False, unique=True)
    name = Column(String, nullable=False, unique=False)
    posts = relationship(Post, secondary=tag_post)
