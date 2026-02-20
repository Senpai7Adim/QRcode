from flask import Flask, render_template, request, send_file
from flask_sqlalchemy import SQLAlchemy
from PIL import Image
import qrcode
import qrcode.constants
import os
from datetime import datetime
import tempfile
import shutil
from pathlib import Path

app = Flask(__name__)

# Use /tmp for database in Vercel (writable directory)
if os.environ.get('VERCEL_ENV'):
    # Production on Vercel
    db_path = Path('/tmp') / 'qrcodes.db'
    qr_codes_path = Path('/tmp') / 'static' / 'qrcodes'
else:
    # Local development
    db_path = Path('instance') / 'qrcodes.db'
    qr_codes_path = Path('static') / 'qrcodes'

# Ensure directories exist
qr_codes_path.mkdir(parents=True, exist_ok=True)

# Database configuration
app.config["SQLALCHEMY_DATABASE_URI"] = f"sqlite:///{db_path}"
app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False
db = SQLAlchemy(app)

# --- Model ---
class QRCodeModel(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    data = db.Column(db.Text, nullable=False)
    filename = db.Column(db.String(200), nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

# Create tables
with app.app_context():
    db.create_all()

# --- Routes ---
@app.route("/", methods=["GET", "POST"])
def index():
    qr_filename = None

    if request.method == "POST":
        data = request.form.get("data")
        fg_color = request.form.get("fg_color") or "#000000"
        bg_color = request.form.get("bg_color") or "#ffffff"
        logo_file = request.files.get("logo")

        if data:
            filename = f"qr_{datetime.now().strftime('%Y%m%d%H%M%S')}.png"
            filepath = qr_codes_path / filename

            # Generate QR code
            qr = qrcode.QRCode(
                version=1,
                error_correction=qrcode.constants.ERROR_CORRECT_H,
                box_size=10,
                border=4,
            )
            qr.add_data(data)
            qr.make(fit=True)

            img = qr.make_image(fill_color=fg_color, back_color=bg_color).convert("RGB")

            # Add logo in center if provided
            if logo_file and logo_file.filename != "":
                # Save logo temporarily
                with tempfile.NamedTemporaryFile(delete=False, suffix='.png') as tmp_logo:
                    logo_file.save(tmp_logo.name)
                    logo = Image.open(tmp_logo.name)
                    
                    img_w, img_h = img.size
                    factor = 4
                    size = img_w // factor
                    logo = logo.resize((size, size))

                    pos = ((img_w - size) // 2, (img_h - size) // 2)
                    if logo.mode == "RGBA":
                        img.paste(logo, pos, mask=logo)
                    else:
                        img.paste(logo, pos)
                    
                    # Clean up temp file
                    os.unlink(tmp_logo.name)

            img.save(filepath)

            # Save to database
            new_qr = QRCodeModel(data=data, filename=filename)
            db.session.add(new_qr)
            db.session.commit()

            qr_filename = filename

    all_qrcodes = QRCodeModel.query.order_by(QRCodeModel.created_at.desc()).all()
    return render_template("index.html", qr_filename=qr_filename, all_qrcodes=all_qrcodes)

@app.route("/download/<filename>")
def download(filename):
    file_path = qr_codes_path / filename
    return send_file(file_path, as_attachment=True)

# Vercel handler
def handler(request):
    return app(request)

# --- Run app ---
if __name__ == "__main__":
    app.run(debug=True)