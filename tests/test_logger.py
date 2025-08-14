import pytest
from zpp_logs.core import LogManager, Logger, CustomFormatter
from zpp_logs.handlers.console import ConsoleHandler

def test_log_manager_from_config(create_config_file):
    manager = LogManager(create_config_file)
    assert 'root' in manager._loggers
    assert 'console' in manager._handlers
    assert 'standard' in manager._formatters
    
    logger = manager.get_logger('root')
    assert isinstance(logger, Logger)
    assert len(logger.handlers) == 2

def test_programmatic_logger():
    formatter = CustomFormatter(format_str="{{ msg }}")
    handler = ConsoleHandler(level='INFO', formatter=formatter)
    logger = Logger(name='prog_logger', handlers=[handler])
    
    assert logger.name == 'prog_logger'
    assert len(logger.handlers) == 1

def test_dynamic_add_remove_handler():
    formatter = CustomFormatter(format_str="{{ msg }}")
    handler1 = ConsoleHandler(level='INFO', formatter=formatter)
    handler2 = ConsoleHandler(level='DEBUG', formatter=formatter)
    logger = Logger(name='test', handlers=[handler1])
    
    assert len(logger.handlers) == 1
    logger.add_handler(handler2)
    assert len(logger.handlers) == 2
    logger.remove_handler(handler1)
    assert len(logger.handlers) == 1
    assert logger.handlers[0].level == 10  # DEBUG

def test_get_logger_fallback(create_config_file):
    """Tests that getting a non-existent logger falls back to root."""
    manager = LogManager(create_config_file)
    
    # This logger is not defined in the config, so it should get the root logger.
    undefined_logger = manager.get_logger('undefined_logger')
    root_logger = manager.get_logger('root')
    
    assert undefined_logger is root_logger
