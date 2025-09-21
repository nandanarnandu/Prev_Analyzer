from flask import Flask, request, redirect, url_for, render_template, flash, session, send_file, make_response, jsonify
import sqlite3
import pandas as pd
from datetime import datetime
import os
from Crypto.Cipher import AES
from base64 import b64encode
import hashlib
from Crypto.Util.Padding import pad
from io import BytesIO
from xhtml2pdf import pisa
from connection import groq_client  # Import groq client
import chardet
import traceback

app = Flask(__name__)
app.secret_key = 'prevanalyzer_123'

DB_PATH = 'data.db'
UPLOAD_FOLDER = 'uploads'
os.makedirs(UPLOAD_FOLDER, exist_ok=True)
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER

# -------------------------
# Database connection
# -------------------------
def get_db_connection():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn

# -------------------------
# Protection Functions
# -------------------------
def mask(value):
    value = str(value)
    if len(value) <= 2:
        return '*' * len(value)
    elif '@' in value:
        local, domain = value.split('@', 1)
        if len(local) <= 2:
            masked_local = '*' * len(local)
        else:
            masked_local = local[0] + '*' * (len(local) - 2) + local[-1]
        return masked_local + '@' + domain
    else:
        return value[0] + '*' * (len(value) - 2) + value[-1]

cipher_key = b'Sixteen byte key'  # AES key must be 16 bytes

def encrypt(value):
    try:
        cipher = AES.new(cipher_key, AES.MODE_ECB)
        padded = pad(str(value).encode('utf-8'), AES.block_size)
        encrypted = cipher.encrypt(padded)
        return b64encode(encrypted).decode('utf-8')
    except Exception as e:
        print(f"[Encryption Error] Value: {value} | Error: {e}")
        return "ENCRYPTION_ERROR"

def hash_value(value):
    return hashlib.sha256(str(value).encode('utf-8')).hexdigest()

# Simulated tokenization
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

# -------------------------
# Routes
# -------------------------
@app.route("/")
def index():
    return render_template('index.html',
                           columns=session.get('columns'),
                           filename=session.get('filename'))

# Upload file
@app.route('/upload', methods=['POST'])
def upload_file():
    file = request.files.get('file')
    if file:
        filename = file.filename
        filepath = os.path.join(app.config['UPLOAD_FOLDER'], filename)
        file.save(filepath)

        # Optional: record upload event (ensure uploads table exists)
        try:
            conn = get_db_connection()
            conn.execute("INSERT INTO uploads (filename, upload_time) VALUES (?, ?)", (filename, datetime.now().isoformat()))
            conn.commit()
            conn.close()
        except Exception:
            # ignore DB errors for uploads table if not present
            pass

        # Read file (CSV or Excel)
        try:
            if filename.lower().endswith('.csv'):
                # detect encoding
                with open(filepath, 'rb') as f:
                    raw = f.read()
                    enc = chardet.detect(raw)
                    encoding = enc.get('encoding') or 'utf-8'
                df = pd.read_csv(filepath, encoding=encoding)
            else:
                df = pd.read_excel(filepath)
        except Exception as e:
            flash(f"⚠️ Failed to read file: {e}", "danger")
            return redirect(url_for("index"))

        session['columns'] = list(df.columns)
        session['filename'] = filename

        flash("✅ File uploaded successfully!", "success")
        return redirect(url_for("index"))

    flash("⚠️ No file uploaded.", "danger")
    return redirect(url_for("index"))

# Apply standard protection
@app.route('/apply_protection', methods=['POST'])
def apply_protection():
    filename = request.form.get('filename')
    filepath = os.path.join(app.config['UPLOAD_FOLDER'], filename)

    if not filename or not os.path.exists(filepath):
        flash("⚠️ File not found.", "danger")
        return redirect(url_for('index'))

    try:
        if filename.lower().endswith('.csv'):
            with open(filepath, 'rb') as f:
                raw = f.read()
                enc = chardet.detect(raw)
                encoding = enc.get('encoding') or 'utf-8'
            df = pd.read_csv(filepath, encoding=encoding)
        else:
            df = pd.read_excel(filepath)
    except Exception as e:
        flash(f"⚠️ Failed to read file: {e}", "danger")
        return redirect(url_for('index'))

    selected_techniques = {
        col: request.form.get(f'protection_{col}', 'none')
        for col in df.columns
    }

    for col in df.columns:
        method = selected_techniques.get(col, 'none')
        try:
            df[col] = df[col].astype(str).apply(protection_map.get(method, lambda x: x))
        except Exception as e:
            # If a column conversion fails, keep original values and continue
            print(f"[Protection Error] column={col} method={method} error={e}")

    # Save protected data in session for preview/chat/download
    session['protected_data'] = df.to_json(orient='records')
    session['columns'] = list(df.columns)
    session['filename'] = filename

    all_data = df.to_dict(orient='records')

    # Save protected file
    protected_filepath = os.path.join(app.config['UPLOAD_FOLDER'], f'protected_{filename}')
    try:
        df.to_csv(protected_filepath, index=False)
        session['protected_filepath'] = protected_filepath
    except Exception as e:
        print(f"[File Save Error] {e}")

    flash("✅ Protection applied!", "success")
    return render_template("index.html",
                           protected_preview=all_data,
                           show_all_button=False,
                           columns=session.get('columns'),
                           filename=session.get('filename'))

