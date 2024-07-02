from flask import Blueprint, render_template, request, redirect, url_for, flash, session
from werkzeug.security import generate_password_hash, check_password_hash
from .models import User
from . import db, mail, mongo
from flask_login import login_user, login_required, logout_user, current_user
from flask_mail import Message
from itsdangerous import URLSafeTimedSerializer, SignatureExpired
import pickle
from datetime import datetime

auth = Blueprint('auth', __name__)

s = URLSafeTimedSerializer('random-secret')

def log_activity(activty_type, description):
    activity_log = {
        "activity_type" : activty_type,
        "description" : description,
        "timestamp" : datetime.now(),
        "user_id" : get_current_user()
    }
    mongo.db.activity_logs.insert_one(activity_log)


def get_current_user():
    user = session.get('user')
    if user:
        user_data = pickle.loads(user)
        user_obj = User.query.get(user_data.id)
        if user_obj:
            return int(user_obj.id)
    return None

@auth.route("/login", methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        email = request.form.get('email')
        password = request.form.get('password')

        user = User.query.filter_by(email=email).first()

        if user:
            if check_password_hash(user.password, password) and user.confirmed:
                flash("Logged in", category="success")
                login_user(user, remember=True)
                log_activity("login", f"User {user.firstName} logged in")
                user_json = pickle.dumps(user)
                session['user'] = user_json
                return redirect(url_for('views.home'))
            else:
                flash("Incorrect password", category="error")
                log_activity("failed_login_attempt", f"User {user.firstName} entered incorrect password")
                
        else:
            flash("User does not exist", category="error")
            log_activity("failed_login_attempt", f"User does not exist")

    return render_template("login.html", user=current_user)


@auth.route("/logout")
@login_required
def logout():
    logout_user()
    session.pop('user', None)
    log_activity("logout", f"User logged out")
    return redirect(url_for("auth.login"))


@auth.route("/signup", methods=['GET', 'POST'])
def signup():
    if request.method == 'POST':
        email = request.form.get('email')
        firstName = request.form.get('firstName')
        password1 = request.form.get('password1')
        password2 = request.form.get('password2')

        user = User.query.filter_by(email=email).first()
        if user:
            flash('Email already exists.', category='error')
        elif password1 != password2:
            flash('Passwords don\'t match.', category='error')
        else:
            token = s.dumps(email, salt='email-confirm')

            msg = Message("Verify email", recipients=[email])
            link = url_for("auth.confirm_email", token=token, _external = True)
            msg.body = f"Please click on the link to verify your email: {link}"
            mail.send(msg)


            new_user = User(email=email, firstName=firstName, password=generate_password_hash(password1, method='pbkdf2:sha256'))
            db.session.add(new_user)
            db.session.commit()
            # login_user(new_user, remember=True)
            log_activity("signup", f"User {new_user.firstName} signed up")
            log_activity("verification_email_sent", f"User {new_user.firstName} was sent the verification email")
            flash('Verification Email sent. Please verify your email!', category='success')
            return redirect(url_for('auth.login'))

    return render_template("sign_up.html", user=current_user)


@auth.route("/confirm_email/<token>")
def confirm_email(token):
    try:
        email = s.loads(token, salt='email-confirm', max_age=3600)
    except:
        flash("The link is either invalid or expired!", category="error")
    
    user = User.query.filter_by(email=email).first()
    if user:
        if user.confirmed:
            flash("Account already confirmed. Please login!", category="success")
        else:
            user.confirmed = True
            db.session.commit()
            flash("Email confirmed! You can now login!", category="success")
            log_activity("user_verified", f"User {user.firstName} verified their email")
            return redirect(url_for("auth.login"))
    else:
        flash("Invalid email! Please signup", category="error")
        return redirect(url_for("auth.signup"))
    

@auth.route('/activity_logs')
def activity_logs():
    logs = list(mongo.db.activity_logs.find())
    return render_template('activity_logs.html', logs=logs, user=current_user)