"""
Email Promo Code Extractor

This module extracts promotional codes from emails via IMAP and saves them to CSV.
Supports multiple code formats and email providers with automatic reconnection
and error handling.
"""

import csv
import email
import imaplib
import os
import re
import time
from datetime import datetime
from email.header import decode_header
from email.utils import parsedate_to_datetime


def save_code_to_csv(email_addr, code, email_date, filename="codes.csv"):
    """
    Save extracted promo code to CSV file.

    Creates a new CSV file with headers if it doesn't exist, otherwise appends
    to the existing file. Each row contains the recipient email, extracted code,
    and the date when the email was received.

    Args:
        email_addr (str): Email address that received the promo code.
        code (str): Promo code extracted from the email body.
        email_date (str): Date and time when the email was received (format: YYYY-MM-DD HH:MM:SS).
        filename (str, optional): Output CSV filename. Defaults to "codes.csv".

    Returns:
        None

    Raises:
        IOError: If the file cannot be written to.
        ValueError: If email_addr or code are None or empty.
    """
    if not email_addr or not code:
        raise ValueError("Email address and code cannot be empty")

    file_exists = os.path.isfile(filename)

    with open(filename, mode="a", newline="", encoding="utf-8") as csvfile:
        writer = csv.writer(csvfile)

        if not file_exists:
            writer.writerow(["email", "code", "received_date"])

        writer.writerow([email_addr, code, email_date])


def validate_email(email_addr) -> bool:
    """
    Validate email address format using regex pattern.

    Checks if the provided string matches a standard email format pattern.
    Does not verify if the email actually exists.

    Args:
        email_addr (str): Email address to validate.

    Returns:
        bool: True if email format is valid, False otherwise.

    Example:
        >>> validate_email("user@example.com")
        True
        >>> validate_email("invalid.email")
        False
    """
    pattern = r"^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$"
    return re.match(pattern, email_addr) is not None


def validate_date(date_string) -> datetime | None:
    """
    Validate and parse date string in YYYY-MM-DD format.

    Attempts to parse the provided date string and returns a datetime object
    if successful. Used to ensure user provides properly formatted start dates.

    Args:
        date_string (str): Date string to validate (format: YYYY-MM-DD).

    Returns:
        datetime.datetime: Parsed datetime object if valid, None otherwise.

    Example:
        >>> validate_date("2026-01-27")
        datetime.datetime(2026, 1, 27, 0, 0)
        >>> validate_date("01-27-2026")
        None
    """
    try:
        return datetime.strptime(date_string, "%Y-%m-%d")
    except ValueError:
        return None


def get_user_inputs() -> dict:
    """
    Collect and validate user inputs for IMAP configuration interactively.

    Prompts the user to enter IMAP server details, email credentials, date range,
    search criteria, and mailbox folder. Provides sensible defaults for common
    configurations (Gmail) and validates all inputs before returning.

    Returns:
        dict: Configuration dictionary containing:
            - imap_server (str): IMAP server address (default: imap.gmail.com)
            - email (str): Validated email address
            - password (str): Account password/app password
            - start_date (datetime): Start date for email search
            - subject_keyword (str): Subject line keyword to filter emails
            - mailbox (str): Mailbox folder path (default: [Gmail]/Spam)

    Raises:
        KeyboardInterrupt: If user cancels input with Ctrl+C.

    Notes:
        - Email address format is validated before accepting.
        - Password cannot be empty.
        - Date must be in YYYY-MM-DD format.
        - Can be interrupted at any time with Ctrl+C.
    """
    print("\n=== Email Promo Code Extractor Configuration ===\n")

    try:
        imap_server = input("IMAP Server (default: imap.gmail.com): ").strip()
        if not imap_server:
            imap_server = "imap.gmail.com"

        while True:
            email_addr = input("Email address: ").strip()
            if validate_email(email_addr):
                break
            print("Invalid email format. Please try again.")

        while True:
            password = input("Password or App Password: ").strip()
            if password:
                break
            print("Password cannot be empty.")

        while True:
            date_input = input("Start date (YYYY-MM-DD, example: 2026-01-27): ").strip()
            start_date = validate_date(date_input)
            if start_date:
                break
            print("Invalid date format. Please use YYYY-MM-DD.")

        subject_keyword = input("Subject keyword to search (default: 20%): ").strip()
        if not subject_keyword:
            subject_keyword = "20%"

        mailbox = input("Mailbox folder (default: [Gmail]/Spam): ").strip()
        if not mailbox:
            mailbox = "[Gmail]/Spam"

        return {
            "imap_server": imap_server,
            "email": email_addr,
            "password": password,
            "start_date": start_date,
            "subject_keyword": subject_keyword,
            "mailbox": mailbox,
        }

    except KeyboardInterrupt:
        raise


