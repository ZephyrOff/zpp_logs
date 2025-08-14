# --- Log Levels ---
CRITICAL = 50
ERROR = 40
WARNING = 30
SUCCESS = 25  # New level
INFO = 20
DEBUG = 10
NOTSET = 0

_level_to_name = {
    CRITICAL: 'CRITICAL',
    ERROR: 'ERROR',
    WARNING: 'WARNING',
    SUCCESS: 'SUCCESS',
    INFO: 'INFO',
    DEBUG: 'DEBUG',
    NOTSET: 'NOTSET',
}

_name_to_level = {name: level for level, name in _level_to_name.items()}
