import operator
import queue
import threading
import traceback
import atexit
from ..jinja_utils import _shared_jinja_env
from ..levels import _name_to_level, NOTSET

# --- Base Handler Class ---
class BaseHandler:
    _ops_map = {
        '>': operator.gt, '<': operator.lt,
        '>=': operator.ge, '<=': operator.le,
        '==': operator.eq, '!=': operator.ne,
    }

    def __init__(self, level, formatter, filters=None, ops=">=", async_mode=False):
        self.level = _name_to_level.get(level.split('.')[-1], NOTSET) if isinstance(level, str) else level
        self.op = self._ops_map.get(ops)
        self.formatter = formatter
        self.filters = filters if filters is not None else []
        self.jinja_env = _shared_jinja_env
        self.async_mode = async_mode

        if self.async_mode:
            self.queue = queue.Queue()
            self.thread = threading.Thread(target=self._worker, daemon=True)
            self.thread.start()
            atexit.register(self.stop)

    def _worker(self):
        while True:
            try:
                record = self.queue.get()
                if record is None:  # Sentinel
                    break
                self._emit_sync(record)
            except Exception:
                print("Exception in async handler worker:")
                traceback.print_exc()
            finally:
                self.queue.task_done()

    def emit(self, record):
        if self.async_mode:
            self.queue.put(record)
        else:
            self._emit_sync(record)

    def _emit_sync(self, record):
        raise NotImplementedError("Subclasses must implement _emit_sync method")

    def stop(self):
        if self.async_mode:
            self.queue.put(None)
            self.thread.join()

    def _check_filters(self, record):
        for filter_expression_str in self.filters:
            filter_eval_template = self.jinja_env.from_string(f"{{{{ {filter_expression_str} }}}}")
            match_str = filter_eval_template.render(record).strip().lower()
            if match_str == 'false':
                return False
        return True

    def should_handle(self, record):
        level_check = self.op(record['levelno'], self.level)
        if not level_check:
            return False
        return self._check_filters(record)

    def expects_formatted_string(self):
        return False

    # --- Dynamic Modification Methods for Handlers ---
    def set_formatter(self, formatter_instance):
        self.formatter = formatter_instance

    def set_level(self, level):
        self.level = _name_to_level.get(level.split('.')[-1], NOTSET) if isinstance(level, str) else level

    def set_ops(self, ops):
        self.op = self._ops_map.get(ops)

    def add_filter(self, filter_expression_str):
        if filter_expression_str not in self.filters:
            self.filters.append(filter_expression_str)

    def remove_filter(self, filter_expression_str):
        if filter_expression_str in self.filters:
            self.filters.remove(filter_expression_str)