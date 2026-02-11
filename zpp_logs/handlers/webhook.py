from .base import BaseHandler
import requests
from requests.auth import HTTPBasicAuth
import urllib3

urllib3.disable_warnings()

class WebhookHandler(BaseHandler):
    def __init__(self, level, formatter, filters=None, ops='>=', async_mode=False, url=None, ssl_verify=True, data=None, bearer=None, basic=None, token=None):
        super().__init__(level=level, formatter=formatter, filters=filters, ops=ops, async_mode=async_mode)
        if url is None:
            raise ValueError("WebhookHandler requires a 'url' parameter.")
        self.url = url
        self.ssl_verify = ssl_verify
        self.data_template = data or {}
        self.bearer_token = bearer
        self.basic_auth = basic
        self.token = token

    def _render_value(self, value, record):
        """Recursively render values using Jinja."""
        
        if isinstance(value, dict):
            return {
                k: self._render_value(v, record)
                for k, v in value.items()
            }

        elif isinstance(value, list):
            return [
                self._render_value(item, record)
                for item in value
            ]

        elif isinstance(value, str):
            template = self.jinja_env.from_string(value)
            return template.render(record)

        else:
            # int, float, bool, None etc.
            return value

    def _render_payload(self, record):
        return self._render_value(self.data_template, record)

    def _emit_sync(self, record):
        """Prepares and sends the webhook."""
        modified_record = self.formatter.apply_rules(record)
        if self.should_handle(modified_record):
            
            # --- Prepare Authentication ---
            headers = {"Content-Type": "application/json"}
            auth = None
            if self.bearer_token:
                headers['Authorization'] = f"Bearer {self.bearer_token}"
            elif self.basic_auth and 'user' in self.basic_auth and 'pass' in self.basic_auth:
                auth = HTTPBasicAuth(self.basic_auth['user'], self.basic_auth['pass'])
            elif self.token:
                headers['X-Webhook-Token'] = self.token

            # --- Prepare Payload ---
            payload = self._render_payload(modified_record)

            # --- Send Request ---
            try:
                response = requests.post(
                    self.url,
                    headers=headers,
                    json=payload,
                    auth=auth,
                    verify=self.ssl_verify
                )
                response.raise_for_status() # Lève une exception pour les codes 4xx/5xx
                #print(f"[WebhookHandler] Successfully sent webhook to {self.url}. Status: {response.status_code}")
            except requests.exceptions.RequestException as e:
                print(f"[WebhookHandler] Failed to send webhook to {self.url}: {e}")

