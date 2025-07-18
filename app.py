from flask import Flask, request, render_template, flash, redirect, url_for, session, send_file
import csv
import os
import qrcode
import hashlib
from datetime import datetime
from PIL import Image
from werkzeug.security import generate_password_hash, check_password_hash

app = Flask(__name__)
app.secret_key = os.environ.get('FLASK_SECRET_KEY', 'replace-with-your-secret')

DATA_FILE = 'data.csv'
USER_FILE = 'users.csv'
ATTENDANCE_FILE = 'attendance.csv'
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
QR_FOLDER = os.path.join(BASE_DIR, 'static', 'qr_codes')

# Init dirs and files
os.makedirs(QR_FOLDER, exist_ok=True)

if not os.path.exists(DATA_FILE):
    with open(DATA_FILE, 'w', newline='') as f:
        writer = csv.writer(f)
        writer.writerow(['user_id', 'hash', 'qr_filename', 'created_at', 'id_value'])

if not os.path.exists(USER_FILE):
    with open(USER_FILE, 'w', newline='') as f:
        writer = csv.writer(f)
        writer.writerow(['user_id', 'username', 'email', 'password_hash'])

if not os.path.exists(ATTENDANCE_FILE):
    with open(ATTENDANCE_FILE, 'w', newline='') as f:
        writer = csv.writer(f)
        writer.writerow(['student_id', 'name', 'timestamp'])

def hash_id(id_str):
    return hashlib.sha256(id_str.encode()).hexdigest()

def get_user_by_email(email):
    with open(USER_FILE, newline='') as f:
        reader = csv.DictReader(f)
        for row in reader:
            if row['email'] == email:
                return row
    return None

def get_qr_history(user_id):
    history = []
    with open(DATA_FILE, newline='') as f:
        reader = csv.DictReader(f)
        for row in reader:
            if row['user_id'] == user_id:
                history.append(row)
    return history[::-1][:10]

@app.route('/register', methods=['GET', 'POST'])
def register():
    if 'user_id' in session:
        flash('You are already logged in.', 'error')
        return redirect(url_for('index'))

    if request.method == 'POST':
        username = request.form.get('username', '').strip()
        email = request.form.get('email', '').strip()
        password = request.form.get('password', '').strip()

        if not username or not email or not password:
            flash('All fields are required.', 'error')
            return redirect(url_for('register'))

        if get_user_by_email(email):
            flash('Email already registered.', 'error')
            return redirect(url_for('register'))

        user_id = hashlib.sha256(email.encode()).hexdigest()
        password_hash = generate_password_hash(password)

        with open(USER_FILE, 'a', newline='') as f:
            writer = csv.writer(f)
            writer.writerow([user_id, username, email, password_hash])

        flash('Registration successful. Please log in.', 'success')
        return redirect(url_for('login'))

    return render_template('register.html')

@app.route('/login', methods=['GET', 'POST'])
def login():
    if 'user_id' in session:
        flash('You are already logged in.', 'error')
        return redirect(url_for('index'))

    if request.method == 'POST':
        email = request.form.get('email', '').strip()
        password = request.form.get('password', '').strip()

        if not email or not password:
            flash('Email and password are required.', 'error')
            return redirect(url_for('login'))

        user = get_user_by_email(email)
        if user and check_password_hash(user['password_hash'], password):
            session['user_id'] = user['user_id']
            session['username'] = user['username']
            flash('Login successful.', 'success')
            return redirect(url_for('index'))
        else:
            flash('Invalid email or password.', 'error')
            return redirect(url_for('login'))

    return render_template('login.html')

@app.route('/logout')
def logout():
    session.clear()
    flash('Logged out.', 'success')
    return redirect(url_for('login'))

@app.route('/', methods=['GET', 'POST'])
def index():
    if 'user_id' not in session:
        flash('Please log in.', 'error')
        return redirect(url_for('login'))

    qr_filename = session.get('qr_filename')
    qr_history = get_qr_history(session['user_id'])

    if request.method == 'POST':
        id_value = request.form.get('unique_id', '').strip()
        qr_color = request.form.get('qr_color', '#000000')
        qr_size = int(request.form.get('qr_size', 10))

        if not id_value:
            flash('ID is required.', 'error')
            return render_template('index.html', qr_filename=qr_filename, qr_history=qr_history, username=session.get('username'))

        hashed_id = hash_id(id_value)

        with open(DATA_FILE, newline='') as f:
            reader = csv.DictReader(f)
            existing = {row['hash'] for row in reader if row['user_id'] == session['user_id']}
            if hashed_id in existing:
                flash('ID already exists.', 'error')
                return render_template('index.html', qr_filename=qr_filename, qr_history=qr_history, username=session.get('username'))

        qr = qrcode.QRCode(
            version=1,
            error_correction=qrcode.constants.ERROR_CORRECT_L,
            box_size=qr_size,
            border=4,
        )
        qr.add_data(id_value)
        qr.make(fit=True)
        img = qr.make_image(fill_color=qr_color, back_color="white")

        qr_filename = f"{session['user_id'][:10]}_{hashed_id[:10]}.png"
        qr_path = os.path.join(QR_FOLDER, qr_filename)
        img.save(qr_path)

        with open(DATA_FILE, 'a', newline='') as f:
            writer = csv.writer(f)
            writer.writerow([session['user_id'], hashed_id, qr_filename, datetime.now().isoformat(), id_value])

        session['qr_filename'] = qr_filename
        flash('QR code created.', 'success')
        return redirect(url_for('index'))

    return render_template('index.html', qr_filename=qr_filename, qr_history=qr_history, username=session.get('username'))

@app.route('/download/<filename>/<format>')
def download_qr(filename, format):
    if 'user_id' not in session:
        flash('Please log in.', 'error')
        return redirect(url_for('login'))

    qr_path = os.path.join(QR_FOLDER, filename)
    if not os.path.exists(qr_path):
        flash("QR code not found.", "error")
        return redirect(url_for('index'))

    with open(DATA_FILE, newline='') as f:
        reader = csv.DictReader(f)
        for row in reader:
            if row['qr_filename'] == filename and row['user_id'] == session['user_id']:
                if format == 'png':
                    return send_file(qr_path, as_attachment=True)
                flash("Only PNG is available.", "error")
                return redirect(url_for('index'))

    flash("Unauthorized access.", "error")
    return redirect(url_for('index'))

@app.route("/scan")
def scan_qr():
    student_hash = request.args.get("id")
    if not student_hash:
        return "Invalid QR Code", 400

    with open(DATA_FILE, newline='') as f:
        reader = csv.DictReader(f)
        for row in reader:
            if row['hash'] == student_hash:
                return render_template("scan.html", student_id=row['hash'], name=row['id_value'])

    return "Student not found", 404

@app.route("/mark_attendance", methods=["POST"])
def mark_attendance():
    student_id = request.form.get("student_id")
    name = request.form.get("name")
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    with open(ATTENDANCE_FILE, "a", newline='') as f:
        writer = csv.writer(f)
        writer.writerow([student_id, name, timestamp])

    return render_template("thank_you.html", name=name, time=timestamp)

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port, debug=True)
