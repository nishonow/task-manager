from flask import Flask, request, jsonify, send_from_directory, render_template, redirect, url_for, flash
from sqlalchemy.orm import Session
from database import SessionLocal, engine
import models
import logging
from flask_login import LoginManager, login_user, login_required, logout_user, current_user

app = Flask(__name__, static_folder='static')
app.secret_key = 'your-secret-key'  # Replace with a secure key
logging.basicConfig(level=logging.DEBUG)

login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = 'login'

@login_manager.user_loader
def load_user(user_id):
    db = SessionLocal()
    user = db.query(models.User).filter(models.User.id == int(user_id)).first()
    db.close()
    return user

# Create database tables
models.Base.metadata.create_all(bind=engine)

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

@app.route('/')
def serve_index():
    if current_user.is_authenticated:
        return render_template('index.html')
    return redirect(url_for('login'))

@app.route('/styles.css')
def serve_styles():
    return send_from_directory('static', 'styles.css')

@app.route('/scripts.js')
def serve_scripts():
    return send_from_directory('static', 'scripts.js')

@app.route('/login', methods=['GET', 'POST'])
def login():
    if current_user.is_authenticated:
        return redirect(url_for('serve_index'))
    if request.method == 'POST':
        email = request.json.get('email')
        password = request.json.get('password')
        db = next(get_db())
        user = db.query(models.User).filter(models.User.email == email).first()
        if user and user.check_password(password):
            login_user(user)
            return jsonify({"message": "Logged in successfully"}), 200
        return jsonify({"error": "Invalid email or password"}), 401
    return render_template('login.html')

@app.route('/register', methods=['GET', 'POST'])
def register():
    if current_user.is_authenticated:
        return redirect(url_for('serve_index'))
    if request.method == 'POST':
        email = request.json.get('email')
        password = request.json.get('password')
        db = next(get_db())
        existing_user = db.query(models.User).filter(models.User.email == email).first()
        if existing_user:
            return jsonify({"error": "Email already registered"}), 400
        user = models.User(email=email)
        user.set_password(password)
        db.add(user)
        db.commit()
        login_user(user)
        return jsonify({"message": "Registered successfully"}), 201
    return render_template('register.html')

@app.route('/api/user', methods=['GET'])
@login_required
def get_user():
    try:
        return jsonify({"email": current_user.email}), 200
    except Exception as e:
        logging.error(f"Error fetching user: {e}")
        return jsonify({"error": "Failed to fetch user"}), 500


@app.route('/profile', methods=['GET', 'POST'])
@login_required
def profile():
    if request.method == 'POST':
        db = next(get_db())
        try:
            data = request.json
            new_email = data.get('email', '').strip()
            new_password = data.get('password', '').strip()

            user = db.query(models.User).filter(models.User.id == current_user.id).first()

            if new_email:
                existing_user = db.query(models.User).filter(models.User.email == new_email,
                                                             models.User.id != current_user.id).first()
                if existing_user:
                    return jsonify({"error": "Email already in use by another user"}), 400
                user.email = new_email

            if new_password:
                user.set_password(new_password)

            db.add(user)  # Ensure the user is added to the session
            db.commit()
            return jsonify({"message": "Profile updated successfully"}), 200
        except Exception as e:
            db.rollback()  # Roll back on error
            logging.error(f"Error updating profile: {e}")
            return jsonify({"error": "Failed to update profile"}), 500
    return render_template('profile.html')

@app.route('/logout', methods=['POST'])
@login_required
def logout():
    logout_user()
    return jsonify({"message": "Logged out successfully"}), 200

@app.route('/api/tasks/', methods=['POST'])
@login_required
def create_task():
    db = next(get_db())
    try:
        data = request.get_json()
        if not data or not data.get('title'):
            return jsonify({"error": "Title is required"}), 400
        task = models.Task(
            title=data['title'],
            description=data.get('description'),
            completed=data.get('completed', False),
            user_id=current_user.id
        )
        db.add(task)
        db.commit()
        db.refresh(task)
        return jsonify({
            'id': task.id,
            'title': task.title,
            'description': task.description,
            'completed': task.completed
        }), 201
    except Exception as e:
        logging.error(f"Error in create_task: {e}")
        return jsonify({"error": "Internal server error"}), 500

@app.route('/api/tasks/', methods=['GET'])
@login_required
def read_tasks():
    db = next(get_db())
    try:
        tasks = db.query(models.Task).filter(models.Task.user_id == current_user.id).all()
        return jsonify([{
            'id': task.id,
            'title': task.title,
            'description': task.description,
            'completed': task.completed
        } for task in tasks])
    except Exception as e:
        logging.error(f"Error in read_tasks: {e}")
        return jsonify({"error": "Internal server error"}), 500

@app.route('/api/tasks/<int:task_id>', methods=['GET'])
@login_required
def read_task(task_id):
    db = next(get_db())
    try:
        task = db.query(models.Task).filter(models.Task.id == task_id, models.Task.user_id == current_user.id).first()
        if not task:
            return jsonify({"error": "Task not found"}), 404
        return jsonify({
            'id': task.id,
            'title': task.title,
            'description': task.description,
            'completed': task.completed
        })
    except Exception as e:
        logging.error(f"Error in read_task: {e}")
        return jsonify({"error": "Internal server error"}), 500

@app.route('/api/tasks/<int:task_id>', methods=['PUT'])
@login_required
def update_task(task_id):
    db = next(get_db())
    try:
        task = db.query(models.Task).filter(models.Task.id == task_id, models.Task.user_id == current_user.id).first()
        if not task:
            return jsonify({"error": "Task not found"}), 404
        data = request.get_json()
        for key, value in data.items():
            if key in ['title', 'description', 'completed']:
                setattr(task, key, value)
        db.commit()
        db.refresh(task)
        return jsonify({
            'id': task.id,
            'title': task.title,
            'description': task.description,
            'completed': task.completed
        })
    except Exception as e:
        logging.error(f"Error in update_task: {e}")
        return jsonify({"error": "Internal server error"}), 500

@app.route('/api/tasks/<int:task_id>', methods=['DELETE'])
@login_required
def delete_task(task_id):
    db = next(get_db())
    try:
        task = db.query(models.Task).filter(models.Task.id == task_id, models.Task.user_id == current_user.id).first()
        if not task:
            return jsonify({"error": "Task not found"}), 404
        db.delete(task)
        db.commit()
        return jsonify({"message": "Task deleted"})
    except Exception as e:
        logging.error(f"Error in delete_task: {e}")
        return jsonify({"error": "Internal server error"}), 500

if __name__ == '__main__':
    app.run(debug=True, port=8080)