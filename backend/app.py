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

    try:
        dt = datetime.datetime.strptime(date, '%Y-%m-%d')
        yy = dt.strftime('%y')
        mm = dt.strftime('%m')
        dd = dt.strftime('%d')
        formatted_date = dt.strftime('%d-%m-%Y')
    except Exception:
        return jsonify({'error': 'Invalid date format'}), 400

    rand5 = str(random.randint(10000, 99999))
    ref_number_str = f"Ref No. ARR/SLS/PPSL/{rand5}/{yy}{mm}{dd}-001"

    # Modify PDF using PyMuPDF
    doc = fitz.open(pdf_path)
    page = doc[0]
    replacements = {
        "Ref No. ARR/SLS/PPSL/XXXXX/YYDDMM-001": ref_number_str,
        "Date: DD-MM-YYYY": f"Date: {formatted_date}",
        "Mr.XXXXXXXXXXXXXXX\nXXXXXXXXXXXXXXXXX": f"Mr.{name}\n{city}, {pincode}",
        "Mobile: XXXXXXXXXX": f"Mobile: {mobile}"
    }

    for old_text, new_text in replacements.items():
        areas = page.search_for(old_text)
        if not areas:
            print(f"[WARNING] Text not found: '{old_text}'")
            continue
        # Redact first
        for area in areas:
            page.add_redact_annot(area, fill=(1, 1, 1))
        page.apply_redactions()
        # Then insert new text
        for area in areas:
            page.insert_text((area.x0, area.y1 - 1), new_text, fontname="helv", fontsize=11, fill=(0, 0, 0))

    temp_filename = os.path.join(tempfile.gettempdir(), f"quote_{random.randint(1000,9999)}.pdf")
    doc.save(temp_filename)
    doc.close()

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

    with open(temp_filename, 'rb') as f:
        file_data = f.read()
        file_name = os.path.basename(pdf_path).replace('.pdf', f'-{ref_number_str}.pdf')
    msg.add_attachment(file_data, maintype='application', subtype='pdf', filename=file_name)

    try:
        with smtplib.SMTP_SSL('smtp.gmail.com', 465) as smtp:
            smtp.login(GMAIL_USER, GMAIL_PASS)
            smtp.send_message(msg)
        os.remove(temp_filename)

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
