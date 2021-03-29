# Import all required models and Frameworks
from functools import wraps
from flask import Flask, render_template, redirect, url_for, flash, abort, request
from flask_bootstrap import Bootstrap
from flask_ckeditor import CKEditor
from datetime import date
from werkzeug.security import generate_password_hash, check_password_hash
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy.exc import IntegrityError
from flask_login import login_required, login_user, logout_user, current_user, LoginManager, UserMixin
from forms import *
from flask_gravatar import Gravatar
import os
from datetime import datetime
from tables import create_tables
from authentication import Authentication

# Create flask app
app = Flask(__name__)
# Add the secret key
app.config['SECRET_KEY'] = os.environ.get('SECRET_KEY', os.urandom(20).hex())
# init CkEditor
ckeditor = CKEditor(app)
# init Bootstrap
Bootstrap(app)
# Create a object from the LoginManager class
login_manager = LoginManager()
login_manager.init_app(app=app)
# Int Gravatar
gravatar = Gravatar(app,
                    size=100,
                    rating='g',
                    default='retro',
                    force_default=False,
                    force_lower=False,
                    use_ssl=False,
                    base_url=None)
# CONNECT TO DB
app.config['SQLALCHEMY_DATABASE_URI'] = os.environ.get('DATABASE_URL', 'sqlite:///database.db')
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
db = SQLAlchemy(app)
# Create tables
User, NotConfirmedAccount, BlogPost, Comment = create_tables(db, UserMixin=UserMixin)

db.create_all()

authentication = Authentication()


@login_manager.user_loader
def load_user(user_id):
    return User.query.filter_by(id=user_id).first()


