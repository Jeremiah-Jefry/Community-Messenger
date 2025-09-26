import html # Added for server-side HTML escaping
from flask import Flask, render_template, redirect, url_for, request, flash
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager, login_user, login_required, logout_user, UserMixin, current_user
from flask_socketio import SocketIO, emit
from werkzeug.security import generate_password_hash, check_password_hash

# Setup
app = Flask(__name__)
app.config['SECRET_KEY'] = "devkey"
app.config['SQLALCHEMY_DATABASE_URI'] = "sqlite:///messenger.db"
db = SQLAlchemy(app)
socketio = SocketIO(app, cors_allowed_origins="*")
login = LoginManager(app)
login.login_view = "login"

# User model
class User(UserMixin, db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(50), unique=True, nullable=False)
    password = db.Column(db.String(128), nullable=False)

@login.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))

# Routes
@app.route("/")
def home():
    if current_user.is_authenticated:
        return redirect(url_for("chat"))
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
            return redirect(url_for("chat"))
        flash("Invalid username or password")
    return render_template("login.html")

@app.route("/logout")
@login_required
def logout():
    logout_user()
    return redirect(url_for("home"))

@app.route("/chat")
@login_required
def chat():
    return render_template("chat.html", username=current_user.username)

@app.route("/dashboard")
@login_required
def dashboard():
    # Query the total number of users
    total_users = db.session.query(User).count()
    return render_template("dashboard.html", total_users=total_users)

# Socket events
@socketio.on("send_message")
def handle_message(data):
    # Sanitize the message text before broadcasting it to all clients
    # This prevents Cross-Site Scripting (XSS) by turning HTML tags into literal text
    safe_text = html.escape(data["text"])
    msg = {"username": current_user.username, "text": safe_text}
    emit("receive_message", msg, broadcast=True)

# Run
if __name__ == "__main__":
    with app.app_context():
        db.create_all()
    socketio.run(app, debug=True)