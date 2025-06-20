# Solar Quote App

A web application to collect user information and send a solar quote PDF via email based on the selected quote.

## Features
- Beautiful React form UI (Material-UI)
- Collects: Name, Mobile Number, Email, City, Pincode, Quote
- Sends an email with the correct PDF attached (from the `P/` folder) using Gmail

---

## Folder Structure
```
Solar Page/
  backend/        # Flask backend
    app.py
    requirements.txt
  frontend/       # React frontend
    src/
      App.js
      index.js
    package.json
  P/              # PDF files (already present)
```

---

## Backend Setup (Python/Flask)

1. **Install dependencies:**
   ```bash
   pip install -r backend/requirements.txt
   ```

2. **Gmail Setup:**
   - Use a Gmail account.
   - Enable 2-Step Verification in your Google Account.
   - Create an "App Password" (Google Account > Security > App Passwords).
   - Replace the placeholders in `backend/app.py`:
     ```python
     GMAIL_USER = 'your_email@gmail.com'
     GMAIL_PASS = 'your_app_password'
     ```

3. **Run the backend:**
   ```bash
   python backend/app.py
   ```
   - The backend will run on `http://localhost:5000`

---

## Frontend Setup (React)

1. **Install dependencies:**
   ```bash
   cd frontend
   npm install
   ```

2. **Start the frontend:**
   ```bash
   npm start
   ```
   - The app will open in your browser (usually at `http://localhost:3000`).

---

## Usage
1. Fill out the form fields.
2. Select a quote.
3. Submit the form.
4. The backend will send an email with the corresponding PDF attached.

---

## Notes
- Make sure the backend can access the `P/` folder and the PDF files are present.
- The backend and frontend must both be running for the app to work.
- If you deploy, update the API endpoint in the frontend accordingly.

---

## Troubleshooting
- **Email not sending?**
  - Double-check your Gmail credentials and app password.
  - Make sure less secure app access is enabled if not using app passwords (not recommended).
  - Check your spam folder.
- **PDF not found?**
  - Ensure the filenames in `backend/app.py` match exactly with those in the `P/` folder.

---

## License
MIT 