from .base import BaseHandler
import sys

class ConsoleHandler(BaseHandler):
    def __init__(self, level, formatter, filters=None, output='sys.stdout', ops='>=', async_mode=False): # ops moved to end
        super().__init__(level=level, formatter=formatter, filters=filters, ops=ops, async_mode=async_mode)
        if isinstance(output, str):
            self.stream = sys.stdout if output == 'sys.stdout' else sys.stderr
        else:
            self.stream = output

    def _emit_sync(self, record):
        modified_record = self.formatter.apply_rules(record)
        if self.should_handle(modified_record):
            formatted_message = self.formatter.render(modified_record)
            self.stream.write(str(formatted_message) + '\n')
            self.stream.flush()

    def expects_formatted_string(self):
        return True