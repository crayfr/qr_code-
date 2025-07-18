from flask import Flask, request, render_template, flash, redirect, url_for
import csv
import os
import qrcode

app = Flask(__name__)
app.secret_key = 'replace-with-your-secret'

DATA_FILE = 'data.csv'
QR_FOLDER = 'qr_codes'

# Ensure storage exists
os.makedirs(QR_FOLDER, exist_ok=True)
if not os.path.exists(DATA_FILE):
    with open(DATA_FILE, 'w', newline='') as f:
        writer = csv.writer(f)
        writer.writerow(['id', 'qr_path'])


@app.route('/', methods=['GET', 'POST'])
def index():
    if request.method == 'POST':
        id_value = request.form.get('unique_id', '').strip()
        if not id_value:
            flash('ID cannot be empty', 'error')
            return redirect(url_for('index'))

        # Read existing IDs
        with open(DATA_FILE, newline='') as f:
            reader = csv.DictReader(f)
            existing = {row['id'] for row in reader}

        if id_value in existing:
            flash(f"ID '{id_value}' already exists.", 'error')
            return redirect(url_for('index'))

        # Generate QR
        qr = qrcode.make(id_value)
        qr_filename = f"{id_value}.png"
        qr_path = os.path.join(QR_FOLDER, qr_filename)
        qr.save(qr_path)

        # Append to CSV
        with open(DATA_FILE, 'a', newline='') as f:
            writer = csv.writer(f)
            writer.writerow([id_value, qr_path])

        flash(f"ID '{id_value}' saved and QR code created.", 'success')
        return redirect(url_for('index'))

    return render_template('index.html')


if __name__ == '__main__':
    app.run(debug=True)