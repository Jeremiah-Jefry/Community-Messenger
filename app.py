import html
from flask import Flask, render_template, redirect, url_for, request, flash
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager, login_user, login_required, logout_user, UserMixin, current_user
from flask_socketio import SocketIO, emit, join_room
from werkzeug.security import generate_password_hash, check_password_hash
import datetime
import pytz

# Setup
app = Flask(__name__)
app.config['SECRET_KEY'] = "devkey-for-final-project"
app.config['SQLALCHEMY_DATABASE_URI'] = "sqlite:///messenger.db"
db = SQLAlchemy(app)
socketio = SocketIO(app, cors_allowed_origins="*")
login = LoginManager(app)
login.login_view = "login"

# --- Timezone Conversion Filter ---
def to_ist(utc_dt):
    if utc_dt is None:
        return ""
    ist_timezone = pytz.timezone('Asia/Kolkata')
    return pytz.utc.localize(utc_dt).astimezone(ist_timezone).strftime('%I:%M %p')

app.jinja_env.filters['to_ist'] = to_ist


# --- Database Models ---
group_members = db.Table('group_members',
    db.Column('user_id', db.Integer, db.ForeignKey('user.id'), primary_key=True),
    db.Column('group_id', db.Integer, db.ForeignKey('group.id'), primary_key=True)
)

class User(UserMixin, db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(50), unique=True, nullable=False)
    password = db.Column(db.String(128), nullable=False)

class Group(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), unique=True, nullable=False)
    members = db.relationship('User', secondary=group_members, lazy='subquery',
        backref=db.backref('groups', lazy=True))

class Message(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    text = db.Column(db.String(500), nullable=False)
    timestamp = db.Column(db.DateTime, default=datetime.datetime.utcnow)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    group_id = db.Column(db.Integer, db.ForeignKey('group.id'), nullable=False)
    user = db.relationship('User')
    group = db.relationship('Group')

@login.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))

# --- Routes ---
@app.route("/")
def home():
    if current_user.is_authenticated:
        return redirect(url_for("groups"))
    return render_template("index.html")

@app.route("/register", methods=["GET", "POST"])
def register():
    if request.method == "POST":
        username = request.form["username"]
        password = request.form["password"]
        if User.query.filter_by(username=username).first():
            flash("Username already taken")
            return redirect(url_for("register"))
        user = User(username=username, password=generate_password_hash(password))
        db.session.add(user)
        db.session.commit()
        flash("Registered! Please log in.")
        return redirect(url_for("login"))
    return render_template("register.html")

@app.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        username = request.form["username"]
        password = request.form["password"]
        user = User.query.filter_by(username=username).first()
        if user and check_password_hash(user.password, password):
            login_user(user)
            return redirect(url_for("groups"))
        flash("Invalid username or password")
    return render_template("login.html")

@app.route("/logout")
@login_required
def logout():
    logout_user()
    return redirect(url_for("home"))

@app.route("/groups", methods=["GET", "POST"])
@login_required
def groups():
    if request.method == "POST":
        group_name = request.form.get("group_name")
        if group_name and not Group.query.filter_by(name=group_name).first():
            new_group = Group(name=group_name)
            new_group.members.append(current_user)
            db.session.add(new_group)
            db.session.commit()
            flash(f"Group '{group_name}' created!")
            return redirect(url_for('groups'))
        else:
            flash("Group name already exists or is invalid.")
    all_groups = Group.query.all()
    return render_template("groups.html", user_groups=current_user.groups, all_groups=all_groups)

@app.route("/join_group/<int:group_id>")
@login_required
def join_group(group_id):
    group = Group.query.get_or_404(group_id)
    if current_user not in group.members:
        group.members.append(current_user)
        db.session.commit()
        flash(f"You have joined the group '{group.name}'!")
    else:
        flash("You are already a member of this group.")
    return redirect(url_for('groups'))

@app.route("/dashboard")
@login_required
def dashboard():
    all_users = User.query.all()
    total_users = len(all_users)
    return render_template("dashboard.html", total_users=total_users, all_users=all_users)

@app.route("/chat/<int:group_id>")
@login_required
def chat(group_id):
    group = Group.query.get_or_404(group_id)
    if current_user not in group.members:
        flash("You are not a member of this group.")
        return redirect(url_for('groups'))
    messages = Message.query.filter_by(group_id=group.id).order_by(Message.timestamp.asc()).all()
    return render_template("chat.html", user=current_user, group=group, messages=messages)

# State for online users: {group_id: {user_id, ...}, ...}
online_users = {}

# --- Socket Events ---
@socketio.on('join')
def on_join(data):
    room = data['room']
    join_room(room)

    if room not in online_users:
        online_users[room] = set()
    online_users[room].add(current_user.id)

    users_in_room = User.query.filter(User.id.in_(online_users[room])).all()
    usernames = [user.username for user in users_in_room]

    emit('update_online_users', {'users': usernames}, to=room)

@socketio.on('disconnect')
def on_disconnect():
    for room, users in online_users.items():
        if hasattr(current_user, 'id') and current_user.id in users:
            users.remove(current_user.id)
            users_in_room = User.query.filter(User.id.in_(users)).all()
            usernames = [user.username for user in users_in_room]
            emit('update_online_users', {'users': usernames}, to=room)
            break

@socketio.on("send_message")
def handle_message(data):
    if not current_user.is_authenticated:
        return

    room = data['room']
    safe_text = html.escape(data["text"])
    timestamp_utc = datetime.datetime.utcnow()

    message = Message(text=safe_text, user_id=current_user.id, group_id=int(room), timestamp=timestamp_utc)
    db.session.add(message)
    db.session.commit()

    # Convert UTC timestamp to IST for real-time display
    ist_timezone = pytz.timezone('Asia/Kolkata')
    timestamp_ist = pytz.utc.localize(timestamp_utc).astimezone(ist_timezone)

    msg = {
        "username": current_user.username,
        "text": safe_text,
        "timestamp": timestamp_ist.strftime('%I:%M %p')
    }
    emit("receive_message", msg, broadcast=True, to=room)

# --- Run Application ---
if __name__ == "__main__":
    with app.app_context():
        db.create_all()
    socketio.run(app, debug=True, allow_unsafe_werkzeug=True)