from .base import BaseHandler
import smtplib
from email.mime.text import MIMEText

class SMTPHandler(BaseHandler):
    def __init__(self, level, formatter, filters=None, host=None, port=None, username=None, password=None, fromaddr=None, toaddrs=None, subject=None, ops='>=', async_mode=False): # ops moved to end
        super().__init__(level=level, formatter=formatter, filters=filters, ops=ops, async_mode=async_mode)
        self.host = host
        self.port = port
        self.username = username
        self.password = password
        self.fromaddr = fromaddr
        self.toaddrs = toaddrs
        self.subject_template_str = subject

    def _emit_sync(self, record):
        modified_record = self.formatter.apply_rules(record)
        if self.should_handle(modified_record):
            subject = self.jinja_env.from_string(self.subject_template_str).render(modified_record)
            msg = MIMEText(modified_record['msg'])
            msg['Subject'] = subject
            msg['From'] = self.fromaddr
            msg['To'] = ", ".join(self.toaddrs)

            try:
                with smtplib.SMTP(self.host, self.port) as server:
                    server.starttls()
                    server.login(self.username, self.password)
                    server.send_message(msg)
                print(f"[SMTPHandler] Email sent to {self.toaddrs} with subject: {subject}")
            except Exception as e:
                print(f"[SMTPHandler] Failed to send email: {e}")