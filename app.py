from flask import Flask, render_template, request, jsonify, send_from_directory
import imaplib
import ssl
import os
import email
from email import policy
from email.parser import BytesParser
import re
import datetime
from threading import Thread
import time

app = Flask(__name__)

# Configuration
IMAP_SERVER = "imap.gmail.com"
IMAP_PORT = 993
DOWNLOAD_DIR = "downloaded_attachments"

# Global variable to store progress
progress_data = {
    'status': 'idle',
    'message': '',
    'progress': 0,
    'total': 0,
    'downloads': 0,
    'files': []
}

def sanitize_filename(filename):
    """Removes potentially problematic characters from a filename."""
    return re.sub(r'[^\w\-. ]', '_', filename)

def connect_to_imap(email_address, app_password, imap_server, imap_port):
    """Connects to an IMAP server and logs in."""
    try:
        context = ssl.create_default_context()
        mail = imaplib.IMAP4_SSL(imap_server, imap_port, ssl_context=context)
        mail.login(email_address, app_password)
        return mail
    except imaplib.IMAP4.error as e:
        raise Exception(f"IMAP login failed: {e}")
    except Exception as e:
        raise Exception(f"Connection error: {e}")

def process_emails(email_address, app_password, sender_mail, start_date_str, end_date_str):
    """Process emails and download attachments (runs in background thread)."""
    global progress_data
    
    try:
        progress_data = {
            'status': 'connecting',
            'message': 'Connecting to IMAP server...',
            'progress': 0,
            'total': 0,
            'downloads': 0,
            'files': []
        }
        
        # Connect to IMAP
        mail_connection = connect_to_imap(email_address, app_password, IMAP_SERVER, IMAP_PORT)
        
        progress_data['message'] = 'Connected! Parsing dates...'
        
        # Parse dates
        start_date_obj = datetime.datetime.strptime(start_date_str, '%Y-%m-%d').date()
        end_date_obj = datetime.datetime.strptime(end_date_str, '%Y-%m-%d').date()
        before_date_obj = end_date_obj + datetime.timedelta(days=1)
        
        imap_start_date = start_date_obj.strftime('%d-%b-%Y')
        imap_before_date = before_date_obj.strftime('%d-%b-%Y')
        
        # Select INBOX
        progress_data['message'] = 'Selecting INBOX...'
        status, messages_in_inbox = mail_connection.select("INBOX")
        if status != 'OK':
            raise Exception(f"Failed to select INBOX: {status}")
        
        # Search for emails
        progress_data['message'] = f'Searching for emails from {sender_mail}...'
        search_status, search_data = mail_connection.search(
            None,
            'FROM', f'"{sender_mail}"',
            'SINCE', f'"{imap_start_date}"',
            'BEFORE', f'"{imap_before_date}"'
        )
        
        if search_status != 'OK':
            raise Exception("IMAP search failed")
        
        raw_message_ids_string = search_data[0].decode('utf-8')
        
        if not raw_message_ids_string:
            progress_data['status'] = 'completed'
            progress_data['message'] = 'No messages found matching the criteria.'
            mail_connection.logout()
            return
        
        message_ids = raw_message_ids_string.split()
        progress_data['total'] = len(message_ids)
        progress_data['message'] = f'Found {len(message_ids)} messages. Processing...'
        
        # Create download directory
        os.makedirs(DOWNLOAD_DIR, exist_ok=True)
        
        # Process each email
        download_count = 0
        for idx, uid in enumerate(message_ids):
            progress_data['progress'] = idx + 1
            progress_data['message'] = f'Processing email {idx + 1} of {len(message_ids)}...'
            
            fetch_status, fetch_data = mail_connection.fetch(uid, '(RFC822)')
            
            if fetch_status == 'OK':
                raw_email_bytes = fetch_data[0][1]
                msg = BytesParser(policy=policy.default).parsebytes(raw_email_bytes)
                
                # Process attachments
                for part in msg.walk():
                    if part.get_filename() and part.get_content_type() == 'application/pdf':
                        filename = part.get_filename()
                        safe_filename = sanitize_filename(filename)
                        
                        filepath = os.path.join(DOWNLOAD_DIR, safe_filename)
                        counter = 1
                        while os.path.exists(filepath):
                            name, ext = os.path.splitext(safe_filename)
                            filepath = os.path.join(DOWNLOAD_DIR, f"{name}_{counter}{ext}")
                            counter += 1
                        
                        try:
                            payload = part.get_payload(decode=True)
                            with open(filepath, 'wb') as f:
                                f.write(payload)
                            
                            download_count += 1
                            progress_data['downloads'] = download_count
                            progress_data['files'].append({
                                'name': os.path.basename(filepath),
                                'subject': msg['Subject'],
                                'from': msg['From'],
                                'date': msg['Date']
                            })
                        except Exception as e:
                            print(f"Error saving attachment: {e}")
        
        mail_connection.logout()
        
        progress_data['status'] = 'completed'
        progress_data['message'] = f'Complete! Downloaded {download_count} PDF(s).'
        
    except Exception as e:
        progress_data['status'] = 'error'
        progress_data['message'] = f'Error: {str(e)}'

@app.route('/')
def index():
    """Render the main page."""
    return render_template('index.html')

@app.route('/start', methods=['POST'])
def start_processing():
    """Start the email processing in a background thread."""
    data = request.json
    
    email_address = data.get('email_address')
    app_password = data.get('app_password')
    sender_mail = data.get('sender_mail')
    start_date = data.get('start_date')
    end_date = data.get('end_date')
    
    # Validate inputs
    if not all([email_address, app_password, sender_mail, start_date, end_date]):
        return jsonify({'error': 'All fields are required'}), 400
    
    # Start processing in background thread
    thread = Thread(target=process_emails, args=(email_address, app_password, sender_mail, start_date, end_date))
    thread.daemon = True
    thread.start()
    
    return jsonify({'message': 'Processing started'})

@app.route('/progress')
def get_progress():
    """Get the current progress status."""
    return jsonify(progress_data)

@app.route('/downloads/<path:filename>')
def download_file(filename):
    """Serve downloaded files."""
    return send_from_directory(DOWNLOAD_DIR, filename, as_attachment=True)

@app.route('/files')
def list_files():
    """List all downloaded files."""
    try:
        if os.path.exists(DOWNLOAD_DIR):
            files = []
            for filename in os.listdir(DOWNLOAD_DIR):
                filepath = os.path.join(DOWNLOAD_DIR, filename)
                if os.path.isfile(filepath):
                    files.append({
                        'name': filename,
                        'size': os.path.getsize(filepath),
                        'modified': datetime.datetime.fromtimestamp(os.path.getmtime(filepath)).strftime('%Y-%m-%d %H:%M:%S')
                    })
            return jsonify({'files': files})
        return jsonify({'files': []})
    except Exception as e:
        return jsonify({'error': str(e)}), 500

if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=9090)

