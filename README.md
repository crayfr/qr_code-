# Minimal Flask QR Code Generator

A simple Flask web app to:

- Input unique IDs.
- Store **hashed IDs** securely in a CSV file (GDPR-friendly).
- Generate and display a QR code for each unique ID.
- Prevent duplicate IDs.
- Reset (erase) the database and QR codes through a hidden reset page.

---

## Features

- Modern and clean UI.
- SHA-256 hashing of IDs.
- QR codes saved and served from \`static/qr_codes\`.
- Duplicate ID detection with friendly messages.
- Secure reset at \`/reset\` route with confirmation.

---

## Setup

1. (Optional) Create and activate a virtual environment:

\`\`\`bash
python -m venv venv
source venv/bin/activate  # macOS/Linux
venv\Scripts\activate     # Windows
\`\`\`

2. Install dependencies:

\`\`\`bash
pip install Flask qrcode[pil]
\`\`\`

---

## Run

\`\`\`bash
python app.py
\`\`\`

Go to [http://127.0.0.1:5000/](http://127.0.0.1:5000/) to use.

To reset all data, visit [http://127.0.0.1:5000/reset](http://127.0.0.1:5000/reset).

---

## Project structure

\`\`\`
qr_app/
├── app.py
├── data.csv
├── qr_codes/
├── templates/
│   ├── index.html
│   └── reset.html
└── static/
    └── qr_codes/
\`\`\`

---

## Notes

- Replace \`app.secret_key\` in \`app.py\` with a secure key before deploying.
- The reset page deletes all QR codes and data.
- Designed with simplicity and bug-resistance (KISS).