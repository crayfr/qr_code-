from flask import Flask, request, render_template, flash, redirect, url_for
import csv
import os
import qrcode
import hashlib

app = Flask(__name__)
app.secret_key = 'replace-with-your-secret'

DATA_FILE = 'data.csv'
QR_FOLDER = os.path.join('static', 'qr_codes')

# Ensure storage exists
os.makedirs(QR_FOLDER, exist_ok=True)
if not os.path.exists(DATA_FILE):
    with open(DATA_FILE, 'w', newline='') as f:
        writer = csv.writer(f)
        writer.writerow(['hash', 'qr_filename'])


def hash_id(id_str):
    return hashlib.sha256(id_str.encode()).hexdigest()


@app.route('/', methods=['GET', 'POST'])
def index():
    qr_filename = None

    if request.method == 'POST':
        id_value = request.form.get('unique_id', '').strip()
        if not id_value:
            flash('ID cannot be empty', 'error')
            return redirect(url_for('index'))

        hashed_id = hash_id(id_value)

        # Read existing hashed IDs
        with open(DATA_FILE, newline='') as f:
            reader = csv.DictReader(f)
            existing = {row['hash'] for row in reader}

        if hashed_id in existing:
            flash(f"ID already exists.", 'error')
            return redirect(url_for('index'))

        # Generate QR code based on raw input
        qr = qrcode.make(id_value)
        qr_filename = f"{hashed_id[:10]}.png"
        qr_path = os.path.join(QR_FOLDER, qr_filename)
        qr.save(qr_path)

        # Append to CSV
        with open(DATA_FILE, 'a', newline='') as f:
            writer = csv.writer(f)
            writer.writerow([hashed_id, qr_filename])

        flash(f"ID saved and QR code created.", 'success')

    return render_template('index.html', qr_filename=qr_filename)


if __name__ == '__main__':
    app.run(debug=True)