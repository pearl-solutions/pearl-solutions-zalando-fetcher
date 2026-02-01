import email
import re
import imaplib
import os
import csv
import time
from email.header import decode_header
from email.utils import parsedate_to_datetime
from datetime import datetime
from getpass import getpass


def save_code_to_csv(email_addr, code, email_date, filename="codes.csv"):
    """
    Save extracted code to CSV file

    Args:
        email_addr (str): Email address associated with the code
        code (str): Verification code extracted from email
        email_date (str): Date when the email was received
        filename (str): Output CSV filename
    """
    file_exists = os.path.isfile(filename)

    with open(filename, mode='a', newline='', encoding='utf-8') as csvfile:
        writer = csv.writer(csvfile)

        if not file_exists:
            writer.writerow(['email', 'code', 'received_date'])

        writer.writerow([email_addr, code, email_date])


def validate_email(email_addr):
    """
    Validate email address format

    Args:
        email_addr (str): Email address to validate

    Returns:
        bool: True if valid, False otherwise
    """
    pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
    return re.match(pattern, email_addr) is not None


def validate_date(date_string):
    """
    Validate and parse date string

    Args:
        date_string (str): Date in format YYYY-MM-DD

    Returns:
        datetime: Parsed datetime object or None if invalid
    """
    try:
        return datetime.strptime(date_string, "%Y-%m-%d")
    except ValueError:
        return None


def get_user_inputs():
    """
    Collect and validate user inputs for IMAP configuration

    Returns:
        dict: Configuration dictionary with validated inputs
    """
    print("\n=== Email Code Extractor Configuration ===\n")

    # IMAP Server
    imap_server = input("IMAP Server (default: imap.gmail.com): ").strip()
    if not imap_server:
        imap_server = 'imap.gmail.com'

    # Email address
    while True:
        email_addr = input("Email address: ").strip()
        if validate_email(email_addr):
            break
        print("Invalid email format. Please try again.")

    # Password
    password = getpass("Password (input hidden): ").strip()
    while not password:
        print("Password cannot be empty.")
        password = getpass("Password (input hidden): ").strip()

    # Start date
    while True:
        date_input = input("Start date (YYYY-MM-DD, e.g., 2026-01-27): ").strip()
        start_date = validate_date(date_input)
        if start_date:
            break
        print("Invalid date format. Please use YYYY-MM-DD.")

    # Subject keyword
    subject_keyword = input("Subject keyword to search (default: '20%'): ").strip()
    if not subject_keyword:
        subject_keyword = '20%'

    # Mailbox folder
    mailbox = input("Mailbox folder (default: [Gmail]/Spam): ").strip()
    if not mailbox:
        mailbox = '[Gmail]/Spam'

    return {
        'imap_server': imap_server,
        'email': email_addr,
        'password': password,
        'start_date': start_date,
        'subject_keyword': subject_keyword,
        'mailbox': mailbox
    }


def connect_imap(imap_server, email_addr, password):
    """
    Establish IMAP connection with retry logic

    Args:
        imap_server (str): IMAP server address
        email_addr (str): Email address for login
        password (str): Account password

    Returns:
        imaplib.IMAP4_SSL: Connected IMAP object
    """
    try:
        mail = imaplib.IMAP4_SSL(imap_server)
        mail.login(email_addr, password)
        return mail
    except imaplib.IMAP4.error as e:
        if b'Too many simultaneous connections' in str(e).encode():
            print("Too many simultaneous connections. Waiting 30 seconds...")
            time.sleep(30)
            mail = imaplib.IMAP4_SSL(imap_server)
            mail.login(email_addr, password)
            return mail
        else:
            raise


