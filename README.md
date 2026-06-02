# 📧 AI Gmail Assistant

An AI-powered Gmail management web app that automatically organizes, summarizes, and helps you reply to emails.

## ✨ Features
- 📂 Auto-categorize emails (LinkedIn, IEEE, ChatGPT, Spam, etc.)
- ✨ AI-generated email summaries
- ✍️ AI draft reply generation
- 📦 Archive emails
- 🗑️ Delete/trash emails

## 🛠️ Tech Stack
- Python, Flask
- Gmail API (OAuth 2.0)
- Groq AI (LLaMA 3.3 70B)
- HTML, CSS, JavaScript
- Google Cloud Console

## 🚀 Setup

### 1. Clone the repo
```bash
git clone https://github.com/rohithb2007/Ai-Gmail-Assistant.git
```

### 2. Install dependencies
```bash
pip install flask google-api-python-client google-auth-httplib2 google-auth-oauthlib groq python-dotenv
```

### 3. Get your Groq API key
- Go to [console.groq.com](https://console.groq.com)
- Create a free account
- Generate an API key

### 4. Create a `.env` file
  -GROQ_API_KEY=your_groq_api_key_here
### 5. Set up Gmail API
- Go to [Google Cloud Console](https://console.cloud.google.com)
- Create a project and enable Gmail API
- Download OAuth credentials as `credentials.json`

### 6. Run the app
```bash
python app.py
```
Open [http://127.0.0.1:5000](http://127.0.0.1:5000)

## ⚠️ Important
Never upload your `.env`, `credentials.json`, or `token.json` files to GitHub!