def admin_only(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if not current_user.is_admin:
            return abort(403, "Access denied")
        else:
            return f(*args, **kwargs)

    return decorated_function


@app.context_processor
def inject_now():
    return {'now': datetime.now().utcnow()}


@app.route('/')
def get_all_posts():
    posts: list = BlogPost.query.all()
    # Revers the post list
    posts.reverse()
    return render_template("index.html", all_posts=posts)


@app.route('/register', methods=['GET', 'POST'])
def register():
    global authentication
    # Create a object from RegisterForm
    register_form = RegisterForm()

    if register_form.validate_on_submit():
        if User.query.filter_by(email=register_form.email.data).first():
            flash("You've already signed up that email, log in instead!", "error")
            return redirect(url_for('login'))
        else:
            not_confirmed_user = NotConfirmedAccount()
            while True:
                not_confirmed_user.id = os.urandom(20).hex()
                not_confirmed_user.name = register_form.name.data
                not_confirmed_user.email = register_form.email.data
                not_confirmed_user.password = generate_password_hash(
                    register_form.password.data,
                    salt_length=int(os.environ.get('SALT_LENGTH', '10')))

                db.session.add(not_confirmed_user)
                try:
                    db.session.commit()
                except IntegrityError:
                    pass
                else:
                    break
            text_message_body = " this is your account confirmation email, please copy and past in to your web " \
                                "browser or click on the below link."
            # HTML
            subheading = "Email confirmation to confirm your email and your account is created yourself in my blog."
            description = "please copy and past in to your web browser url bar or click once on the link blow "
            authentication.back_to_default(not_confirmed_user)
            authentication.email_confirmation(text_message_body, subheading, description, subject='Email confirmation',
                                              end_point='account-confirmation/email')

            flash(
                "We are send confirmation email to your email address, please follow the instruction to activate your "
                "account.",
                "Warning")
            return redirect(url_for('get_all_posts'))

    return render_template("register.html", form=register_form)


@app.route('/account-confirmation/email/<jwt_token>')
def confirm_account_as_email(jwt_token):
    if not current_user.is_authenticated:
        email = ''
        print(authentication)
        if authentication is not None:
            email = authentication.check_email_confirmation(jwt_token)
        if email:
            # Find user from  Not Authenticated table.
            not_confirmed_accounts = NotConfirmedAccount.query.filter_by(email=email).all()
            if len(not_confirmed_accounts) == 1:
                user = not_confirmed_accounts[0]
            else:
                user = not_confirmed_accounts[-1]
            # Add authenticated user in to User table
            confirmed_user = User()
            confirmed_user.id = user.id
            confirmed_user.name = user.name
            confirmed_user.email = user.email
            confirmed_user.password = user.password
            confirmed_user.account_created_time = user.create_time
            confirmed_user.is_email_confirmed = True
            confirmed_user.is_account_active = True
            confirmed_user.email_confirmed_time = datetime.now()
            confirmed_user.email_confirmed_time = datetime.now()
            db.session.add(confirmed_user)
            db.session.commit()
            # Remove  authenticated user entry in the Not Authenticated table.
            for not_confirmed_account in not_confirmed_accounts:
                db.session.delete(not_confirmed_account)
            db.session.commit()
            login_user(confirmed_user, True)
            flash("You are successfully authenticated now. thank you for visiting my blog.", "success")
            return redirect(url_for("get_all_posts"))
        else:

            return redirect(url_for('resend_verification'))
    else:
        return redirect(url_for('get_all_posts'))


@app.route('/account-confirmation/email/resend/', methods=['GET', 'POST'])
def resend_verification():
    global authentication
    if not current_user.is_authenticated:
        resend_email_form = ResendEmailFrom()
        if resend_email_form.validate_on_submit():
            user_email_data = resend_email_form.email.data

            not_confirmed_accounts = NotConfirmedAccount.query.filter_by(email=user_email_data).all()
            not_confirmed_accounts_length = len(not_confirmed_accounts)
            not_confirmed_account = None

            if not_confirmed_accounts_length == 0:
                not_confirmed_account = not_confirmed_accounts[0]
            else:
                for not_confirmed_account_index in range(0, not_confirmed_accounts_length - 1):
                    db.session.delete(not_confirmed_accounts[not_confirmed_account_index])
                    db.session.commit()
                    not_confirmed_account = not_confirmed_accounts[-1]

            if not_confirmed_account.email == user_email_data:
                text_message_body = " this is your account confirmation email, please copy and past in to your web " \
                                    "browser or click on the below link."
                # HTML
                subheading = "Email confirmation to confirm your email and your account is created yourself in my blog."
                description = "please copy and past in to your web browser url bar or click once on the link blow "
                authentication.back_to_default(not_confirmed_account)
                authentication.email_confirmation(text_message_body, subheading, description,
                                                  subject='Email confirmation',
                                                  end_point='account-confirmation/email')

                flash("We are send confirmation email to your email address, please follow the instruction to activate "
                      "your "
                      "account.",
                      "Warning")
                return redirect(url_for('get_all_posts'))
            elif not (not_confirmed_account.email == user_email_data):
                flash("You are not author of this account. you cant access any ones account.")
                return redirect(url_for('login'))
            else:
                flash("You are already confirmed your email address. please log in to your account normally")
                return redirect(url_for('login'))

        else:
            return render_template('email_confirmation.html', form=resend_email_form)
    else:
        return redirect('/')


@app.route('/login', methods=['GET', 'POST'])
def login():
    login_form = LoginForm()
    if login_form.validate_on_submit():
        email_data = login_form.email.data
        user = User.query.filter_by(email=email_data).first()
        not_confirmed_account = NotConfirmedAccount.query.filter_by(email=email_data).all()

        if user is not None:
            if user.is_account_active:
                if check_password_hash(user.password, login_form.password.data):
                    login_user(user, True)
                    return redirect(url_for('get_all_posts'))
                else:
                    flash("Password incorrect. please try again", "error")
                    return redirect(url_for('login'))
            else:
                flash("Your account is not activating. please try again or contact me.", "error")
                return redirect(url_for('resend_verification'))
        else:
            if len(not_confirmed_account) != 0:
                flash("Your account is not activating. please try again or contact me.", "error")
                return redirect(url_for('resend_verification'))
            else:
                flash("Email is does not exist, please try again.", "error")
                return redirect(url_for("login"))
    return render_template("login.html", form=login_form)


@app.route('/change_email/<new_email>')
@login_required
def change_email(new_email):
    global authentication
    user = User.query.filter_by(id=current_user.id).first()
    user.is_changing_email = True
    user.is_email_confirmed = False
    db.session.commit()
    text_message_body = "this is your email confirmation, please copy and past in to your " \
                        "web browser or click on the " \
                        "billow link. "
    # HTML
    subheading = "Email confirmation to change current email address to you provided new email address."
    description = "please copy and past in to your web browser url bar or click once on the link blow "
    authentication.back_to_default(user)
    authentication.email_confirmation(text_message_body, subheading, description, subject='Email confirmation',
                                      end_point='change_email/check', another_data={'new_email': new_email})
    flash("A confirmation email now sent to your email. please follow it to change you email.")
    return redirect(url_for('user_profile'))


@app.route('/change_email/check/<jwt_token>')
def change_email_now(jwt_token):
    global authentication
    if authentication is not None:
        data = authentication.check_email_confirmation(jwt_token)
        if data:
            new_email = data['another_data']['new_email']
            user = User.query.filter_by(id=current_user.id).first()
            if len(User.query.filter_by(email=new_email).all()) == 0:
                user.email = new_email
                user.is_email_confirmed = True
                user.is_changing_email = False
                user.last_email_changed_time = datetime.now()
                user.is_account_active = True
                db.session.commit()
                flash("Your email is successfully changed.")
            else:
                user.is_changing_email = False
                user.is_email_confirmed = True
                user.is_account_active = True
                flash("Your email is changing is unsuccessful.")
            return redirect(url_for('user_profile'))
        else:
            flash("This is not your email")
            return redirect('/')
    else:
        flash("Email Changing is field, because server error.")
        return redirect('/')


@app.route('/change_password/<user_id>', methods=['GET', 'POST'])
@login_required
def change_password(user_id):
    global authentication
    if current_user.id == user_id:
        form = ChangePasswordForm()
        if form.validate_on_submit():
            new_password = form.new_password.data
            if not check_password_hash(current_user.password, new_password):
                if new_password == form.confirm_new_password.data:
                    user = User.query.filter_by(id=current_user.id).first()
                    if user:
                        requested_ip = request.remote_addr
                        text_message_body = "Your password change request"
                        # HTML
                        subheading = " if you are requested change your password to new password."
                        description = f"""
                                <h1Request from</h1> 
                                <p>ip:{requested_ip}</p>
                                <p>Time: {datetime.now()}</p>
                                <p>Name: {user.name} </p>
                                <p>email: {user.email} </p> <br> <h2 style='color: blue;'>If this is only request 
                                you, click billow like to change user password</h2> 
                                
                        """
                        authentication.back_to_default(user)
                        authentication.email_confirmation(text_message_body, subheading, description,
                                                          subject='Email confirmation',
                                                          end_point='change_password/check',
                                                          another_data={'new_password': new_password})

                        flash("A confirmation email now sent to your email. please follow it to change you email.")
                        user.is_changing_password = True
                        db.session.commit()
                        return redirect(url_for('user_profile', user_id=user_id))
                    else:
                        flash("You can't change password because this account is not your own.")
                        return redirect(url_for('user_profile', user_id=user_id))
                else:
                    flash("New password is not maths to confirm new password")
                    return redirect(url_for('change_password', user_id=user_id))
            else:
                flash("Current password is not valid")
                return redirect(url_for('change_password', user_id=user_id))
        else:
            return render_template('change_password.html', form=form)


@app.route('/change_password/check/<token>')
def check_change_password(token):
    global authentication
    if authentication is not None:
        data = authentication.check_email_confirmation(token)

        if data:
            user = User.query.filter_by(email=data['email']).first()
            user.is_changing_password = False
            user.password = generate_password_hash(data['another_data']['new_password'], salt_length=10)
            user.last_password_changed_time = datetime.now()
            db.session.commit()
            flash("Password change is successful.")
            return redirect(url_for('user_profile'))
        else:
            flash('Password is  change is unsuccessful.')
            return redirect(url_for('change_password'))
    else:
        return redirect('/')


@login_required
@app.route('/profile', methods=['GET', 'POST'])
def user_profile():
    user = User.query.filter_by(id=current_user.id).first()
    user_profile_form = UserProfileFrom(name=user.name, email=user.email, password=user.password)

    if user_profile_form.validate_on_submit():
        if user_profile_form.email.data != user.email:
            return redirect(url_for('change_email', new_email=user_profile_form.email.data))
        elif not check_password_hash(user.password,
                                     user_profile_form.password.data) and user_profile_form.password.data != '':
            return redirect(url_for('change_password', user_id=user.id))
        elif user_profile_form.name.data != user.name:
            user.name = user_profile_form.name.data
            db.session.commit()
            flash("Your name is successful changed.")
        else:
            return redirect(url_for('user_profile'))

        return redirect(url_for('user_profile'))

    return render_template('user_profile.html', form=user_profile_form)


@app.route('/logout')
@login_required
def logout():
    global authentication
    authentication = Authentication()
    logout_user()
    return redirect(url_for('get_all_posts'))


@app.route("/post/<post_id>", methods=['GET', 'POST'])
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
                except IntegrityError:
                    pass
                else:
                    break
            flash("Your Post is created now")
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
            except IntegrityError:
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


@app.route('/delete/user/<user_id>', methods=['GET', 'POST'])
@login_required
def delete_user(user_id):
    if not current_user.is_admin:
        user = User.query.filter_by(id=user_id).first()
        db.session.delete(user)
        db.session.commit()
        flash("Your account is successes delete")
        return redirect(url_for('get_all_posts'))
    else:
        flash("I don't  want to delete_my_account because I am the admin of this Website / Blog.")
        return redirect(url_for('user_profile'))


if __name__ == "__main__":
    app.run()