def extract_codes(config):
    """
    Main function to extract verification codes from emails

    Args:
        config (dict): Configuration dictionary from user inputs
    """
    date_imap = config['start_date'].strftime("%d-%b-%Y")

    print("\nConnecting to email server...")

    mail = connect_imap(config['imap_server'], config['email'], config['password'])

    # Select the specified mailbox
    print(f"Selecting mailbox: {config['mailbox']}")
    mail.select(config['mailbox'])

    # Search for emails
    search_query = f'(SINCE {date_imap} SUBJECT "{config["subject_keyword"]}")'
    status, search_data = mail.search(None, search_query)

    if status != "OK":
        print("Error in search query.")
        return

    message_ids = search_data[0].split()
    print(f"{len(message_ids)} messages found with '{config['subject_keyword']}' in subject.\n")

    if len(message_ids) == 0:
        print("No messages to process. Exiting.")
        mail.close()
        mail.logout()
        return

    processed = 0
    codes_found = 0

    for num in message_ids:
        try:
            # Reconnect every 50 messages to avoid timeout
            if processed > 0 and processed % 50 == 0:
                print(f"Reconnecting... ({processed} messages processed, {codes_found} codes found)")
                try:
                    mail.close()
                    mail.logout()
                except:
                    pass
                time.sleep(1)
                mail = connect_imap(config['imap_server'], config['email'], config['password'])
                mail.select(config['mailbox'])

            status, msg_data = mail.fetch(num, '(RFC822)')

            if status != "OK":
                print(f"Error fetching message {num}")
                continue

        except Exception as e:
            print(f"Error fetching message {num}: {e}")
            # Attempt to reconnect
            try:
                mail.close()
                mail.logout()
            except:
                pass
            time.sleep(5)
            try:
                mail = connect_imap(config['imap_server'], config['email'], config['password'])
                mail.select(config['mailbox'])
                status, msg_data = mail.fetch(num, '(RFC822)')
            except Exception as e2:
                print(f"Reconnection failed: {e2}")
                continue

        # Parse email
        raw_email = msg_data[0][1]
        msg = email.message_from_bytes(raw_email)

        # Decode subject
        subject, encoding = decode_header(msg.get("Subject"))[0]
        if isinstance(subject, bytes):
            subject = subject.decode(encoding or "utf-8")

        to_ = msg.get("To")

        # Get email received date
        email_date_str = msg.get("Date")
        try:
            # Parse the email date and format it
            email_date = parsedate_to_datetime(email_date_str)
            formatted_date = email_date.strftime("%Y-%m-%d %H:%M:%S")
        except:
            # Fallback to current time if parsing fails
            formatted_date = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

        # Progress update every 10 messages
        if processed % 10 == 0:
            print(f"[{processed}] Processing: {subject[:50]}...")

        # Extract recipient email
        emails_found = re.findall(r'[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}', to_)
        if not emails_found:
            processed += 1
            continue
        recipient_email = emails_found[0]

        # Extract email body
        body = ""
        if msg.is_multipart():
            for part in msg.walk():
                content_type = part.get_content_type()
                content_disposition = str(part.get("Content-Disposition"))

                if content_type == "text/plain" and "attachment" not in content_disposition:
                    charset = part.get_content_charset() or "utf-8"
                    try:
                        body = part.get_payload(decode=True).decode(charset, errors="replace")
                        break
                    except:
                        continue
        else:
            charset = msg.get_content_charset() or "utf-8"
            try:
                body = msg.get_payload(decode=True).decode(charset, errors="replace")
            except:
                pass

        # Search for verification code pattern
        if body:
            # Pattern: <font...>10-character alphanumeric code</font>
            match = re.search(r"<font[^>]*>([A-Z0-9]{10})</font>", body)

            if match:
                code = match.group(1)
                save_code_to_csv(recipient_email, code, formatted_date)
                codes_found += 1
                print(f"Code found: {code} for {recipient_email}")

        processed += 1
        time.sleep(0.1)  # Rate limiting

    # Close connection
    try:
        mail.close()
        mail.logout()
    except:
        pass

    print(f"\n{'=' * 40}")
    print(f"Processing complete!")
    print(f"{processed} messages processed.")
    print(f"{codes_found} codes found and saved to codes.csv")
    print(f"{'=' * 40}\n")


def main():
    """
    Main entry point for the application
    """
    try:
        config = get_user_inputs()
        extract_codes(config)
    except KeyboardInterrupt:
        print("\n\nOperation cancelled by user.")
    except Exception as e:
        print(f"\nAn error occurred: {e}")
        raise


if __name__ == "__main__":
    main()