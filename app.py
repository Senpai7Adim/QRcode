from flask import Flask, render_template, request, send_file
import qrcode
from PIL import Image
import os
from datetime import datetime
from pathlib import Path
import io

app = Flask(__name__)

# Store QR codes in memory (temporary)
recent_qrcodes = []

@app.route('/', methods=['GET', 'POST'])
def index():
    qr_filename = None
    error = None
    
    try:
        if request.method == 'POST':
            data = request.form.get('data')
            fg_color = request.form.get('fg_color') or '#000000'
            bg_color = request.form.get('bg_color') or '#ffffff'
            logo_file = request.files.get('logo')
            
            if not data:
                error = "Please enter data for the QR code"
            else:
                # Create QR code
                qr = qrcode.QRCode(version=1, box_size=10, border=4)
                qr.add_data(data)
                qr.make(fit=True)
                
                img = qr.make_image(fill_color=fg_color, back_color=bg_color).convert('RGB')
                
                # Add logo if provided
                if logo_file and logo_file.filename:
                    try:
                        logo = Image.open(logo_file)
                        # Resize logo
                        max_size = img.size[0] // 3
                        logo.thumbnail((max_size, max_size))
                        
                        # Calculate position
                        x = (img.size[0] - logo.size[0]) // 2
                        y = (img.size[1] - logo.size[1]) // 2
                        
                        # Paste logo
                        if logo.mode == 'RGBA':
                            img.paste(logo, (x, y), logo)
                        else:
                            img.paste(logo, (x, y))
                    except Exception as e:
                        error = f"Error adding logo: {str(e)}"
                
                # Save to bytes
                img_bytes = io.BytesIO()
                img.save(img_bytes, format='PNG')
                img_bytes.seek(0)
                
                # Generate filename
                filename = f"qr_{datetime.now().strftime('%Y%m%d%H%M%S')}.png"
                
                # Save to /tmp in Vercel
                if os.environ.get('VERCEL_ENV'):
                    save_dir = Path('/tmp/qrcodes')
                else:
                    save_dir = Path('static/qrcodes')
                
                save_dir.mkdir(parents=True, exist_ok=True)
                
                with open(save_dir / filename, 'wb') as f:
                    f.write(img_bytes.getvalue())
                
                # Store in memory
                recent_qrcodes.insert(0, {
                    'data': data[:50] + ('...' if len(data) > 50 else ''),
                    'filename': filename
                })
                
                # Keep only last 10
                if len(recent_qrcodes) > 10:
                    recent_qrcodes.pop()
                
                qr_filename = filename
                
    except Exception as e:
        error = str(e)
        print(f"Error in index route: {e}")
    
    return render_template('index.html', 
                         qr_filename=qr_filename, 
                         all_qrcodes=recent_qrcodes,
                         error=error)

@app.route('/download/<filename>')
def download(filename):
    try:
        if os.environ.get('VERCEL_ENV'):
            file_path = Path('/tmp/qrcodes') / filename
        else:
            file_path = Path('static/qrcodes') / filename
        
        return send_file(file_path, as_attachment=True)
    except Exception as e:
        return f"Error downloading file: {str(e)}", 404

# For local development
if __name__ == '__main__':
    os.makedirs('static/qrcodes', exist_ok=True)
    app.run(debug=True)

# Vercel handler
def handler(request):
    return app(request)