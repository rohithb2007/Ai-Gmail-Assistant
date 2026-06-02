import os
import base64
from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build
from groq import Groq

SCOPES = ['https://www.googleapis.com/auth/gmail.modify']
GROQ_API_KEY = "your_groq_api_key_here"

CATEGORIES = ["LinkedIn", "IEEE", "ChatGPT", "Jobs", "Promotions", "Spam", "Newsletter", "Other"]

def authenticate():
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

def get_emails(service, max_emails=20):
    results = service.users().messages().list(userId='me', labelIds=['INBOX'], q='is:unread', maxResults=max_emails).execute()
    return results.get('messages', [])

def get_email_content(service, msg_id):
    msg = service.users().messages().get(userId='me', id=msg_id, format='full').execute()
    headers = msg['payload']['headers']
    subject = next((h['value'] for h in headers if h['name'] == 'Subject'), 'No Subject')
    sender = next((h['value'] for h in headers if h['name'] == 'From'), 'Unknown')
    snippet = msg.get('snippet', '')
    return subject, sender, snippet

def categorize_email(subject, sender, snippet):
    client = Groq(api_key=GROQ_API_KEY)
    prompt = f"""Categorize this email into exactly one of these categories: {', '.join(CATEGORIES)}

From: {sender}
Subject: {subject}
Preview: {snippet}

Reply with ONLY the category name, nothing else."""
    
    response = client.chat.completions.create(
        model="llama-3.3-70b-versatile",
        messages=[{"role": "user", "content": prompt}],
        max_tokens=10
    )
    category = response.choices[0].message.content.strip()
    if category not in CATEGORIES:
        category = "Other"
    return category

def get_or_create_label(service, label_name):
    labels = service.users().labels().list(userId='me').execute().get('labels', [])
    for label in labels:
        if label['name'] == label_name:
            return label['id']
    new_label = service.users().labels().create(userId='me', body={'name': label_name}).execute()
    return new_label['id']

def apply_label(service, msg_id, label_id):
    service.users().messages().modify(userId='me', id=msg_id, body={'addLabelIds': [label_id]}).execute()

def main():
    print("🔐 Authenticating with Gmail...")
    service = authenticate()
    print("✅ Connected to Gmail!\n")
    
    print("📬 Fetching unread emails...")
    messages = get_emails(service)
    print(f"Found {len(messages)} unread emails\n")
    
    for msg in messages:
        subject, sender, snippet = get_email_content(service, msg['id'])
        category = categorize_email(subject, sender, snippet)
        label_id = get_or_create_label(service, f"AI/{category}")
        apply_label(service, msg['id'], label_id)
        print(f"✅ [{category}] {subject[:60]} | From: {sender[:40]}")
    
    print("\n🎉 Done! Check your Gmail for the new labels.")

if __name__ == '__main__':
    main()