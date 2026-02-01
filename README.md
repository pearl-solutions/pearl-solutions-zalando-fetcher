<div align="center">
  <img src="https://github.com/Pearl-Solutions/.github/blob/main/Pearl_Solutions__Tavola_disegno_1-02.png?raw=true" alt="Pearl Solutions Banner" />
</div>

<div align="center">
  <h1>Zalando -20% Code Extractor</h1>
  <p>
    <strong>Automated Zalando -20% code extraction from email</strong><br>
    Streamline your workflow by automatically extracting Zalando -20% codes from your inbox or spam folder.
  </p>
</div>

---

## Overview

**Email Code Extractor** is a Python-based automation tool that searches through your email folders (like spam) to find and extract reduction codes. Perfect for managing multiple accounts or bulk processing emails.

**Key Features:**
- **Fast bulk processing** of reduction emails
- **Smart pattern matching** for code extraction
- **CSV export** with timestamps
- **Auto-reconnection** to handle connection timeouts
- **Input validation** for safe configuration
- **IMAP compatible** with Gmail, Outlook, and more
- **Interactive CLI** with progress tracking

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

2. **Install dependencies**
   ```bash
   pip install -r requirements.txt
   ```
   *Note: This project uses only Python standard library, so no external packages are required.*

---

## Usage

### Basic Usage

Run the script and follow the interactive prompts:

```bash
python main.py
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

### Example Session

```
=== Email Code Extractor Configuration ===

IMAP Server (default: imap.gmail.com): 
Email address: yourname@gmail.com
Password (input hidden): 
Start date (YYYY-MM-DD, e.g., 2026-01-27): 2026-01-15
Subject keyword to search (default: '20%'): 
Mailbox folder (default: [Gmail]/Spam): 

🔄 Connecting to email server...
📂 Selecting mailbox: [Gmail]/Spam
📧 47 messages found with '20%' in subject.

[0] Processing: Get 20% off your next purchase...
✅ Code found: ABC1234XYZ for customer@example.com
[10] Processing: Special 20% discount inside...
✅ Code found: DEF5678UVW for user@example.com
...
```

---

## Output

The extracted codes are saved to `codes.csv` with the following format:

```csv
email,code,timestamp
customer@example.com,ABC1234XYZ,2026-01-27 14:32:15
user@example.com,DEF5678UVW,2026-01-27 14:32:28
```

---

## Code Pattern

The script searches for codes matching this pattern:
```html
<font>XXXXXXXXXX</font>
```
Where `XXXXXXXXXX` is a 10-character alphanumeric code (A-Z, 0-9).

To modify the pattern, edit the regex in `main.py`:
```python
match = re.search(r"<font[^>]*>([A-Z0-9]{10})</font>", body)
```

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

The script includes a 0.1-second delay between emails to avoid rate limiting. Adjust in `main.py`:
```python
time.sleep(0.1)  # Reduce for faster processing (may trigger rate limits)
```

---

## Troubleshooting

### "Too many simultaneous connections"
- The script automatically waits 30 seconds and retries
- Ensure no other email clients are connected

### "Invalid credentials"
- Gmail with 2FA: Use an App Password, not your regular password
- Check if IMAP is enabled in your email settings

### No codes found
- Verify the subject keyword matches your emails
- Check the date range includes your target emails
- Ensure emails are in the specified folder

### Connection timeout
- The script reconnects every 50 messages automatically
- Check your internet connection

---

## License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

---

## Disclaimer

This tool is for personal use and automation of your own email accounts. Always ensure you have the necessary permissions to access and process emails. The developers are not responsible for any misuse of this tool.

---

<div align="center">
  <sub>© 2026 Zalando -20% Code Extractor. Made by Pearl Solutions Group</sub>
</div>
