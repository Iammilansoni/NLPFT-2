"""
Quick SMTP diagnostic — run this directly on your machine (not inside Docker):
  cd Backend
  python test_smtp.py

It will tell you exactly WHERE the Gmail connection fails.
"""
import smtplib
import ssl
import socket
import os
from dotenv import load_dotenv

load_dotenv()

SMTP_HOST = os.getenv("SMTP_HOST", "smtp.gmail.com")
SMTP_PORT = int(os.getenv("SMTP_PORT", "587"))
SMTP_USER = os.getenv("SMTP_USER", "")
SMTP_PASSWORD = os.getenv("SMTP_PASSWORD", "")

print(f"\n{'='*55}")
print("NLPForge — SMTP Diagnostic")
print(f"{'='*55}")
print(f"Host     : {SMTP_HOST}")
print(f"Port     : {SMTP_PORT}")
print(f"User     : {SMTP_USER}")
print(f"Password : {'*' * len(SMTP_PASSWORD)} ({len(SMTP_PASSWORD)} chars)")
print()

# Step 1: DNS resolution
print("Step 1/4 — DNS lookup...")
try:
    ip = socket.gethostbyname(SMTP_HOST)
    print(f"  ✅ Resolved {SMTP_HOST} → {ip}")
except Exception as e:
    print(f"  ❌ DNS FAILED: {e}")
    print("\n  Fix: No internet access from this machine/container.")
    exit(1)

# Step 2: TCP connection
print(f"Step 2/4 — TCP connect to port {SMTP_PORT}...")
try:
    sock = socket.create_connection((SMTP_HOST, SMTP_PORT), timeout=10)
    sock.close()
    print(f"  ✅ TCP connection to {SMTP_HOST}:{SMTP_PORT} OK")
except Exception as e:
    print(f"  ❌ TCP FAILED: {e}")
    print(f"\n  Fix: Port {SMTP_PORT} is BLOCKED by your ISP/firewall.")
    if SMTP_PORT == 587:
        print("  Try: Change SMTP_PORT=465 in .env and run again.")
    elif SMTP_PORT == 465:
        print("  Try: Change SMTP_PORT=587 in .env and run again.")
    print("  Alternative: Use mailjet/sendgrid SMTP relay on port 25/2525.")
    exit(1)

# Step 3: Auth handshake
print(f"Step 3/4 — Auth handshake (port {SMTP_PORT})...")
try:
    if SMTP_PORT == 465:
        import ssl
        server = smtplib.SMTP_SSL(SMTP_HOST, SMTP_PORT, timeout=15)
    else:
        server = smtplib.SMTP(SMTP_HOST, SMTP_PORT, timeout=15)
        server.ehlo()
        server.starttls()
        server.ehlo()
    print(f"  ✅ Connection handshake OK (port {SMTP_PORT})")
except Exception as e:
    print(f"  ❌ Handshake FAILED: {e}")
    exit(1)

# Step 4: Login
print("Step 4/4 — Gmail login...")
try:
    server.login(SMTP_USER, SMTP_PASSWORD)
    print("  ✅ Login OK — credentials are correct!")
    server.quit()
except smtplib.SMTPAuthenticationError as e:
    print(f"  ❌ AUTH FAILED: {e}")
    print()
    print("  The Gmail App Password is WRONG or not set up correctly.")
    print("  Fix: Go to https://myaccount.google.com/apppasswords")
    print("  Create a new App Password for 'Mail' and update SMTP_PASSWORD in .env")
    exit(1)
except Exception as e:
    print(f"  ❌ Login error: {e}")
    exit(1)

print()
print("✅ All checks passed — SMTP is working!")
print("If emails still aren't arriving, check your SPAM folder.")
