from zpp_logs.core import CustomFormatter

def test_basic_formatting():
    formatter = CustomFormatter(format_str="{{ levelname }}:{{ msg }}")
    record = {'levelname': 'INFO', 'msg': 'test message'}
    # The format method applies rules and then renders the final string.
    # Here, we call apply_rules first to get the modified record, then render.
    modified_record = formatter.apply_rules(record)
    formatted = formatter.render(modified_record)
    assert formatted == "INFO:test message"

def test_default_rule():
    formatter = CustomFormatter(format_str="{{ levelname }}:{{ msg }}")
    formatter.set_rule('__default__', {'msg': 'default message'})
    record = {'levelname': 'INFO', 'msg': 'test message'}
    modified_record = formatter.apply_rules(record)
    formatted = formatter.render(modified_record)
    assert formatted == "INFO:default message"

def test_conditional_rule_match():
    formatter = CustomFormatter(format_str="{{ levelname }}:{{ msg }}")
    formatter.set_rule("levelname == 'INFO'", {'msg': 'info message'})
    record = {'levelname': 'INFO', 'msg': 'test message'}
    modified_record = formatter.apply_rules(record)
    formatted = formatter.render(modified_record)
    assert formatted == "INFO:info message"

def test_conditional_rule_no_match():
    formatter = CustomFormatter(format_str="{{ levelname }}:{{ msg }}")
    formatter.set_rule("levelname == 'INFO'", {'msg': 'info message'})
    record = {'levelname': 'WARNING', 'msg': 'test message'}
    modified_record = formatter.apply_rules(record)
    formatted = formatter.render(modified_record)
    assert formatted == "WARNING:test message"

def test_multiple_rules_all_apply():
    formatter = CustomFormatter(format_str="{{ levelname }}:{{ msg }}")
    formatter.set_rule("levelname == 'WARNING'", {'levelname': 'WARN'})
    formatter.set_rule("'test' in msg", {'msg': 'message contains test'})
    record = {'levelname': 'WARNING', 'msg': 'this is a test message'}
    modified_record = formatter.apply_rules(record)
    formatted = formatter.render(modified_record)
    assert formatted == "WARN:message contains test"

def test_function_override_rule():
    formatter = CustomFormatter(format_str="{{ my_func() }}")
    formatter.set_rule("1 == 1", {'my_func()': 'overridden'})
    
    formatter.env.globals['my_func'] = lambda: 'original'
    
    record = {}
    modified_record = formatter.apply_rules(record)
    formatted = formatter.render(modified_record)
    assert formatted == "overridden"

def test_function_override_no_match():
    formatter = CustomFormatter(format_str="{{ my_func() }}")
    formatter.set_rule("1 == 0", {'my_func()': 'overridden'})
    
    formatter.env.globals['my_func'] = lambda: 'original'
    
    record = {}
    modified_record = formatter.apply_rules(record)
    formatted = formatter.render(modified_record)
    assert formatted == "original"
