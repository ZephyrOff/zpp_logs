import pytest
from tests.models import LogTestModel

@pytest.fixture
def simple_formatter_config():
    return {
        'formatters': {
            'simple': {
                'format': '{{ levelname }}:{{ msg }}'
            }
        }
    }

@pytest.fixture
def full_config_dict():
    return {
        'formatters': {
            'standard': {
                'format': '{{ levelname }} - {{ msg }}',
                'rules': {
                    'levelname == \'CRITICAL\'': {
                        'levelname': 'CRITICAL_RULE'
                    },
                    'func_test() == \'value\'': {
                        'msg': 'MSG_RULE'
                    }
                }
            }
        },
        'handlers': {
            'console': {
                'class': 'zpp_logs.ConsoleHandler',
                'level': 'INFO',
                'formatter': 'standard'
            },
            'file': {
                'class': 'zpp_logs.FileHandler',
                'level': 'DEBUG',
                'formatter': 'standard',
                'filename': 'test.log'
            },
            'db': {
                'class': 'zpp_logs.DatabaseHandler',
                'level': 'INFO',
                'formatter': 'standard',
                'connector': {
                    'engine': 'sqlite',
                    'filename': ':memory:'
                },
                'model': 'tests.models.LogTestModel'
            }
        },
        'loggers': {
            'root': {
                'handlers': ['console', 'file']
            },
            'db_logger': {
                'handlers': ['db']
            }
        }
    }

@pytest.fixture
def create_config_file(tmp_path, full_config_dict):
    import yaml
    config_path = tmp_path / "config.yaml"
    with open(config_path, 'w') as f:
        yaml.dump(full_config_dict, f)
    return str(config_path)
