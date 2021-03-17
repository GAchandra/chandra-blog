from functools import wraps
from flask import Flask, render_template, redirect, url_for, flash, abort
from flask_bootstrap import Bootstrap
from flask_ckeditor import CKEditor
from datetime import date
from werkzeug.security import generate_password_hash, check_password_hash
from flask_sqlalchemy import SQLAlchemy
from flask_login import login_required, login_user, logout_user, current_user, LoginManager, UserMixin
from forms import *
from flask_gravatar import Gravatar
import os
from datetime import datetime
from tables import create_tables
from authentication import email_confirmation, check_email_confirmation

app = Flask(__name__)
app.config['SECRET_KEY'] = os.environ.get('SECRET_KEY')
ckeditor = CKEditor(app)
Bootstrap(app)
login_manager = LoginManager()
login_manager.init_app(app=app)

gravatar = Gravatar(app,
                    size=100,
                    rating='g',
                    default='retro',
                    force_default=False,
                    force_lower=False,
                    use_ssl=False,
                    base_url=None)
# CONNECT TO DB
app.config['SQLALCHEMY_DATABASE_URI'] = os.environ.get('DATABASE_URL')
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
db = SQLAlchemy(app)

User, BlogPost, Comment = create_tables(db, UserMixin=UserMixin)
db.create_all()


@login_manager.user_loader
def load_user(user_id):
    return User.query.filter_by(id=user_id).first()