def connect_imap(imap_server, email_addr, password) -> imaplib.IMAP4_SSL:
    """
    Establish IMAP connection with automatic retry on simultaneous connection limit.

    Attempts to connect to the specified IMAP server and authenticate with
    provided credentials. If the server returns a "too many simultaneous connections"
    error, waits 30 seconds before retrying.

    Args:
        imap_server (str): IMAP server address (e.g., imap.gmail.com).
        email_addr (str): Email address for authentication.
        password (str): Account password or app-specific password.

    Returns:
        imaplib.IMAP4_SSL: Connected and authenticated IMAP connection object.

    Raises:
        imaplib.IMAP4.error: If authentication fails or server is unreachable.
        socket.error: If network connection cannot be established.

    Notes:
        - Uses SSL/TLS encryption for connection security.
        - Automatically handles temporary connection limits with exponential backoff.
    """
    try:
        mail = imaplib.IMAP4_SSL(imap_server)
        mail.login(email_addr, password)
        return mail
    except imaplib.IMAP4.error as e:
        if b"Too many simultaneous connections" in str(e).encode():
            print(
                "Too many simultaneous connections. Waiting 30 seconds before retry..."
            )
            time.sleep(30)
            mail = imaplib.IMAP4_SSL(imap_server)
            mail.login(email_addr, password)
            return mail
        else:
            raise


def extract_promo_code(body) -> str | None:
    """
    Extract promo code from email body using multiple pattern matching strategies.

    Attempts to find a promo code by trying several regex patterns in order
    of specificity. Falls back to more general patterns if specific ones don't match.
    Supports codes embedded in HTML tags, preceded by keywords, or standalone.

    Args:
        body (str): Email body content (may contain HTML).

    Returns:
        str: Extracted promo code (10 uppercase alphanumeric characters),
             or None if no code is found.

    Notes:
        Code format expected: 10 uppercase alphanumeric characters (e.g., W79UQJ8892).
        To support different formats, modify the regex patterns or the {10} quantifier.

    Pattern strategies (in order):
        1. Inside <td> HTML tags
        2. Inside any HTML tag
        3. Preceded by code-related keywords
        4. No generic fallback (prevents false positives)
    """
    if not body:
        return None

    patterns = [
        (r"<td[^>]*>([A-Z0-9]{10})</td>", "TD HTML tag"),
        (r"<[^>]*>([A-Z0-9]{10})<", "Generic HTML tag"),
        (
            r"(?:code|promo|discount|coupon)[\s:]*([A-Z0-9]{10})",
            "Promo keyword",
        ),
    ]

    for pattern, strategy_name in patterns:
        match = re.search(pattern, body, re.IGNORECASE)
        if match:
            return match.group(1)

    return None


def extract_email_from_header(header) -> str | None:
    """
    Extract the first valid email address from an email header field.

    Generic helper function to extract email addresses from To, From, Cc, Bcc,
    or other header fields which may contain multiple email addresses or additional
    formatting (like display names).

    Args:
        header (str): Content of an email header field (To, From, Cc, Bcc, etc.).

    Returns:
        str: First valid email address found, or None if no valid email exists.

    Example:
        >>> extract_email_from_header("user@example.com")
        'user@example.com'
        >>> extract_email_from_header("John Doe <john@example.com>")
        'john@example.com'
        >>> extract_email_from_header("alice@example.com, bob@example.com")
        'alice@example.com'
    """
    if not header:
        return None

    emails_found = re.findall(r"[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}", header)
    return emails_found[0] if emails_found else None


