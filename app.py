from flask import Flask, request, render_template, flash, redirect, url_for, session
import csv
import os
import qrcode
import hashlib
from datetime import datetime
from io import BytesIO
from PIL import Image
import base64
from werkzeug.security import generate_password_hash, check_password_hash

app = Flask(__name__)
app.secret_key = os.environ.get('FLASK_SECRET_KEY', 'replace-with-your-secret')  # Use env variable for security

DATA_FILE = 'data.csv'
USER_FILE = 'users.csv'
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
QR_FOLDER = os.path.join(BASE_DIR, 'static', 'qr_codes')

# Initialize directories and files
try:
    os.makedirs(QR_FOLDER, exist_ok=True)
    print(f"Created/verified directory: {os.path.abspath(QR_FOLDER)}")
except Exception as e:
    print(f"Failed to create directory {QR_FOLDER}: {str(e)}")
    raise

if not os.path.exists(DATA_FILE):
    try:
        with open(DATA_FILE, 'w', newline='') as f:
            writer = csv.writer(f)
            writer.writerow(['user_id', 'hash', 'qr_filename', 'created_at', 'id_value'])
        print(f"Created QR data CSV file: {os.path.abspath(DATA_FILE)}")
    except Exception as e:
        print(f"Failed to create QR data CSV file {DATA_FILE}: {str(e)}")
        raise

if not os.path.exists(USER_FILE):
    try:
        with open(USER_FILE, 'w', newline='') as f:
            writer = csv.writer(f)
            writer.writerow(['user_id', 'username', 'email', 'password_hash'])
        print(f"Created users CSV file: {os.path.abspath(USER_FILE)}")
    except Exception as e:
        print(f"Failed to create users CSV file {USER_FILE}: {str(e)}")
        raise

def hash_id(id_str):
    try:
        return hashlib.sha256(id_str.encode()).hexdigest()
    except Exception as e:
        print(f"Error hashing ID: {str(e)}")
        return None

def get_qr_history(user_id):
    history = []
    try:
        with open(DATA_FILE, newline='') as f:
            reader = csv.DictReader(f)
            for row in reader:
                if row['user_id'] == user_id:
                    history.append({
                        'hash': row['hash'],
                        'qr_filename': row['qr_filename'],
                        'created_at': row['created_at'],
                        'id_value': row['id_value']
                    })
        return history[::-1][:10]  # Return last 10 entries for the user
    except Exception as e:
        print(f"Error reading QR history: {str(e)}")
        return []

def get_user_by_email(email):
    try:
        with open(USER_FILE, newline='') as f:
            reader = csv.DictReader(f)
            for row in reader:
                if row['email'] == email:
                    return row
        return None
    except Exception as e:
        print(f"Error reading user data: {str(e)}")
        return None

def get_user_by_id(user_id):
    try:
        with open(USER_FILE, newline='') as f:
            reader = csv.DictReader(f)
            for row in reader:
                if row['user_id'] == user_id:
                    return row
        return None
    except Exception as e:
        print(f"Error reading user data: {str(e)}")
        return None

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

        try:
            with open(USER_FILE, 'a', newline='') as f:
                writer = csv.writer(f)
                writer.writerow([user_id, username, email, password_hash])
            flash('Registration successful. Please log in.', 'success')
            return redirect(url_for('login'))
        except Exception as e:
            flash(f"Error registering user: {str(e)}", 'error')
            print(f"User registration error: {str(e)}")
            return redirect(url_for('register'))

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
    session.pop('user_id', None)
    session.pop('username', None)
    session.pop('qr_filename', None)
    flash('Logged out successfully.', 'success')
    return redirect(url_for('index'))

@app.route('/', methods=['GET', 'POST'])
def index():
    if 'user_id' not in session:
        flash('Please log in to access this page.', 'error')
        return redirect(url_for('login'))

    qr_filename = session.pop('qr_filename', None)
    qr_history = get_qr_history(session['user_id'])

    if request.method == 'POST':
        id_value = request.form.get('unique_id', '').strip()
        qr_color = request.form.get('qr_color', '#000000')
        qr_size = int(request.form.get('qr_size', 10))

        if not id_value:
            flash('ID cannot be empty', 'error')
            return redirect(url_for('index'))

        hashed_id = hash_id(id_value)
        if not hashed_id:
            flash('Failed to hash the input ID', 'error')
            return redirect(url_for('index'))
        print(f"Hashed ID: {hashed_id}")

        # Read existing hashed IDs for the user
        try:
            with open(DATA_FILE, newline='') as f:
                reader = csv.DictReader(f)
                existing = {row['hash'] for row in reader if row['user_id'] == session['user_id']}
        except Exception as e:
            flash(f"Error reading CSV file: {str(e)}", 'error')
            print(f"CSV read error: {str(e)}")
            return redirect(url_for('index'))

        if hashed_id in existing:
            flash(f"ID already exists.", 'error')
            return redirect(url_for('index'))

        # Generate and save QR code
        try:
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
            qr_path = os.path.abspath(os.path.join(QR_FOLDER, qr_filename))
            print(f"Attempting to save QR code to: {qr_path}")
            img.save(qr_path)

            if os.path.exists(qr_path):
                print(f"Successfully saved QR code: {qr_path}")
                # Append to CSV
                try:
                    with open(DATA_FILE, 'a', newline='') as f:
                        writer = csv.writer(f)
                        writer.writerow([session['user_id'], hashed_id, qr_filename, datetime.now().isoformat(), id_value])
                    print(f"Appended to CSV: {hashed_id}, {qr_filename}")
                    session['qr_filename'] = qr_filename
                    flash("ID saved and QR code created.", "success")
                except Exception as e:
                    flash(f"Error writing to CSV: {str(e)}", "error")
                    print(f"CSV write error: {str(e)}")
                    return redirect(url_for('index'))
            else:
                flash("Failed to save QR code image.", "error")
                print(f"File not found after saving: {qr_path}")
                return redirect(url_for('index'))
        except Exception as e:
            flash(f"Error generating/saving QR code: {str(e)}", "error")
            print(f"QR code generation/saving failed: {str(e)}")
            return redirect(url_for('index'))

    return render_template('index.html', qr_filename=qr_filename, qr_history=qr_history, now=datetime.now().timestamp, username=session.get('username'))

@app.route('/download/<filename>/<format>')
def download_qr(filename, format):
    if 'user_id' not in session:
        flash('Please log in to download QR codes.', 'error')
        return redirect(url_for('login'))

    qr_path = os.path.join(QR_FOLDER, filename)
    if not os.path.exists(qr_path):
        flash("QR code not found.", "error")
        return redirect(url_for('index'))

    # Verify the QR code belongs to the user
    try:
        with open(DATA_FILE, newline='') as f:
            reader = csv.DictReader(f)
            for row in reader:
                if row['qr_filename'] == filename and row['user_id'] == session['user_id']:
                    if format == 'png':
                        return send_file(qr_path, as_attachment=True)
                    elif format == 'svg':
                        flash("SVG format not implemented yet.", "error")
                        return redirect(url_for('index'))
                    elif format == 'pdf':
                        flash("PDF format not implemented yet.", "error")
                        return redirect(url_for('index'))
                    else:
                        flash("Invalid format requested.", "error")
                        return redirect(url_for('index'))
        flash("You don't have permission to download this QR code.", "error")
        return redirect(url_for('index'))
    except Exception as e:
        flash(f"Error accessing QR code: {str(e)}", "error")
        return redirect(url_for('index'))

if __name__ == '__main__':
    app.run(debug=True)