def admin_only(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if current_user.id != 1:
            return abort(403, "Access denied")
        else:
            return f(*args, **kwargs)

    return decorated_function


@app.context_processor
def inject_now():
    return {'now': datetime.now().utcnow()}


@app.route('/')
def get_all_posts():
    posts = BlogPost.query.all()
    return render_template("index.html", all_posts=posts)


@app.route('/register', methods=['GET', 'POST'])
def register():
    register_form = RegisterForm()
    if register_form.validate_on_submit():
        if User.query.filter_by(email=register_form.email.data).first():
            flash("You've already signed up that email, log in instead!", "error")
            return redirect(url_for('login'))
        else:
            user = User()
            while True:
                user.id = os.urandom(20).hex()
                user.name = register_form.name.data
                user.email = register_form.email.data
                user.password = generate_password_hash(register_form.password.data,
                                                       salt_length=int(os.environ.get('SALT_LENGTH')))

                db.session.add(user)
                try:
                    db.session.commit()
                except:
                    pass
                else:
                    break
            email_confirmation(user.email, user.name)
            flash(
                "We are send confirmation email to your email address, please follow the instruction to activate your "
                "account.",
                "Warning")
            return redirect(url_for('get_all_posts'))

    return render_template("register.html", form=register_form)


@app.route('/account-confirmation/email/<jwt_token>')
def confirm_account_as_email(jwt_token):
    email = check_email_confirmation(jwt_token)
    if email:
        # Update the user
        update_user = User.query.filter_by(email=email).first()
        update_user.is_email_active = True
        update_user.is_account_active = True
        update_user.confirmed_time = datetime.now()
        db.session.commit()
        login_user(update_user, True)
        flash("You are successfully authenticated now. thank you for visiting my blog.", "success")
        return redirect(url_for("get_all_posts"))
    else:

        return redirect(url_for('resend_verification'))


@app.route('/account-confirmation/email/resend/', methods=['GET', 'POST'])
def resend_verification():
    resend_email_form = ResendEmailFrom()
    if resend_email_form.validate_on_submit():
        user = User.query.filter_by(email=resend_email_form.email.data).first()
        email_confirmation(user.email, user.name)
        flash(
            "We are send confirmation email to your email address, please follow the instruction to activate your "
            "account.",
            "Warning")
        return redirect(url_for('get_all_posts'))
    else:
        return render_template('email_confirmation.html', form=resend_email_form)


@app.route('/login', methods=['GET', 'POST'])
def login():
    login_form = LoginForm()
    if login_form.validate_on_submit():
        user = User.query.filter_by(email=login_form.email.data).first()
        if user is not None:
            if user.is_account_active:
                print(user.is_account_active)
                if check_password_hash(user.password, login_form.password.data):
                    login_user(user, True)
                    return redirect(url_for('get_all_posts'))
                else:
                    flash("Password incorrect. please try again", "error")
                    return redirect(url_for('login'))
            else:
                flash("Your account is not activating. please try again or contact me.", "error")
                return redirect(url_for('login'))
        else:
            flash("Email is does not exist, please try again.", "error")
            return redirect(url_for("login"))
    return render_template("login.html", form=login_form)


@app.route('/logout')
@login_required
def logout():
    logout_user()
    return redirect(url_for('get_all_posts'))


@app.route("/post/<int:post_id>", methods=['GET', 'POST'])
def show_post(post_id):
    comment_form = CommentForm()
    if comment_form.validate_on_submit():
        if current_user.is_authenticated:
            parent_post = BlogPost.query.get(post_id)

            while True:
                comment = Comment(id=os.urandom(20).hex(), comment_author=current_user, parent_post=parent_post,
                                  text=comment_form.text.data)
                db.session.add(comment)
                try:
                    db.session.commit()
                except:
                    pass
                else:
                    break

            return redirect(url_for('show_post', post_id=post_id))
        else:
            flash("You need to login or register to comment")
            return redirect(url_for('login'))
    else:
        requested_post = BlogPost.query.get(post_id)
        return render_template("post.html", post=requested_post, form=comment_form, gravatar=gravatar)


@app.route("/about")
def about():
    return render_template("about.html")


@app.route("/contact")
def contact():
    return render_template("contact.html")


@app.route("/new-post", methods=['GET', 'POST'])
@login_required
@admin_only
def add_new_post():
    form = CreatePostForm()
    if form.validate_on_submit():
        while True:
            new_post = BlogPost(
                id=os.urandom(20).hex(),
                title=form.title.data,
                subtitle=form.subtitle.data,
                body=form.body.data,
                img_url=form.img_url.data,
                author=current_user,
                date=date.today().strftime("%B %d, %Y")
            )
            db.session.add(new_post)
            try:
                db.session.commit()
            except:
                pass
            else:
                break
        return redirect(url_for("get_all_posts"))
    return render_template("make-post.html", form=form)


@app.route("/edit-post/<post_id>", methods=['GET', 'POST'])
@login_required
@admin_only
def edit_post(post_id):
    post = BlogPost.query.get(post_id)
    edit_form = CreatePostForm(
        title=post.title,
        subtitle=post.subtitle,
        img_url=post.img_url,
        body=post.body
    )
    if edit_form.validate_on_submit():
        post.title = edit_form.title.data
        post.subtitle = edit_form.subtitle.data
        post.img_url = edit_form.img_url.data
        post.body = edit_form.body.data
        db.session.commit()
        return redirect(url_for("show_post", post_id=post.id))

    return render_template("make-post.html", form=edit_form)


@app.route("/delete/<post_id>")
@login_required
@admin_only
def delete_post(post_id):
    post_to_delete = BlogPost.query.get(post_id)
    db.session.delete(post_to_delete)
    db.session.commit()
    return redirect(url_for('get_all_posts'))


@app.route('/delete/comment/<post_id>/<comment_id>/<user_id>')
@login_required
def delete_comment(post_id, comment_id, user_id):
    comments = Comment.query.filter_by(author_id=user_id).all()
    for comment in comments:
        if comment.post_id == post_id and comment.id == comment_id:
            db.session.delete(comment)
            db.session.commit()
            return redirect(url_for('show_post', post_id=post_id))

    flash("Comment deleting is failed. please try again.")
    return redirect(url_for('show_post', post_id=post_id))


if __name__ == "__main__":
    app.run()
