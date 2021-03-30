from sqlalchemy.orm import relationship
from datetime import datetime


def create_tables(db, UserMixin):
    class User(UserMixin, db.Model):
        __tablename__ = 'users'
        id = db.Column(db.String, primary_key=True, nullable=False, unique=True)
        name = db.Column(db.String(50), nullable=False)
        email = db.Column(db.String(250), unique=True, nullable=False)
        password = db.Column(db.TEXT, nullable=False)
        account_created_time = db.Column(db.DateTime, default=datetime.now())
        is_email_confirmed = db.Column(db.Boolean, default=False)
        is_account_active = db.Column(db.Boolean, default=False)
        email_confirmed_time = db.Column(db.DateTime)
        is_changing_email = db.Column(db.Boolean, default=False)
        is_changing_password = db.Column(db.Boolean, default=False)
        last_password_changed_time = db.Column(db.DateTime)
        last_email_changed_time = db.Column(db.DateTime)
        is_admin = db.Column(db.Boolean, default=False)
        posts = relationship("BlogPost", back_populates='author')
        comments = relationship("Comment", back_populates='comment_author')

    class NotConfirmedAccount(db.Model):
        __tablename__ = "not_confirmed_accounts"
        id = db.Column(db.String, primary_key=True, nullable=False, unique=True)
        name = db.Column(db.String(50), nullable=False)
        email = db.Column(db.String(250), nullable=False)
        password = db.Column(db.TEXT, nullable=False)
        create_time = db.Column(db.DateTime, default=datetime.now())
        is_re_email_sent = db.Column(db.Boolean, default=False)
        last_email_sent_time = db.Column(db.DateTime)

    class BlogPost(db.Model):
        __tablename__ = "blog_posts"
        id = db.Column(db.String, primary_key=True)
        author_id = db.Column(db.String, db.ForeignKey('users.id'))
        author = relationship("User", back_populates='posts')
        title = db.Column(db.String(250), unique=True, nullable=False)
        subtitle = db.Column(db.String(250), nullable=False)
        date = db.Column(db.String(250), nullable=False)
        body = db.Column(db.Text, nullable=False)
        img_url = db.Column(db.String(250), nullable=False)
        comments = relationship("Comment", back_populates='parent_post')

    class Comment(db.Model):
        __tablename__ = 'comments'
        id = db.Column(db.String, primary_key=True)
        author_id = db.Column(db.String, db.ForeignKey('users.id'))
        comment_author = relationship("User", back_populates='comments')
        post_id = db.Column(db.String, db.ForeignKey('blog_posts.id'))
        parent_post = relationship("BlogPost", back_populates='comments')
        text = db.Column(db.TEXT, nullable=False)

    return User, NotConfirmedAccount, BlogPost, Comment
