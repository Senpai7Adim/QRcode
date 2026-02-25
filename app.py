from flask import Flask, render_template, request, send_file
from flask_sqlalchemy import SQLAlchemy
from PIL import Image
import qrcode
import qrcode.constants
import os
from datetime import datetime
from pathlib import Path
import tempfile

# -------------------------
# App Initialization
# -------------------------

app = Flask(__name__)

# -------------------------
# Database Configuration
# -------------------------

# -------------------------
# Database Paths (Safe Mode)
# -------------------------

BASE_DIR = Path(__file__).resolve().parent

if os.environ.get("VERCEL_ENV"):
    db_path = Path("/tmp/qrcodes.db")
    qr_codes_path = Path("/tmp/static/qrcodes")
else:
    db_folder = BASE_DIR / "instance"
    qr_codes_path = BASE_DIR / "static/qrcodes"

    # Create folders safely
    db_folder.mkdir(parents=True, exist_ok=True)
    qr_codes_path.mkdir(parents=True, exist_ok=True)

    db_path = db_folder / "qrcodes.db"

# Ensure QR storage directory exists
qr_codes_path.mkdir(parents=True, exist_ok=True)

# SQLAlchemy config
app.config["SQLALCHEMY_DATABASE_URI"] = f"sqlite:///{db_path}"
app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False

db = SQLAlchemy(app)

# -------------------------
# Database Model
# -------------------------

class QRCodeModel(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    data = db.Column(db.Text, nullable=False)
    filename = db.Column(db.String(200), nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

# Create database tables
with app.app_context():
    db.create_all()

# -------------------------
# Routes
# -------------------------

@app.route("/", methods=["GET", "POST"])
def index():
    qr_filename = None

    if request.method == "POST":
        data = request.form.get("data")
        fg_color = request.form.get("fg_color") or "#000000"
        bg_color = request.form.get("bg_color") or "#ffffff"
        logo_file = request.files.get("logo")

        if data:
            # Generate filename
            filename = f"qr_{datetime.now().strftime('%Y%m%d%H%M%S')}.png"
            filepath = qr_codes_path / filename

            # Create QR code
            qr = qrcode.QRCode(
                version=1,
                error_correction=qrcode.constants.ERROR_CORRECT_H,
                box_size=10,
                border=4,
            )

            qr.add_data(data)
            qr.make(fit=True)

            img = qr.make_image(
                fill_color=fg_color,
                back_color=bg_color
            ).convert("RGB")

            # Add logo if provided
            if logo_file and logo_file.filename != "":
                with tempfile.NamedTemporaryFile(delete=False, suffix=".png") as tmp_logo:
                    logo_file.save(tmp_logo.name)

                    logo = Image.open(tmp_logo.name)

                    img_w, img_h = img.size
                    size = img_w // 4

                    logo = logo.resize((size, size))

                    pos = ((img_w - size) // 2, (img_h - size) // 2)

                    if logo.mode == "RGBA":
                        img.paste(logo, pos, mask=logo)
                    else:
                        img.paste(logo, pos)

                    os.unlink(tmp_logo.name)

            img.save(filepath)

            # Save to database
            new_qr = QRCodeModel(
                data=data,
                filename=filename
            )

            db.session.add(new_qr)
            db.session.commit()

            qr_filename = filename

    all_qrcodes = QRCodeModel.query.order_by(
        QRCodeModel.created_at.desc()
    ).all()

    return render_template(
        "index.html",
        qr_filename=qr_filename,
        all_qrcodes=all_qrcodes
    )

# -------------------------
# Download Route
# -------------------------

@app.route("/download/<filename>")
def download(filename):
    file_path = qr_codes_path / filename
    return send_file(file_path, as_attachment=True)

# -------------------------
# Run Locally
# -------------------------

if __name__ == "__main__":
    app.run(debug=True)