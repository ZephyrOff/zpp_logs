import time
import pytest
from zpp_logs.handlers.console import ConsoleHandler
from zpp_logs.handlers.file import FileHandler
from zpp_logs.core import CustomFormatter, Logger
from datetime import datetime

def test_async_handler_does_not_block(monkeypatch):
    # Mock the actual writing to avoid printing to console during tests
    # and to simulate a slow operation.
    def slow_emit(self, record):
        time.sleep(0.2)
    
    monkeypatch.setattr(ConsoleHandler, '_emit_sync', slow_emit)
    
    formatter = CustomFormatter(format_str="{{ msg }}")
    # Create an async handler
    handler = ConsoleHandler(level='INFO', formatter=formatter, async_mode=True)
    logger = Logger(name='async_test', handlers=[handler])
    
    start_time = time.time()
    logger.info("This should not block", timestamp=datetime.now())
    end_time = time.time()
    
    # The logger call should return almost immediately
    assert end_time - start_time < 0.1
    
    # Stop the handler to ensure the log is processed before the test ends
    handler.stop()

def test_async_log_is_processed(tmp_path):
    log_file = tmp_path / "async_test.log"
    
    formatter = CustomFormatter(format_str="{{ msg }}")
    handler = FileHandler(level='INFO', formatter=formatter, filename=str(log_file), async_mode=True)
    logger = Logger(name='async_file_test', handlers=[handler])
    
    logger.info("test message", timestamp=datetime.now())
    
    # Give the worker thread some time to process the log
    handler.stop() # This will wait for the queue to be empty
    
    assert log_file.read_text() == 'test message\n'
