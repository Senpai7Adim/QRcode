from flask import Flask, render_template, request, send_file
from flask_sqlalchemy import SQLAlchemy
from PIL import Image
import qrcode
import os
from datetime import datetime

app = Flask(__name__)

# --- Database setup ---
app.config["SQLALCHEMY_DATABASE_URI"] = "sqlite:///qrcodes.db"
app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False
db = SQLAlchemy(app)

# --- Model ---
class QRCodeModel(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    data = db.Column(db.Text, nullable=False)
    filename = db.Column(db.String(200), nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

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
            filepath = os.path.join("static/qrcodes/", filename)

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
                logo_path = os.path.join("static/qrcodes/", f"logo_{filename}")
                logo_file.save(logo_path)

                logo = Image.open(logo_path)
                img_w, img_h = img.size
                factor = 4
                size = img_w // factor
                logo = logo.resize((size, size))

                pos = ((img_w - size) // 2, (img_h - size) // 2)
                if logo.mode == "RGBA":
                    img.paste(logo, pos, mask=logo)
                else:
                    img.paste(logo, pos)

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
    path = os.path.join("static/qrcodes", filename)
    return send_file(path, as_attachment=True)

# --- Run app ---
if __name__ == "__main__":
    os.makedirs("static/qrcodes", exist_ok=True)
    with app.app_context():
        db.create_all()
    app.run(debug=True)
