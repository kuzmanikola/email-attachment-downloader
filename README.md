# 📧 Email Attachment Downloader

A modern web application to download PDF attachments from Gmail using IMAP. Features a beautiful, responsive UI and real-time progress tracking.

![Python](https://img.shields.io/badge/Python-3.7+-blue.svg)
![Flask](https://img.shields.io/badge/Flask-3.0-green.svg)

## ✨ Features

- 🎨 Modern, responsive web interface
- 📊 Real-time progress tracking
- 📥 Automatic PDF attachment download
- 🔍 Filter emails by sender and date range
- 🔒 Secure connection using Gmail App Passwords
- 📱 Mobile-friendly design

## 🚀 Quick Start

### Prerequisites

- Python 3.7 or higher
- Gmail account with 2-Step Verification enabled
- Gmail App Password ([Generate one here](https://myaccount.google.com/apppasswords))

### Installation

1. Clone or download this repository

2. Install dependencies:
```bash
pip install -r requirements.txt
```

### Running the Application

1. Start the Flask server:
```bash
python app.py
```

2. Open your browser and navigate to:
```
http://localhost:9090
```

3. Fill in the form:
   - **Your Gmail Address**: Your full Gmail email address
   - **App Password**: Your 16-character app password (not your regular Gmail password)
   - **Sender Email**: Email address of the sender whose attachments you want to download
   - **Start Date**: Beginning of the date range
   - **End Date**: End of the date range

4. Click "Start Download" and watch the progress in real-time!

## 🔐 Setting Up Gmail App Password

1. Enable [2-Step Verification](https://support.google.com/accounts/answer/185833) on your Google Account
2. Go to [App Passwords](https://myaccount.google.com/apppasswords)
3. Select "Mail" and your device
4. Click "Generate"
5. Copy the 16-character password and use it in the application

## 📁 File Structure

```
email-puller/
├── app.py                      # Flask backend application
├── connect_imap.py             # Original CLI version
├── requirements.txt            # Python dependencies
├── templates/
│   └── index.html             # Web UI template
├── static/
│   ├── style.css              # Styling
│   └── script.js              # Frontend JavaScript
└── downloaded_attachments/     # Downloaded PDFs (created automatically)
```

## 🛠️ How It Works

1. **Connection**: The app connects to Gmail's IMAP server using SSL/TLS
2. **Search**: Searches for emails from the specified sender within the date range
3. **Processing**: Processes each email and extracts PDF attachments
4. **Download**: Saves PDFs to the `downloaded_attachments` folder
5. **Display**: Shows downloaded files with metadata in the web interface

## 📝 Original CLI Version

The original command-line version is still available in `connect_imap.py`. You can run it with:

```bash
python connect_imap.py
```

## 🔧 Configuration

You can modify these settings in `app.py`:

- `IMAP_SERVER`: IMAP server address (default: `imap.gmail.com`)
- `IMAP_PORT`: IMAP port (default: `993`)
- `DOWNLOAD_DIR`: Download directory name (default: `downloaded_attachments`)

## 🌐 Accessing from Other Devices

The server runs on `0.0.0.0:9090` by default, making it accessible from other devices on your network:

1. Find your computer's IP address:
   - **Mac/Linux**: `ifconfig` or `ip addr`
   - **Windows**: `ipconfig`

2. On another device, navigate to:
   ```
   http://YOUR_IP_ADDRESS:9090
   ```

## 🐛 Troubleshooting

### "IMAP login failed"
- Ensure 2-Step Verification is enabled
- Make sure you're using an App Password, not your regular password
- Check that the email address is correct

### "No messages found"
- Verify the sender email address is correct
- Check the date range includes messages
- Ensure the emails are in your INBOX

### Port already in use
If port 9090 is already in use, you can change it in `app.py`:
```python
app.run(debug=True, host='0.0.0.0', port=9091)  # Change to any available port
```

## 📄 License

This project is open source and available for personal and educational use.

## 🤝 Contributing

Feel free to fork, modify, and improve this application!

## ⚠️ Security Notes

- Never commit your email address or app password to version control
- Consider using environment variables for sensitive data:
  ```bash
  export EMAIL_ADDRESS="your.email@gmail.com"
  export APP_PASSWORD="your-app-password"
  ```
- The app stores credentials only in memory during execution
- Downloaded files are saved locally and not shared

## 💡 Tips

- Set default date ranges to avoid typing every time
- Check the `downloaded_attachments` folder after each run
- Files with the same name get automatically numbered (e.g., `file.pdf`, `file_1.pdf`)
- The app only downloads PDF attachments; other file types are ignored

---

Story behind how the app was created: It started as a problem I faced every last day of the month - manually downloading PDF attachments from emails for my mom’s company. I got the idea to automate it. Made with ❤️ for my mom, to make email attachment management easier.

