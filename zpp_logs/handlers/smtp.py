from .base import BaseHandler
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from email.mime.base import MIMEBase
from email import encoders


class SMTPHandler(BaseHandler):
    def __init__(self, level, formatter, filters=None, host=None, port=None, username=None, password=None, fromaddr=None, toaddrs=None, cc=None, bcc=None, subject=None, ops='>=', async_mode=False, insecure=False, attachments=None): # ops moved to end
        super().__init__(level=level, formatter=formatter, filters=filters, ops=ops, async_mode=async_mode)
        self.host = host
        self.port = port
        self.username = username
        self.password = password
        self.fromaddr = fromaddr
        self.toaddrs = toaddrs
        self.cc = cc if cc else []
        self.bcc = bcc if bcc else []
        self.subject_template_str = subject
        self.insecure = insecure
        self.attachments = attachments if attachments else []

    def _emit_sync(self, record):
        modified_record = self.formatter.apply_rules(record)
        if self.should_handle(modified_record):
            subject = self.jinja_env.from_string(self.subject_template_str).render(modified_record)

            msg = MIMEMultipart()
            msg['Subject'] = subject
            msg['From'] = self.fromaddr
            msg['To'] = ", ".join(self.toaddrs)

            # Handle CC and BCC
            if self.cc:
                msg['Cc'] = ", ".join(self.cc)
            if self.bcc:
                msg['Bcc'] = ", ".join(self.bcc)

            # Handle the body (HTML content)
            body = modified_record.get('msg', '')
            msg.attach(MIMEText(body, 'html'))

            # Attach any files
            for attachment in self.attachments:
                try:
                    with open(attachment, 'rb') as attach_file:
                        attach_obj = MIMEBase('application', 'octet-stream')
                        attach_obj.set_payload(attach_file.read())
                        encoders.encode_base64(attach_obj)
                        attach_obj.add_header('Content-Disposition', f'attachment; filename={attachment}')
                        msg.attach(attach_obj)
                except Exception as e:
                    print(f"[SMTPHandler] Failed to attach file {attachment}: {e}")

            try:
                with smtplib.SMTP(self.host, self.port) as server:
                    if not self.insecure:
                        server.starttls()
                        server.ehlo()

                    if self.username and self.password:
                        server.login(self.username, self.password)
                    #server.send_message(msg)
                    server.sendmail(self.fromaddr, self.toaddrs + self.cc + self.bcc, msg.as_string())
                #print(f"[SMTPHandler] Email sent to {self.toaddrs} with subject: {subject}")
            except Exception as e:
                print(f"[SMTPHandler] Failed to send email: {e}")