def extract_recipient_email(to_header, from_header, imap_email) -> str | None:
    """
    Extract the recipient email address with intelligent fallback logic.

    Attempts to extract a valid recipient email from the To header. If the To
    header is empty or matches the IMAP account email, falls back to extracting
    the sender's email from the From header. This handles cases where emails
    are sent to the account itself (e.g., promotional emails from vendors), where
    the actual relevant email address is the sender, not the recipient.

    Args:
        to_header (str): Content of the email's To header field.
        from_header (str): Content of the email's From header field.
        imap_email (str): The IMAP account email address used for login.

    Returns:
        str: Valid email address to associate with the promo code, or None if
             no valid email is found. Prioritizes To header unless it matches
             imap_email, in which case uses From header.

    Example:
        >>> extract_recipient_email("customer@example.com", "promo@zalando.com", "account@gmail.com")
        'customer@example.com'
        >>> extract_recipient_email("account@gmail.com", "promo@zalando.com", "account@gmail.com")
        'promo@zalando.com'
        >>> extract_recipient_email("", "sender@example.com", "account@gmail.com")
        'sender@example.com'

    Notes:
        - Email comparison is case-insensitive
        - If To header is the IMAP account, assumes email was sent TO the account
          and uses From (sender) as the relevant contact
        - Returns None only if both To and From are invalid or missing
    """
    to_email = extract_email_from_header(to_header)

    if to_email and to_email.lower() != imap_email.lower():
        return to_email

    from_email = extract_email_from_header(from_header)
    return from_email if from_email else None


def extract_email_body(msg) -> str:
    """
    Extract plain text content from email message.

    Handles both multipart and single-part messages. For multipart messages,
    prioritizes plain text content over HTML. Automatically detects and decodes
    character encoding, with UTF-8 as fallback.

    Args:
        msg (email.message.Message): Parsed email message object.

    Returns:
        str: Extracted plain text body, or empty string if extraction fails.

    Notes:
        - Multipart emails: iterates through parts and extracts first text/plain
        - Single-part emails: extracts payload directly
        - Uses error="replace" to handle encoding issues gracefully
    """
    body = ""

    if msg.is_multipart():
        for part in msg.walk():
            content_type = part.get_content_type()
            content_disposition = str(part.get("Content-Disposition", ""))

            if content_type == "text/plain" and "attachment" not in content_disposition:
                charset = part.get_content_charset() or "utf-8"
                try:
                    body = part.get_payload(decode=True).decode(
                        charset, errors="replace"
                    )
                    break
                except Exception:
                    continue
    else:
        charset = msg.get_content_charset() or "utf-8"
        try:
            body = msg.get_payload(decode=True).decode(charset, errors="replace")
        except Exception:
            pass

    return body


def get_email_date(msg) -> str:
    """
    Extract and format the email's received date.

    Parses the Date header from the email and formats it as a human-readable
    timestamp. Falls back to current time if parsing fails.

    Args:
        msg (email.message.Message): Parsed email message object.

    Returns:
        str: Formatted date and time (format: YYYY-MM-DD HH:MM:SS).

    Notes:
        - Handles various date formats from different email servers
        - Fallback to current time ensures a value is always returned
    """
    email_date_str = msg.get("Date")
    try:
        email_date = parsedate_to_datetime(email_date_str)
        return email_date.strftime("%Y-%m-%d %H:%M:%S")
    except Exception:
        return datetime.now().strftime("%Y-%m-%d %H:%M:%S")


def process_email_message(mail, msg_num, config) -> dict:
    """
    Fetch, parse, and process a single email message.

    Retrieves an email by its message number, extracts the recipient address,
    email date, and body content, then searches for promo codes.
    Saves found codes to CSV only if a valid recipient email is found.

    Args:
        mail (imaplib.IMAP4_SSL): Active IMAP connection.
        msg_num (bytes): Message number/UID from IMAP server.
        config (dict): Configuration dictionary containing at least 'email' key.

    Returns:
        dict: Result dictionary containing:
            - success (bool): True if message was processed without errors
            - code_found (bool): True if a promo code was extracted and saved
            - code (str): Extracted code, or None
            - email (str): Recipient email address, or None
            - error (str): Error message if applicable, or None

    Notes:
        - Code is only saved if both recipient_email and code are valid
        - If recipient_email cannot be determined, code is not saved
    """
    try:
        status, msg_data = mail.fetch(msg_num, "(RFC822)")

        if status != "OK":
            return {
                "success": False,
                "code_found": False,
                "error": f"Fetch failed: {status}",
            }

        raw_email = msg_data[0][1]
        msg = email.message_from_bytes(raw_email)

        subject, encoding = decode_header(msg.get("Subject", ""))[0]
        if isinstance(subject, bytes):
            subject = subject.decode(encoding or "utf-8")

        to_header = msg.get("To", "")
        from_header = msg.get("From", "")
        recipient_email = extract_recipient_email(
            to_header, from_header, config["email"]
        )

        email_date = get_email_date(msg)
        body = extract_email_body(msg)
        code = extract_promo_code(body)

        if code and recipient_email:
            save_code_to_csv(recipient_email, code, email_date)
            return {
                "success": True,
                "code_found": True,
                "code": code,
                "email": recipient_email,
            }

        if code and not recipient_email:
            return {
                "success": True,
                "code_found": False,
                "email": None,
                "error": "Code found but no valid recipient email",
            }

        return {"success": True, "code_found": False, "email": recipient_email}

    except Exception as e:
        return {"success": False, "code_found": False, "error": str(e)}


