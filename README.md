# 🛡️ PREVANALYZER — Data Privacy & Protection Tool

[![Python](https://img.shields.io/badge/python-v3.8+-blue.svg)](https://www.python.org/downloads/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)

> **Prevanalyzer** is a Flask-based **data privacy and protection web application** that allows users to upload datasets, apply privacy-preserving techniques (masking, hashing, encryption, tokenization), and get guidance via an **AI-powered chatbot**. Designed for secure, beginner-friendly data protection.
> 
<img width="1920" height="1080" alt="1" src="https://github.com/user-attachments/assets/20c52b20-37e7-4033-84d2-a504dbe492d0" />
<img width="1920" height="1080" alt="2" src="https://github.com/user-attachments/assets/9acbb119-3386-4598-846b-265d71f14fe8" />
<img width="1920" height="1080" alt="3" src="https://github.com/user-attachments/assets/7011d345-954d-4359-bb43-1a2c159b7e3b" />
<img width="1920" height="1080" alt="4" src="https://github.com/user-attachments/assets/52d34ed5-78b7-44d5-8419-77841f38b8d4" />
<img width="1920" height="1080" alt="5" src="https://github.com/user-attachments/assets/b8672f4f-4c7c-48fa-a8a7-a37fc34d37f7" />
<img width="406" height="372" alt="7" src="https://github.com/user-attachments/assets/c9ce2279-09a3-49f0-a3a9-be1926eb1a8f" />
<img width="1230" height="683" alt="8" src="https://github.com/user-attachments/assets/337c046f-b0e8-43c8-9647-4cdb14965910" />

---

## ✨ Features

- **Secure File Uploads** – CSV, Excel, JSON
- **Data Protection Techniques**
    - Masking (partial data hiding)
    - Hashing (irreversible transformation)
    - Encryption (AES-based)
    - Tokenization (safe value replacement)
- **Column-wise Protection Selection**
- **Custom Python Code Editor** for advanced transformations
- **Protected Data Preview & Download**
- **AI Chatbot Assistance**
    - Privacy tips & guidance
    - Dataset-aware Q&A (powered by Groq LLM)
- **Database Logging**
    - Upload history
    - Applied protection methods
---

## 🚀 Quick Start

```bash
# Clone the repository
git clone https://github.com/YOUR_USERNAME/prevanalyzer.git
cd prevanalyzer

# Create virtual environment
python -m venv venv
# Activate
# Windows
venv\Scripts\activate
# macOS / Linux
source venv/bin/activate

# Install dependencies
pip install -r requirements.txt

# Initialize database
python database.py

# Run the Flask app
python app.py

```

## 📸 Usage

1. Upload a CSV / Excel / JSON file
2. Select protection techniques for each column
3. (Optional) Apply custom Python transformation logic
4. Preview protected data
5. Download processed file or PDF report
6. Ask privacy-related questions via the AI chatbot

## 🛠️ Tech Stack

- Backend: Python, Flask
- Data Processing: Pandas
- Security: AES Encryption, SHA-256 Hashing
- Database: SQLite
- Frontend: HTML, CSS, Bootstrap
- AI Chatbot: Groq API (LLaMA models)

## 📁 Project Structure

prevanalyzer/
│── app.py              # Main Flask application
│── database.py         # SQLite setup
│── connection.py       # Groq chatbot integration
│── templates/          # HTML templates
│── uploads/            # Uploaded & processed files
│── data.db             # SQLite database
│── requirements.txt    # Dependencies
│── .env                # API keys (ignored in Git)
│── .gitignore

## 🎯 Use Cases

- Students learning data privacy & anonymization
- Data analysts securing datasets before analysis
- Organizations protecting sensitive customer data
- General users sharing files safely

## 🎨 Future Enhancements

- User authentication (login/signup)
- Advanced anonymization techniques
- Role-based access control
- Cloud deployment (AWS / GCP)
- Privacy analytics dashboard
  
## 🤝 Contributing

1. Fork the repository
2. Create a feature branch
3. Commit your changes
4. Open a pull request

💡 Contributions, issues, and feature requests are welcome!


---



