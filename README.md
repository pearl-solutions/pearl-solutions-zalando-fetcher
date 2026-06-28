<div align="center">
  <img src="https://github.com/Pearl-Solutions/.github/blob/main/Pearl_Solutions__Tavola_disegno_1-02.png?raw=true" alt="Pearl Solutions Banner" />
</div>

<div align="center">
  <h1>Zalando -20% Promo Code Extractor</h1>
  <p>
    <strong>Automated extraction of Zalando promotional codes from email</strong><br>
    Streamline your workflow by automatically extracting Zalando -20% promo codes from your inbox or spam folder.
  </p>
</div>

---

## Overview

**Email Promo Code Extractor** is a Python-based automation tool that searches through your email folders (like spam) to find and extract promotional reduction codes. Perfect for managing multiple accounts or bulk processing emails.

**Key Features:**
- **Fast bulk processing** of promo emails
- **Intelligent recipient detection** (To → From fallback for marketing emails)
- **Multi-pattern code matching** for HTML and text formats
- **CSV export** with timestamps and sender information
- **Robust error handling** with auto-reconnection
- **Input validation** for safe configuration
- **IMAP compatible** with Gmail, Outlook, and more
- **Interactive CLI** with real-time progress tracking
- **No external dependencies** (Python standard library only)

---

## Prerequisites

