from .base import BaseHandler
import requests

class ResendHandler(BaseHandler):
    def __init__(self, level, formatter, filters=None, api_key=None, fromaddr=None, to=None, subject=None, ops='>=', async_mode=False): # ops moved to end
        super().__init__(level=level, formatter=formatter, filters=filters, ops=ops, async_mode=async_mode)
        self.api_key = api_key
        self.fromaddr = fromaddr
        self.to = to
        self.subject_template_str = subject


    def _emit_sync(self, record):
        modified_record = self.formatter.apply_rules(record)
        if self.should_handle(modified_record):
            subject = self.jinja_env.from_string(self.subject_template_str).render(modified_record)
            
            headers = {
                "Authorization": f"Bearer {self.api_key}",
                "Content-Type": "application/json"
            }
            data = {
                "from": self.fromaddr,
                "to": self.to,
                "subject": subject,
                "html": modified_record['msg'] # Sending raw message as HTML for simplicity
            }

            try:
                response = requests.post("https://api.resend.com/emails", headers=headers, json=data)
                response.raise_for_status() # Raise HTTPError for bad responses (4xx or 5xx)
                print(f"[ResendHandler] Email sent via Resend API. Status: {response.status_code}")
            except requests.exceptions.RequestException as e:
                print(f"[ResendHandler] Failed to send email via Resend API: {e}")