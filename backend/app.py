from flask import Flask, request, jsonify
from flask_cors import CORS
import smtplib
from email.message import EmailMessage
import os
from reportlab.pdfgen import canvas
from reportlab.lib.pagesizes import letter
from PyPDF2 import PdfReader, PdfWriter
import io
import random
import tempfile
import datetime
import json

app = Flask(__name__)
CORS(app)

# Configure your Gmail credentials here
GMAIL_USER = 'yasindevelopment10@gmail.com'
GMAIL_PASS = 'rntztglyeoilklil'

# Map quote values to PDF filenames
QUOTE_TO_PDF = {
    '1.09': "P/1.Proposal -1.09KWp -ver 4-Apr'25.pdf",
    '1.64': "P/2..Proposal-1.635wp-Ver4-Apr'25.pdf",
    '2.18': "P/3.Proposal-2.18wp-Ver4-Apr'25.pdf",
    '2.27': "P/4.Proposal-2.725wp-ver 4-Apr'25.pdf",
    '3.37': "P/5.Proposal -3.27KWp -ver4-Apr'25.pdf"
}

@app.route('/send-quote', methods=['POST'])
def send_quote():
    data = request.get_json()
    if not data:
        return jsonify({'error': 'Invalid or missing JSON in request'}), 400

    name = data.get('name')
    mobile = data.get('mobile')
    email = data.get('email')
    city = data.get('city')
    pincode = data.get('pincode')
    quote = data.get('quote')
    date = data.get('date')

    pdf_path = QUOTE_TO_PDF.get(quote)
    if not pdf_path or not os.path.exists(pdf_path):
        return jsonify({'error': 'Invalid quote or PDF not found'}), 400

    # Parse date for ref number
    try:
        dt = datetime.datetime.strptime(date, '%Y-%m-%d')
        yy = dt.strftime('%y')
        mm = dt.strftime('%m')
        dd = dt.strftime('%d')
    except Exception:
        return jsonify({'error': 'Invalid date format'}), 400
    rand5 = str(random.randint(10000, 99999))
    ref_number_str = f"Ref No. ARR/SLS/PPSL/{rand5}/{yy}{dd}{mm}-001"

    # Read original PDF
    with open(pdf_path, 'rb') as f:
        original_pdf = PdfReader(f)
        first_page = original_pdf.pages[0]
        packet = io.BytesIO()
        can = canvas.Canvas(packet, pagesize=letter)
        # White out old reference number area
        can.setFillColorRGB(1, 1, 1)  # White
        can.rect(45, 760, 350, 18, fill=1, stroke=0)  # Adjust width/height as needed
        # White out old address block area
        can.rect(45, 710, 350, 55, fill=1, stroke=0)  # Adjust width/height as needed
        # White out old date value area (after colon, top right)
        can.rect(470, 760, 80, 18, fill=1, stroke=0)  # Adjust position/size as needed
        can.setFillColorRGB(0, 0, 0)  # Reset to black
        # Overlay reference number (top, bold)
        can.setFont("Helvetica-Bold", 12)
        can.drawString(50, 765, ref_number_str)
        # Overlay address block (To section)
        can.setFont("Helvetica", 11)
        can.drawString(50, 730, "To")
        can.setFont("Helvetica-Bold", 11)
        can.drawString(50, 715, f"Mr.{name}")
        can.drawString(50, 700, f"{city}, {pincode}")
        can.drawString(50, 685, f"Mobile: {mobile}")
        # Overlay date value (top right, after colon, bold)
        can.setFont("Helvetica-Bold", 12)
        can.drawString(480, 765, date)
        can.save()
        packet.seek(0)
        overlay_pdf = PdfReader(packet)
        overlay_page = overlay_pdf.pages[0]
        first_page.merge_page(overlay_page)
        writer = PdfWriter()
        writer.add_page(first_page)
        for page in original_pdf.pages[1:]:
            writer.add_page(page)
        temp_filename = os.path.join(tempfile.gettempdir(), f"quote_{random.randint(1000,9999)}.pdf")
        with open(temp_filename, 'wb') as out_f:
            writer.write(out_f)

    # Compose email
    msg = EmailMessage()
    msg['Subject'] = f'New Solar Quote Request: {quote} kWp'
    msg['From'] = GMAIL_USER
    msg['To'] = email
    msg.set_content(f"""
Name: {name}
Mobile: {mobile}
Email: {email}
City: {city}
Pincode: {pincode}
Quote: {quote}
Date: {date}
Reference Number: {ref_number_str}
""")

    # Attach modified PDF
    with open(temp_filename, 'rb') as f:
        file_data = f.read()
        file_name = os.path.basename(pdf_path).replace('.pdf', f'-{ref_number_str}.pdf')
    msg.add_attachment(file_data, maintype='application', subtype='pdf', filename=file_name)

    # Send email
    try:
        with smtplib.SMTP_SSL('smtp.gmail.com', 465) as smtp:
            smtp.login(GMAIL_USER, GMAIL_PASS)
            smtp.send_message(msg)
        os.remove(temp_filename)
        # Save submission to text file
        submission_record = {
            'name': name,
            'mobile': mobile,
            'email': email,
            'city': city,
            'pincode': pincode,
            'quote': quote,
            'date': date,
            'ref_number': ref_number_str
        }
        with open('submissions.txt', 'a', encoding='utf-8') as subfile:
            subfile.write(json.dumps(submission_record) + '\n')
        return jsonify({'message': 'Email sent successfully'})
    except Exception as e:
        os.remove(temp_filename)
        return jsonify({'error': str(e)}), 500

@app.route('/submissions', methods=['GET'])
def get_submissions():
    submissions = []
    if os.path.exists('submissions.txt'):
        with open('submissions.txt', 'r', encoding='utf-8') as subfile:
            for line in subfile:
                try:
                    submissions.append(json.loads(line.strip()))
                except Exception:
                    continue
    return jsonify(submissions)

@app.route('/submissions/<ref_number>', methods=['PUT'])
def update_submission(ref_number):
    data = request.get_json()
    if not data:
        return jsonify({'error': 'Invalid or missing JSON in request'}), 400
    updated = False
    new_lines = []
    if os.path.exists('submissions.txt'):
        with open('submissions.txt', 'r', encoding='utf-8') as subfile:
            for line in subfile:
                try:
                    record = json.loads(line.strip())
                    if record.get('ref_number') == ref_number:
                        record.update(data)
                        updated = True
                    new_lines.append(json.dumps(record))
                except Exception:
                    continue
        with open('submissions.txt', 'w', encoding='utf-8') as subfile:
            for l in new_lines:
                subfile.write(l + '\n')
    if updated:
        return jsonify({'message': 'Submission updated'})
    else:
        return jsonify({'error': 'Submission not found'}), 404

@app.route('/submissions/<ref_number>', methods=['DELETE'])
def delete_submission(ref_number):
    deleted = False
    new_lines = []
    if os.path.exists('submissions.txt'):
        with open('submissions.txt', 'r', encoding='utf-8') as subfile:
            for line in subfile:
                try:
                    record = json.loads(line.strip())
                    if record.get('ref_number') == ref_number:
                        deleted = True
                        continue
                    new_lines.append(json.dumps(record))
                except Exception:
                    continue
        with open('submissions.txt', 'w', encoding='utf-8') as subfile:
            for l in new_lines:
                subfile.write(l + '\n')
    if deleted:
        return jsonify({'message': 'Submission deleted'})
    else:
        return jsonify({'error': 'Submission not found'}), 404

if __name__ == '__main__':
    app.run(debug=True)
