from flask import Flask, request, redirect, url_for, render_template, flash, session, send_file, make_response
import sqlite3
import pandas as pd
from datetime import datetime
import os
from Crypto.Cipher import AES
from base64 import b64encode
import hashlib
from Crypto.Util.Padding import pad
from io import BytesIO
from xhtml2pdf import pisa  # install using: pip install xhtml2pdf
from connection import groq_client  # Import groq client

app = Flask(__name__)
app.secret_key = 'prevanalyzer_123'

DB_PATH = 'data.db'
UPLOAD_FOLDER = 'uploads'
os.makedirs(UPLOAD_FOLDER, exist_ok=True)
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER

# --- DB Connection ---
def get_db_connection():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn

# --- Protection Functions ---
# --- Protection Functions ---

def mask(value):
    value = str(value)
    if len(value) <= 2:
        return '*' * len(value)
    elif '@' in value:
        # For email-like data
        local, domain = value.split('@')
        masked_local = local[0] + '*' * (len(local) - 2) + local[-1]
        return masked_local + '@' + domain
    else:
        return value[0] + '*' * (len(value) - 2) + value[-1]

cipher_key = b'Sixteen byte key'  # AES key must be 16 bytes

def encrypt(value):
    try:
        cipher = AES.new(cipher_key, AES.MODE_ECB)
        padded = pad(value.encode(), AES.block_size)
        encrypted = cipher.encrypt(padded)
        return b64encode(encrypted).decode('utf-8')
    except Exception as e:
        print(f"[Encryption Error] Value: {value} | Error: {e}")
        return "ENCRYPTION_ERROR"

def hash_value(value):
    return hashlib.sha256(value.encode()).hexdigest()

# Simulated tokenization using token vault dictionary
_token_vault = {}
def tokenize(value):
    if value not in _token_vault:
        _token_vault[value] = f"TOKEN_{len(_token_vault) + 1:05d}"
    return _token_vault[value]

# Mapping
protection_map = {
    'masking': mask,
    'encryption': encrypt,
    'hashing': hash_value,
    'tokenization': tokenize,
    'none': lambda x: x
}

# --- Home ---
@app.route("/")
def index():
    return render_template('index.html',
                           columns=session.get('columns'),
                           filename=session.get('filename'))

# --- Upload ---
@app.route('/upload', methods=['POST'])
def upload_file():
    file = request.files.get('file')
    if file:
        filename = file.filename
        filepath = os.path.join(app.config['UPLOAD_FOLDER'], filename)
        file.save(filepath)

        # Save to DB
        conn = get_db_connection()
        conn.execute("INSERT INTO uploads (filename, upload_time) VALUES (?, ?)", (filename, datetime.now().isoformat()))
        conn.commit()
        conn.close()

        df = pd.read_csv(filepath) if filename.endswith('.csv') else pd.read_excel(filepath)
        session['columns'] = list(df.columns)
        session['filename'] = filename

        flash("✅ File uploaded successfully!", "success")
        return redirect(url_for("index"))
    
    flash("⚠️ No file uploaded.", "danger")
    return redirect(url_for("index"))

# --- Apply Protection ---
@app.route('/apply_protection', methods=['POST'])
def apply_protection():
    filename = request.form.get('filename')
    filepath = os.path.join(app.config['UPLOAD_FOLDER'], filename)

    if not filename or not os.path.exists(filepath):
        flash("⚠️ File not found.", "danger")
        return redirect(url_for('index'))

    # Load file
    df = pd.read_csv(filepath) if filename.endswith('.csv') else pd.read_excel(filepath)

    # Get selected protection methods
    selected_techniques = {
        col: request.form.get(f'protection_{col}', 'none')
        for col in df.columns
    }

    print("Selected techniques:", selected_techniques)

    # Apply protection
    for col in df.columns:
        method = selected_techniques[col]
        df[col] = df[col].astype(str).apply(protection_map.get(method, lambda x: x))

    print("Protected DataFrame:", df.head()) 

     # Save to session
    session['protected_data'] = df.to_json()  # MUST be saved here
    session['columns'] = list(df.columns)
    session['filename'] = filename

    # Save all data to session (optional, though large datasets might be risky)
    session['protected_data'] = df.to_json()

    # Convert all rows to dictionary
    all_data = df.to_dict(orient='records')

    # Save the protected file
    protected_filepath = os.path.join(app.config['UPLOAD_FOLDER'], f'protected_{filename}')
    df.to_csv(protected_filepath, index=False)
    session['protected_filepath'] = protected_filepath  # store in session

    flash("✅ Protection applied!", "success")
    return render_template("index.html",
                        protected_preview=all_data,
                        show_all_button=False,
                        columns=session.get('columns'),
                        filename=session.get('filename'))

# --- Show All Rows ---
@app.route('/show_all_rows')
def show_all_rows():
    if 'protected_data' not in session:
        flash("⚠️ No processed data found to display.", "warning")
        return redirect(url_for("index"))

    df = pd.read_json(session['protected_data'])
    all_data = df.to_dict(orient='records')

    print("SESSION IN SHOW_ALL_ROWS:", session.get('protected_data'))

    return render_template('index.html',
                           protected_preview=all_data,
                           show_all_button=False,
                           columns=session.get('columns'),
                           filename=session.get('filename'))

@app.route('/download_protected')
def download_protected():
    if 'protected_data' not in session:
        flash("⚠️ No protected data to download.", "warning")
        return redirect(url_for('index'))

    df = pd.read_json(session['protected_data'])
    html = render_template("pdf_template.html", data=df.to_dict(orient='records'))

    # Generate PDF
    result = BytesIO()
    pdf = pisa.pisaDocument(BytesIO(html.encode("UTF-8")), result)

    if not pdf.err:
        response = make_response(result.getvalue())
        response.headers['Content-Type'] = 'application/pdf'
        response.headers['Content-Disposition'] = 'attachment; filename=protected_data.pdf'
        session['downloaded'] = True  # flag for flash message
        return response
    else:
        flash("❌ Failed to generate PDF.", "danger")
        return redirect(url_for('index'))
    
@app.route('/chat', methods=['POST'])
def chat():
    user_question = request.json.get("message", "")
    
    if 'protected_data' not in session:
        return {"answer": "⚠️ No data available. Please upload and protect a file first."}

    df = pd.read_json(session['protected_data'])
    preview_data = df.head(20).to_string(index=False)

    prompt = f"""You are a data assistant. Based on this data:

{preview_data}

Answer the following question:
{user_question}
"""

    try:
        chat_response = groq_client.chat.completions.create(
            messages=[{"role": "user", "content": prompt}],
            model="llama3-8b-8192"
        )

        response_text = chat_response.choices[0].message.content
        return {"answer": response_text}

    except Exception as e:
        print("[❌ Groq API Error]", e)  # 👈 Add this to see the real error
        return {"answer": "❌ Sorry, something went wrong while contacting the chatbot."}


# --- Main ---
if __name__ == "__main__":
    app.run(debug=True)
