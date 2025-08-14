import sys
from unittest.mock import MagicMock, patch
from zpp_logs.handlers.console import ConsoleHandler
from zpp_logs.handlers.file import FileHandler
from zpp_logs.handlers.database import DatabaseHandler
from zpp_logs.handlers.smtp import SMTPHandler
from zpp_logs.handlers.resend import ResendHandler
from zpp_logs.core import CustomFormatter
from .conftest import LogTestModel
from sqlalchemy import create_engine, text
from datetime import datetime

def test_console_handler_stdout(monkeypatch):
    mock_stdout = MagicMock()
    monkeypatch.setattr(sys, 'stdout', mock_stdout)
    formatter = CustomFormatter(format_str="{{ msg }}")
    handler = ConsoleHandler(level='INFO', formatter=formatter)
    handler.emit({'levelno': 20, 'levelname': 'INFO', 'msg': 'test', 'timestamp': datetime.now()})
    # The actual output includes a newline character
    mock_stdout.write.assert_called_with('test\n')

def test_file_handler_creation(tmp_path):
    log_file = tmp_path / "test.log"
    formatter = CustomFormatter(format_str="{{ msg }}")
    handler = FileHandler(level='INFO', formatter=formatter, filename=str(log_file))
    handler.emit({'levelno': 20, 'levelname': 'INFO', 'msg': 'test', 'timestamp': datetime.now()})
    handler.stop()  # Close the file stream to ensure write is flushed
    assert log_file.read_text() == 'test\n'

def test_file_handler_rotation(tmp_path):
    log_file = tmp_path / "test_rotation.log"
    formatter = CustomFormatter(format_str="{{ msg }}")
    # Small maxBytes to trigger rotation easily
    handler = FileHandler(level='INFO', formatter=formatter, filename=str(log_file), maxBytes=10, backupCount=2)
    handler.emit({'levelno': 20, 'levelname': 'INFO', 'msg': 'message1', 'timestamp': datetime.now()})
    handler.emit({'levelno': 20, 'levelname': 'INFO', 'msg': 'message2', 'timestamp': datetime.now()})
    handler.emit({'levelno': 20, 'levelname': 'INFO', 'msg': 'message3', 'timestamp': datetime.now()})
    handler.stop()
    assert (tmp_path / "test_rotation.log.1").exists()
    assert (tmp_path / "test_rotation.log").read_text() == 'message3\n'

def test_database_handler_model(tmp_path):
    db_file = tmp_path / "test.db"
    formatter = CustomFormatter(format_str="{{ msg }}")
    handler = DatabaseHandler(
        level='INFO',
        formatter=formatter,
        connector={'engine': 'sqlite', 'filename': str(db_file)},
        model=LogTestModel
    )
    record = {'levelno': 20, 'levelname': 'INFO', 'msg': 'db test', 'logger_name': 'test_db', 'timestamp': datetime.now()}
    handler.emit(record)
    handler.stop()

    engine = create_engine(f"sqlite:///{db_file}")
    with engine.connect() as conn:
        result = conn.execute(text("SELECT message FROM test_logs")).scalar_one()
        assert result == 'db test'

    @patch('smtplib.SMTP')
    def test_smtp_handler(mock_smtp):
        # Configure the mock to act as a context manager
        mock_smtp.return_value.__enter__.return_value = mock_smtp.return_value
        mock_smtp.return_value.__exit__.return_value = False # Don't suppress exceptions

        formatter = CustomFormatter(format_str="{{ msg }}")
        handler = SMTPHandler(
            level='ERROR',
            formatter=formatter,
            host='smtp.test.com',
            port=587,
            username='user',
            password='password',
            fromaddr='from@test.com',
            toaddrs=['to@test.com'],
            subject='Test'
        )
        handler.emit({'levelno': 40, 'levelname': 'ERROR', 'msg': 'smtp test', 'timestamp': datetime.now()})
        
        instance = mock_smtp.return_value
        instance.send_message.assert_called_once()

@patch('requests.post')
def test_resend_handler(mock_post):
    formatter = CustomFormatter(format_str="{{ msg }}")
    handler = ResendHandler(
        level='ERROR',
        formatter=formatter,
        api_key='re_test',
        fromaddr='from@test.com',
        to=['to@test.com'],
        subject='Test'
    )
    handler.emit({'levelno': 40, 'levelname': 'ERROR', 'msg': 'resend test', 'timestamp': datetime.now()})
    mock_post.assert_called_once()
    call_args = mock_post.call_args[1]
    assert call_args['json']['html'] == 'resend test'
