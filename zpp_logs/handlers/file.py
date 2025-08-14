from .base import BaseHandler
import os


class FileHandler(BaseHandler):
    def __init__(self, level, formatter, filters=None, filename=None, maxBytes=0, backupCount=0, ops='>=', async_mode=False): # ops moved to end
        super().__init__(level=level, formatter=formatter, filters=filters, ops=ops, async_mode=async_mode)
        self.filename_template_str = filename
        self.maxBytes = maxBytes
        self.backupCount = backupCount
        self.stream = None
        self.current_filename = None

        self._open_file()

    def _get_rendered_filename(self):
        template = self.jinja_env.from_string(self.filename_template_str)
        return template.render()

    def _open_file(self):
        if self.stream:
            self.stream.close()
        
        self.current_filename = self._get_rendered_filename()
        os.makedirs(os.path.dirname(self.current_filename) or '.', exist_ok=True)
        self.stream = open(self.current_filename, 'a', encoding='utf-8')

    def _do_rollover(self):
        if self.stream:
            self.stream.close()
            self.stream = None

        if self.backupCount > 0: # Standard rotation (rename files)
            for i in range(self.backupCount - 1, 0, -1):
                sfn = f"{self.current_filename}.{i}"
                dfn = f"{self.current_filename}.{i + 1}"
                if os.path.exists(sfn):
                    if os.path.exists(dfn):
                        os.remove(dfn)
                    os.rename(sfn, dfn)
            dfn = f"{self.current_filename}.1"
            if os.path.exists(dfn):
                os.remove(dfn)
            os.rename(self.current_filename, dfn)
        elif self.maxBytes > 0 and self.backupCount == 0: # Circular logging (delete first line)
            try:
                with open(self.current_filename, 'r+', encoding='utf-8') as f:
                    lines = f.readlines()
                    if len(lines) > 1:
                        f.seek(0)
                        f.truncate(0) # Clear content
                        f.writelines(lines[1:]) # Write all but the first line
                    else:
                        f.seek(0)
                        f.truncate(0) # Clear if only one line
            except Exception as e:
                print(f"[FileHandler] Error during circular rollover: {e}")
        self._open_file()

    def _emit_sync(self, record):
        modified_record = self.formatter.apply_rules(record)
        if self.should_handle(modified_record):
            formatted_message = self.formatter.render(modified_record)
            if self.maxBytes > 0:
                current_size = os.path.getsize(self.current_filename) if os.path.exists(self.current_filename) else 0
                if current_size + len(formatted_message.encode('utf-8')) >= self.maxBytes:
                    self._do_rollover()
            self.stream.write(str(formatted_message) + '\n')
            self.stream.flush()

    def expects_formatted_string(self):
        return True