import imaplib
import ssl
import os
import email
from email import policy
from email.parser import BytesParser
import re
import datetime

EMAIL_ADDRESS = "YOUR_GMAIL_EMAIL@gmail.com"
APP_PASSWORD = "YOUR_GENERATED_APP_PASSWORD"
IMAP_SERVER = "imap.gmail.com"
IMAP_PORT = 993

DOWNLOAD_DIR = "downloaded_attachments"

def connect_to_imap(email_address, app_password, imap_server, imap_port):
    try: # Start a 'try' block to handle potential errors during connection and login.
        context = ssl.create_default_context()
        print(f"Attempting to connect to IMAP server: {imap_server}:{imap_port}...")
        mail = imaplib.IMAP4_SSL(imap_server, imap_port, ssl_context=context)
        print("Connected to IMAP Server.")

        print(f"Logging in as {email_address}...")
        mail.login(email_address, app_password)
        print("Successfully logged in.")

        return mail

    except imaplib.IMAP4.error as e:
        print(f"IMAP login failed: {e}")
        print("Please check your email address, app password, and ensure 2-Step Verification is enabled and an app password was generated correctly.")
        return None
    except Exception as e:
        print(f"An unexpected error occurred: {e}")
        return None

def sanitize_filename(filename):
    return re.sub(r'[^\w\-. ]', '_', filename)

def main():
    email_address = os.environ.get("EMAIL_ADDRESS", EMAIL_ADDRESS)
    app_password = os.environ.get("APP_PASSWORD", APP_PASSWORD)

    if email_address == "YOUR_GMAIL_EMAIL@gmail.com" or app_password == "YOUR_GENERATED_APP_PASSWORD":
        print("ERROR: Please replace 'YOUR_GMAIL_EMAIL@gmail.com' and 'YOUR_GENERATED_APP_PASSWORD' with your actual Gmail email and the generated app password.")
        print("Alternatively, set the EMAIL_ADDRESS and APP_PASSWORD environment variables.")
        return

    mail_connection = connect_to_imap(email_address, app_password, IMAP_SERVER, IMAP_PORT)

    if mail_connection:
        print("\nConnection successful!")

        sender_mail = input('What sender to use?: ').strip()
        print("Please enter dates in DD-Mon-YYYY format (e.g., 01-Jan-2024)")
        start_date_str = input('From which date?: ').strip()
        end_date_str = input('To which date?: ').strip()

        try:
            start_date_obj = datetime.datetime.strptime(start_date_str, '%d-%b-%Y').date()
            end_date_obj = datetime.datetime.strptime(end_date_str, '%d-%b-%Y').date()
            before_date_obj = end_date_obj + datetime.timedelta(days=1)
            
            imap_start_date = start_date_obj.strftime('%d-%b-%Y')
            imap_before_date = before_date_obj.strftime('%d-%b-%Y')

            print("\nAvailable Mailboxes:")
            status, mailboxes_data = mail_connection.list()
            if status == 'OK':
                for mailbox_info in mailboxes_data:
                    decoded_mailbox_info = mailbox_info.decode('utf-8')
                    last_quote_index = decoded_mailbox_info.rfind('"')
                    if last_quote_index != -1:
                        first_quote_index = decoded_mailbox_info.rfind('"', 0, last_quote_index)
                        if first_quote_index != -1:
                            mailbox_name = decoded_mailbox_info[first_quote_index + 1 : last_quote_index]
                            print(f"- {mailbox_name}")
                        else:
                            print(f"- Could not parse: {decoded_mailbox_info}")
                    else:
                        print(f"- Could not parse: {decoded_mailbox_info}")
            else:
                print(f"Failed to list mailboxes: {status}")

            status, messages_in_inbox = mail_connection.select("INBOX")
            if status == 'OK':
                print(f"\nSelected INBOX. Total messages: {messages_in_inbox[0].decode('utf-8')}")
            else:
                print(f"\nFailed to select INBOX: {status}. Exiting search operation.")
                return

            print(f"\nSearching INBOX for emails from '{sender_mail}' between {start_date_str} and {end_date_str}...")
            search_status, search_data = mail_connection.search(
                None,
                'FROM', f'"{sender_mail}"',
                'SINCE', f'"{imap_start_date}"',
                'BEFORE', f'"{imap_before_date}"'
            )

            if search_status == 'OK':
                raw_message_ids_string = search_data[0].decode('utf-8')

                if raw_message_ids_string:
                    message_ids = raw_message_ids_string.split()
                    print(f"Found {len(message_ids)} messages matching criteria.")

                    os.makedirs(DOWNLOAD_DIR, exist_ok=True)
                    print(f"\nAttachments will be saved in: {os.path.abspath(DOWNLOAD_DIR)}")

                    print("\n--- Processing Fetched Emails and Downloading PDFs ---")
                    download_count = 0
                    for uid in message_ids:
                        print(f"\nProcessing email with UID: {uid}")
                        fetch_status, fetch_data = mail_connection.fetch(uid, '(RFC822)')

                        if fetch_status == 'OK':
                            raw_email_bytes = fetch_data[0][1]
                            msg = BytesParser(policy=policy.default).parsebytes(raw_email_bytes)

                            print(f"  Subject: {msg['Subject']}")
                            print(f"  From: {msg['From']}")
                            print(f"  Date: {msg['Date']}")

                            for part in msg.walk():
                                if part.get_filename() and part.get_content_type() == 'application/pdf':
                                    filename = part.get_filename()
                                    print(f"  -> Identified PDF attachment: {filename}")

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
                                        print(f"  -> Successfully downloaded: {os.path.basename(filepath)}")
                                        download_count += 1
                                    except Exception as e:
                                        print(f"  -> ERROR: Could not save attachment '{safe_filename}': {e}")

                        else:
                            print(f"Failed to fetch email UID {uid}: {fetch_status}. Details: {fetch_data[0].decode('utf-8') if fetch_data else 'No details'}")

                    print(f"\n--- Download complete. Total PDFs downloaded: {download_count} ---")

                else:
                    print("No messages found matching the specified criteria.")
            else:
                print(f"IMAP search failed: {status}. Details: {data[0].decode('utf-8')}")

        except ValueError as e:
            print(f"ERROR: Invalid date format. Please use DD-Mon-YYYY. Details: {e}")
        except imaplib.IMAP4.error as e:
            print(f"IMAP operation failed: {e}")
        except Exception as e:
            print(f"An unexpected error occurred during IMAP operations: {e}")
        finally:
            if mail_connection:
                mail_connection.logout()
                print("Logged out from IMAP server.")
    else:
        print("\nFailed to establish IMAP connection. Exiting.")

if __name__ == "__main__":
    main()