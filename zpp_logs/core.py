import yaml
from datetime import datetime

from .handlers.console import ConsoleHandler
from .handlers.database import DatabaseHandler
from .handlers.file import FileHandler
from .handlers.resend import ResendHandler
from .handlers.smtp import SMTPHandler
from .handlers.webhook import WebhookHandler

from .levels import CRITICAL, ERROR, WARNING, SUCCESS, INFO, DEBUG, NOTSET, _level_to_name, _name_to_level
from .jinja_utils import _shared_jinja_env


# --- Handlers ---
_handler_class_map = {
    'zpp_logs.ConsoleHandler': ConsoleHandler,
    'zpp_logs.FileHandler': FileHandler,
    'zpp_logs.DatabaseHandler': DatabaseHandler,
    'zpp_logs.SMTPHandler': SMTPHandler,
    'zpp_logs.ResendHandler': ResendHandler,
    'zpp_logs.WebhookHandler': WebhookHandler,
}

# --- Core Components ---
class CustomFormatter:
    def __init__(self, format_str):
        self.format_str = format_str
        self.rules = {}
        
        self.env = _shared_jinja_env

        self.template = self.env.from_string(self.format_str)

    def apply_rules(self, record):
        render_context = record.copy()
        function_overrides = {}

        # Default rule
        if '__default__' in self.rules:
            default_rule_body = self.rules['__default__']
            for key, template_str in default_rule_body.items():
                rule_template = self.env.from_string(template_str)
                if key.endswith('()'):
                    func_name = key[:-2]
                    rendered_value = rule_template.render(render_context)
                    function_overrides[func_name] = lambda v=rendered_value: v
                else:
                    render_context[key] = rule_template.render(render_context)

        # Other rules
        for condition_str, rule_body in self.rules.items():
            if condition_str == '__default__':
                continue

            condition_eval_template = self.env.from_string(f"{{{{ {condition_str} }}}}")
            match_str = condition_eval_template.render(record).strip().lower()
            match = (match_str == 'true')

            if match:
                for key, template_str in rule_body.items():
                    rule_template = self.env.from_string(template_str)
                    if key.endswith('()'):
                        func_name = key[:-2]
                        rendered_value = rule_template.render(render_context)
                        function_overrides[func_name] = lambda v=rendered_value: v
                    else:
                        render_context[key] = rule_template.render(render_context)
        
        render_context.update(function_overrides)
        return render_context

    def format(self, record):
        modified_record = self.apply_rules(record)
        return self.render(modified_record)

    def render(self, record):
        return self.template.render(record)

    # --- Dynamic Modification Methods for Formatter --
    def set_rule(self, condition_str, rule_body):
        self.rules[condition_str] = rule_body

    def delete_rule(self, condition_str):
        if condition_str in self.rules:
            del self.rules[condition_str]

class Logger:
    def __init__(self, name, handlers):
        self.name = name
        self.handlers = handlers

    def _log(self, level, msg, *args, **kwargs):
        if args:
            msg = msg % args
        
        record = {
            'name': self.name,
            'levelno': level,
            'levelname': _level_to_name[level],
            'msg': msg,
            'timestamp': datetime.now(),
            **kwargs
        }
        
        for handler in self.handlers:
            handler.emit(record)

    def debug(self, msg, *args, **kwargs):
        self._log(DEBUG, msg, *args, **kwargs)

    def info(self, msg, *args, **kwargs):
        self._log(INFO, msg, *args, **kwargs)

    def success(self, msg, *args, **kwargs):
        self._log(SUCCESS, msg, *args, **kwargs)

    def warning(self, msg, *args, **kwargs):
        self._log(WARNING, msg, *args, **kwargs)

    def error(self, msg, *args, **kwargs):
        self._log(ERROR, msg, *args, **kwargs)

    def critical(self, msg, *args, **kwargs):
        self._log(CRITICAL, msg, *args, **kwargs)

    # --- Dynamic Modification Methods for Logger ---
    def add_handler(self, handler_instance):
        if handler_instance not in self.handlers:
            self.handlers.append(handler_instance)

    def remove_handler(self, handler_instance):
        if handler_instance in self.handlers:
            self.handlers.remove(handler_instance)

class LogManager:
    def __init__(self, config_file):
        with open(config_file, 'r') as f:
            self.config = yaml.safe_load(f)
        
        self._formatters = self._create_formatters()
        self._handlers = self._create_handlers()
        self._loggers = {}
        self.default_logger = self.get_logger('root') # Set default logger

    def _create_formatters(self):
        formatters = {}
        for name, config in self.config.get('formatters', {}).items():
            # Pass format_str directly to CustomFormatter
            formatter_instance = CustomFormatter(config['format'])
            # Set rules using set_rule method
            for rule_condition, rule_body in config.get('rules', {}).items():
                formatter_instance.set_rule(rule_condition, rule_body)
            formatters[name] = formatter_instance
        return formatters

    def _create_handlers(self):
        handlers = {}
        for name, config in self.config.get('handlers', {}).items():
            if 'level' in config and '.' in config['level']:
                config['level'] = config['level'].split('.')[-1]
            
            handler_class = _handler_class_map.get(config['class'])
            if not handler_class:
                raise ValueError(f"Unknown handler class: {config['class']}")

            # Extract common handler args
            level = config.get('level')
            ops = config.get('ops', '>=')
            formatter_name = config.get('formatter')
            formatter_instance = self._formatters.get(formatter_name)
            filters = config.get('filters', [])
            async_mode = config.get('async_mode', False) # Get the async flag

            # Extract specific handler args
            specific_args = {
                k: v for k, v in config.items() 
                if k not in ['class', 'level', 'ops', 'formatter', 'filters', 'async_mode']
            }
            
            # Instantiate the handler with all its arguments
            handlers[name] = handler_class(
                level=level, 
                formatter=formatter_instance, 
                filters=filters, 
                ops=ops,
                async_mode=async_mode, # Pass the async flag
                **specific_args
            )
        return handlers

    def get_logger(self, name):
        if name in self._loggers:
            return self._loggers[name]

        logger_config = self.config.get('loggers', {}).get(name)
        if not logger_config:
            if name != 'root' and 'root' in self.config.get('loggers', {}):
                return self.get_logger('root')
            raise ValueError(f"Logger '{name}' not found in configuration.")

        logger_handlers = [self._handlers[h_name] for h_name in logger_config.get('handlers', []) if h_name in self._handlers]
        
        logger = Logger(name, logger_handlers)
        self._loggers[name] = logger
        return logger

    