# Apply custom code from editor
@app.route("/apply_custom_code", methods=["POST"])
def apply_custom_code():
    try:
        data = request.get_json(force=True)
        custom_code = data.get("code", "").strip()
        filename = data.get("filename", "").strip()

        if not custom_code:
            return jsonify({"success": False, "message": "❌ No custom code provided."})

        if not filename:
            return jsonify({"success": False, "message": "❌ No filename provided."})

        # Ensure safe file path
        file_path = os.path.join(app.config['UPLOAD_FOLDER'], filename)
        if not os.path.isfile(file_path):
            return jsonify({"success": False, "message": "❌ File not found in upload folder."})

        # Read the file based on extension
        if filename.lower().endswith('.csv'):
            with open(file_path, 'rb') as f:
                raw_data = f.read()
                result = chardet.detect(raw_data)
                encoding = result.get("encoding") or "utf-8"
            df = pd.read_csv(file_path, encoding=encoding)
        else:
            df = pd.read_excel(file_path, engine="openpyxl")
            encoding = None  # Excel doesn't require encoding

        # Prepare safe exec environment
        local_vars = {}
        try:
            exec(custom_code, {}, local_vars)
        except Exception as e:
            return jsonify({"success": False, "message": f"❌ Error executing custom code: {e}"})

        if "custom_protection" not in local_vars or not callable(local_vars["custom_protection"]):
            return jsonify({"success": False, "message": "❌ No valid 'custom_protection' function found in custom code."})

        # Apply the custom function
        try:
            df = local_vars["custom_protection"](df)
        except Exception as e:
            return jsonify({"success": False, "message": f"❌ Error while running custom_protection: {e}"})

        # Save processed file
        output_filename = f"processed_{filename}"
        output_path = os.path.join(app.config['UPLOAD_FOLDER'], output_filename)
        if filename.lower().endswith('.csv'):
            df.to_csv(output_path, index=False, encoding=encoding or "utf-8")
        else:
            df.to_excel(output_path, index=False, engine="openpyxl")

        # Save session info
        session['protected_data'] = df.to_json(orient='records')
        session['columns'] = list(df.columns)
        session['filename'] = output_filename
        session['protected_filepath'] = output_path

        # Generate preview table (first 50 rows)
        processed_table = df.head(50).to_html(
            classes="table table-striped table-bordered", 
            index=False, 
            escape=False
        )

        return jsonify({
            "success": True,
            "message": "✅ Custom code applied successfully!",
            "table": processed_table,
            "download_file": output_filename
        })

    except Exception as e:
        return jsonify({"success": False, "message": f"❌ Unexpected error: {str(e)}"})

# Show all rows
@app.route('/show_all_rows')
def show_all_rows():
    if 'protected_data' not in session:
        flash("⚠️ No processed data found to display.", "warning")
        return redirect(url_for("index"))

    # protected_data saved as list-of-dicts JSON (orient='records')
    try:
        df = pd.read_json(session['protected_data'])
    except Exception:
        # fallback: try reading saved protected file
        protected_filepath = session.get('protected_filepath')
        if protected_filepath and os.path.exists(protected_filepath):
            df = pd.read_csv(protected_filepath)
        else:
            flash("⚠️ No processed data available.", "warning")
            return redirect(url_for('index'))

    all_data = df.to_dict(orient='records')

    return render_template('index.html',
                           protected_preview=all_data,
                           show_all_button=False,
                           columns=session.get('columns'),
                           filename=session.get('filename'))

# Download protected data as PDF
@app.route('/download_protected')
def download_protected():
    if 'protected_data' not in session:
        flash("⚠️ No protected data to download.", "warning")
        return redirect(url_for('index'))

    try:
        df = pd.read_json(session['protected_data'])
    except Exception:
        flash("⚠️ Failed to load protected data.", "danger")
        return redirect(url_for('index'))

    html = render_template("pdf_template.html", data=df.to_dict(orient='records'))

    result = BytesIO()
    pdf = pisa.pisaDocument(BytesIO(html.encode("UTF-8")), result)

    if not pdf.err:
        response = make_response(result.getvalue())
        response.headers['Content-Type'] = 'application/pdf'
        response.headers['Content-Disposition'] = 'attachment; filename=protected_data.pdf'
        return response
    else:
        flash("❌ Failed to generate PDF.", "danger")
        return redirect(url_for('index'))

# Chat with Groq AI
@app.route('/chat', methods=['POST'])
def chat():
    user_question = request.json.get("message", "")

    if 'protected_data' not in session:
        return {"answer": "⚠️ No data available. Please upload and protect a file first."}

    try:
        df = pd.read_json(session['protected_data'])
    except Exception:
        return {"answer": "⚠️ Failed to load protected data for chat."}

    preview_data = df.head(20).to_string(index=False)

    prompt = f"""You are a helpful Prevanalyzer data assistant. Use the provided data sample to answer the user's question precisely and concisely.
Data sample:
{preview_data}

User question:
{user_question}
"""

    try:
        chat_response = groq_client.chat.completions.create(
            messages=[{"role": "user", "content": prompt}],
            model="llama3-8b-8192"
        )
        # defensive access
        answer = ""
        try:
            answer = chat_response.choices[0].message.content
        except Exception:
            answer = str(chat_response)

        return {"answer": answer}

    except Exception as e:
        print("[❌ Groq API Error]", e)
        return {"answer": "❌ Sorry, something went wrong while contacting the chatbot."}

# -------------------------
# Main
# -------------------------
if __name__ == "__main__":
    app.run(debug=True)
