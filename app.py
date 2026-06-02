from dotenv import load_dotenv
load_dotenv()
from flask import Flask, render_template, jsonify, request
import os
import base64
import time
from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build
from groq import Groq
from email.mime.text import MIMEText

app = Flask(__name__)

SCOPES = ['https://www.googleapis.com/auth/gmail.modify']
GROQ_API_KEY = os.getenv("GROQ_API_KEY")
CATEGORIES = ["LinkedIn", "IEEE", "ChatGPT", "Jobs", "Promotions", "Spam", "Newsletter", "Other"]

groq_client = Groq(api_key=GROQ_API_KEY)

def get_gmail_service():
    creds = None
    if os.path.exists('token.json'):
        creds = Credentials.from_authorized_user_file('token.json', SCOPES)
    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            creds.refresh(Request())
        else:
            flow = InstalledAppFlow.from_client_secrets_file('credentials.json', SCOPES)
            creds = flow.run_local_server(port=0)
        with open('token.json', 'w') as token:
            token.write(creds.to_json())
    return build('gmail', 'v1', credentials=creds)

def ai_call(prompt, max_tokens=200):
    response = groq_client.chat.completions.create(
        model="llama-3.3-70b-versatile",
        messages=[{"role": "user", "content": prompt}],
        max_tokens=max_tokens
    )
    return response.choices[0].message.content.strip()

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/api/emails')
def get_emails():
    service = get_gmail_service()
    results = service.users().messages().list(userId='me', labelIds=['INBOX'], q='is:unread', maxResults=30).execute()
    messages = results.get('messages', [])
    
    emails = []
    for msg in messages:
        m = service.users().messages().get(userId='me', id=msg['id'], format='full').execute()
        headers = m['payload']['headers']
        subject = next((h['value'] for h in headers if h['name'] == 'Subject'), 'No Subject')
        sender = next((h['value'] for h in headers if h['name'] == 'From'), 'Unknown')
        snippet = m.get('snippet', '')
        
        category = ai_call(f"""Categorize this email into exactly one of: {', '.join(CATEGORIES)}
From: {sender}
Subject: {subject}
Preview: {snippet}
Reply with ONLY the category name.""", max_tokens=10)
        
        if category not in CATEGORIES:
            category = "Other"
            
        emails.append({
            'id': msg['id'],
            'subject': subject,
            'sender': sender,
            'snippet': snippet,
            'category': category
        })
        time.sleep(2.5)
    
    return jsonify(emails)

@app.route('/api/summary/<msg_id>')
def get_summary(msg_id):
    service = get_gmail_service()
    m = service.users().messages().get(userId='me', id=msg_id, format='full').execute()
    headers = m['payload']['headers']
    subject = next((h['value'] for h in headers if h['name'] == 'Subject'), '')
    sender = next((h['value'] for h in headers if h['name'] == 'From'), '')
    snippet = m.get('snippet', '')
    
    summary = ai_call(f"""Summarize this email in 2-3 sentences clearly:
From: {sender}
Subject: {subject}
Content: {snippet}""")
    
    return jsonify({'summary': summary})

@app.route('/api/reply/<msg_id>')
def draft_reply(msg_id):
    service = get_gmail_service()
    m = service.users().messages().get(userId='me', id=msg_id, format='full').execute()
    headers = m['payload']['headers']
    subject = next((h['value'] for h in headers if h['name'] == 'Subject'), '')
    sender = next((h['value'] for h in headers if h['name'] == 'From'), '')
    snippet = m.get('snippet', '')
    
    reply = ai_call(f"""Draft a short professional reply to this email:
From: {sender}
Subject: {subject}
Content: {snippet}

Write only the reply body, no subject line.""", max_tokens=300)
    
    return jsonify({'reply': reply})

@app.route('/api/delete/<msg_id>', methods=['DELETE'])
def delete_email(msg_id):
    service = get_gmail_service()
    service.users().messages().trash(userId='me', id=msg_id).execute()
    return jsonify({'status': 'deleted'})

@app.route('/api/archive/<msg_id>', methods=['POST'])
def archive_email(msg_id):
    service = get_gmail_service()
    service.users().messages().modify(userId='me', id=msg_id, body={'removeLabelIds': ['INBOX']}).execute()
    return jsonify({'status': 'archived'})

@app.route('/api/label/<msg_id>', methods=['POST'])
def apply_label(msg_id):
    service = get_gmail_service()
    category = request.json.get('category')
    labels = service.users().labels().list(userId='me').execute().get('labels', [])
    label_id = None
    for label in labels:
        if label['name'] == f"AI/{category}":
            label_id = label['id']
            break
    if not label_id:
        new_label = service.users().labels().create(userId='me', body={'name': f"AI/{category}"}).execute()
        label_id = new_label['id']
    service.users().messages().modify(userId='me', id=msg_id, body={'addLabelIds': [label_id]}).execute()
    return jsonify({'status': 'labelled'})

if __name__ == '__main__':
    app.run(debug=True)