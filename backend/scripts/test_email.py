"""Check your SMTP settings:  python scripts/test_email.py you@example.com"""
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
from app.services.notifications import send_mail

to = sys.argv[1] if len(sys.argv) > 1 else sys.exit("usage: python scripts/test_email.py you@example.com")
print("Sent!" if send_mail(to, "Campus Awaaz test email", "If you can read this, class reminder emails will work.") else "Failed - read the message above.")
