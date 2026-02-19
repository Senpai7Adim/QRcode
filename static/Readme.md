# QR Code Generator

Simple Flask app to generate QR codes with:
- Custom foreground/background colors
- Optional center logo
- QR history saved locally
- Live preview with JavaScript

## Installation
- git clone
- cd qrApp
- pip install -r requirements.txt
python app.py

Open in browser:
http://127.0.0.1:5000/

## Project Structure

qrApp/
│── app.py
│── requirements.txt
│── static/
│   ├── style.css
│   ├── script.js
│   └── qrcodes/
│── templates/
│   └── index.html

## Technologies

Flask, Pillow, qrcode, HTML, CSS, JavaScript