def extract_codes(config):
    """
    Main function to extract promo codes from emails via IMAP.

    Connects to the specified IMAP server, searches for emails matching the
    given criteria, extracts promo codes from each message, and saves
    them to a CSV file. Handles connection timeouts, network errors, and
    implements automatic reconnection every 50 messages.

    Args:
        config (dict): Configuration dictionary containing:
            - imap_server (str): IMAP server address
            - email (str): Email account to log in
            - password (str): Account password
            - start_date (datetime): Earliest date to search
            - subject_keyword (str): Subject line filter
            - mailbox (str): Mailbox folder to search

    Returns:
        None (results are written to codes.csv)

    Output:
        Prints processing status, progress, and summary to console.
        Creates or appends to codes.csv with extracted promo codes.

    Notes:
        - Automatically reconnects every 50 messages to avoid server timeouts
        - Implements 0.1 second delay between message processing for rate limiting
        - Handles multipart and single-part email formats
        - Gracefully continues on individual message errors
    """
    date_imap = config["start_date"].strftime("%d-%b-%Y")

    print("\nConnecting to email server...")

    mail = connect_imap(config["imap_server"], config["email"], config["password"])

    print(f"Selecting mailbox: {config['mailbox']}")
    mail.select(config["mailbox"])

    search_query = f'(SINCE {date_imap} SUBJECT "{config["subject_keyword"]}")'
    status, search_data = mail.search(None, search_query)

    if status != "OK":
        print("Error in search query. Exiting.")
        mail.close()
        mail.logout()
        return

    message_ids = search_data[0].split()
    print(
        f"Found {len(message_ids)} messages with '{config['subject_keyword']}' in subject.\n"
    )

    if len(message_ids) == 0:
        print("No messages to process. Exiting.")
        mail.close()
        mail.logout()
        return

    processed = 0
    codes_found = 0
    codes_skipped = 0
    errors = 0

    for msg_num in message_ids:
        try:
            if processed > 0 and processed % 50 == 0:
                print(
                    f"Reconnecting... ({processed} processed, {codes_found} codes found)"
                )
                try:
                    mail.close()
                    mail.logout()
                except Exception:
                    pass
                time.sleep(1)
                mail = connect_imap(
                    config["imap_server"], config["email"], config["password"]
                )
                mail.select(config["mailbox"])

            if processed % 10 == 0:
                print(f"[{processed}] Processing messages...")

            result = process_email_message(mail, msg_num, config)

            if not result["success"]:
                errors += 1
                if result.get("error"):
                    print(f"Error processing message: {result['error']}")
            elif result["code_found"]:
                codes_found += 1
                print(f"Code extracted: {result['code']} ({result['email']})")
            elif result.get("error"):
                codes_skipped += 1
                print(f"Skipped: {result['error']}")

            processed += 1
            time.sleep(0.1)

        except Exception as e:
            print(f"Error fetching message {msg_num}: {e}")
            errors += 1

            try:
                mail.close()
                mail.logout()
            except Exception:
                pass

            time.sleep(5)

            try:
                mail = connect_imap(
                    config["imap_server"], config["email"], config["password"]
                )
                mail.select(config["mailbox"])
            except Exception as reconnect_error:
                print(f"Reconnection failed: {reconnect_error}")
                continue

            processed += 1

    try:
        mail.close()
        mail.logout()
    except Exception:
        pass

    print(f"\n{'=' * 50}")
    print("Processing Complete")
    print(f"Total messages processed: {processed}")
    print(f"Codes successfully extracted: {codes_found}")
    print(f"Codes skipped (no valid recipient): {codes_skipped}")
    print(f"Errors encountered: {errors}")
    print(f"{'=' * 50}\n")


def main():
    """
    Main entry point for the application.

    Orchestrates the interactive configuration process and promo code extraction workflow.
    Handles keyboard interrupts gracefully and provides error reporting.

    Raises:
        KeyboardInterrupt: Handled internally and reported to user.
        Exception: Caught and reported with traceback for debugging.
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