- Python 3.6 or higher
- IMAP-enabled email account
- For Gmail users: [App Password](https://support.google.com/accounts/answer/185833) (if 2FA is enabled)

---

## Installation

1. **Clone the repository**
   ```bash
   git clone https://github.com/pearl-solutions/pearl-solutions-zalando-fetcher.git
   cd pearl-solutions-zalando-fetcher
   ```

2. **Run the script**
   ```bash
   python extract_promo_codes.py
   ```
   *Note: This project uses only Python standard library, so no external packages are required.*

---

## Usage

### Basic Usage

Run the script and follow the interactive prompts:

```bash
python extract_promo_codes.py
```

### Configuration Prompts

The script will ask for:

1. **IMAP Server** (default: `imap.gmail.com`)
   - Gmail: `imap.gmail.com`
   - Outlook: `outlook.office365.com`
   - Yahoo: `imap.mail.yahoo.com`

2. **Email Address**: Your full email address

3. **Password**: 
   - For Gmail with 2FA: Use an [App Password](https://support.google.com/accounts/answer/185833)
   - For other providers: Your regular password

4. **Start Date**: Filter emails from this date (format: YYYY-MM-DD)

5. **Subject Keyword**: Text to search in email subjects (default: `20%`)

6. **Mailbox Folder**: Which folder to search (default: `[Gmail]/Spam`)
   - Gmail Spam: `[Gmail]/Spam`
   - Gmail Inbox: `INBOX`
   - Outlook Spam: `Junk`

### Interrupt Safely

You can stop the script at any time with `Ctrl+C` during configuration or processing.

### Example Session

```
=== Email Promo Code Extractor Configuration ===

IMAP Server (default: imap.gmail.com): 
Email address: yourname@gmail.com
Password or App Password: 
Start date (YYYY-MM-DD, example: 2026-01-27): 2026-01-15
Subject keyword to search (default: 20%): 
Mailbox folder (default: [Gmail]/Spam): 

Connecting to email server...
Selecting mailbox: [Gmail]/Spam
Found 47 messages with '20%' in subject.

[0] Processing messages...
Code extracted: ABC1234XYZ (customer@example.com)
[10] Processing messages...
Code extracted: DEF5678UVW (promo@zalando.com)
...

==================================================
Processing Complete
Total messages processed: 47
Codes successfully extracted: 23
Codes skipped (no valid recipient): 2
Errors encountered: 0
==================================================
```

---

## Output

The extracted codes are saved to `codes.csv` with the following format:

```csv
email,code,received_date
customer@example.com,ABC1234XYZ,2026-01-27 14:32:15
promo@zalando.com,DEF5678UVW,2026-01-27 14:32:28
customer@example.com,XYZ9876ABC,2026-01-27 15:10:42
```

---

## Code Detection Patterns

The script uses multiple pattern-matching strategies to find promo codes:

### Pattern 1: HTML `<td>` Tags
```html
<td align="left">W79UQJ8892</td>
```

### Pattern 2: Generic HTML Tags
```html
<span>ABC1234XYZ</span>
<font>DEF5678UVW</font>
```

### Pattern 3: Keyword-based
```
Code: ABC1234XYZ
Promo: DEF5678UVW
Discount: XYZ9876ABC
Coupon: 123ABC5678
```

The script tries patterns in order of specificity and stops at the first match to minimize false positives.

To customize the pattern, edit the `extract_promo_code()` function in `extract_promo_codes.py`.

---

## Recipient Email Intelligence

The script intelligently determines which email address to save for each code:

1. **Primary**: Uses the **To** email if it's not the IMAP account
2. **Fallback**: Uses the **From** email (sender) if To is the IMAP account
3. **Skips**: If neither To nor From can be determined

This is particularly useful for promotional emails, which are typically sent **to your account** but the sender's email is more relevant than your own.

**Example:**
- Email sent to: `yourname@gmail.com`
- Email from: `promo@zalando.com`
- **Saved email**: `promo@zalando.com` (sender, not recipient)

---

## Advanced Configuration

### Custom Mailbox Folders

Different email providers use different folder names:

| Provider | Spam Folder | Inbox |
|----------|-------------|-------|
| Gmail | `[Gmail]/Spam` | `INBOX` |
| Outlook | `Junk` | `INBOX` |
| Yahoo | `Bulk Mail` | `INBOX` |
| iCloud | `Junk` | `INBOX` |

### Processing Speed

The script includes a 0.1-second delay between emails to avoid rate limiting. Adjust in `extract_promo_codes.py`:
```python
time.sleep(0.1)  # Reduce for faster processing (may trigger rate limits)
```

### Automatic Reconnection

The script automatically reconnects every 50 messages to prevent timeout issues. Modify this threshold:
```python
if processed > 0 and processed % 50 == 0:
```

---

## Troubleshooting

### "Too many simultaneous connections"
- The script automatically waits 30 seconds and retries
- Ensure no other email clients are connected to the same account

### "Invalid credentials"
- Gmail with 2FA: Use an App Password, not your regular password
- Check if IMAP is enabled in your email account settings
- For Gmail: Enable [Less secure app access](https://myaccount.google.com/lesssecureapps) (if 2FA not used)

### "No codes found"
- Verify the subject keyword matches your emails
- Check the date range includes your target emails
- Ensure emails are in the specified folder
- Review the code pattern matches your email format

### "Connection timeout"
- The script reconnects every 50 messages automatically
- Check your internet connection
- Try reducing the number of messages in one session

### "Codes found but not saved"
- If codes are found but not in CSV, check the recipient email extraction
- Verify both To and From headers are present in emails
- Check file permissions for writing to `codes.csv`

---

## Code Quality

- **Type hints** for better code maintainability
- **Comprehensive docstrings** for all functions
- **Error handling** at every step
- **Input validation** before processing
- **CSV validation** to prevent empty/null entries

---

## Performance

- **Bulk Processing**: Process hundreds of emails efficiently
- **Rate Limiting**: Automatic delays to respect server limits
- **Auto-Reconnection**: Handles connection drops gracefully
- **Memory Efficient**: Streams emails instead of loading all at once

---

## License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

---

## Disclaimer

This tool is for personal use and automation of your own email accounts. Always ensure you have the necessary permissions to access and process emails. The developers are not responsible for any misuse of this tool.

---

<div align="center">
  <sub>© 2026 Zalando -20% Promo Code Extractor. Made by Pearl Solutions Group</sub>
</div>
