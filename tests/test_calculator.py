from services.calculator import format_calc_result, process_math_expression


def test_format_calc_result():
    assert format_calc_result(1000.0) == "1 000"
    assert format_calc_result(1234.56000000) == "1 234.56"
    assert format_calc_result(0.000045) == "0.000045"


def test_valid_arithmetic_expressions():
    assert process_math_expression("2 + 2 * 2") == "🧮 <b>2 + 2 * 2 = 6</b>"
    assert process_math_expression("(1500 + 250) / 2") == "🧮 <b>(1500 + 250) / 2 = 875</b>"
    assert process_math_expression("10,5 * 2") == "🧮 <b>10.5 * 2 = 21</b>"
    assert process_math_expression("-50 + 12.5") == "🧮 <b>-50 + 12.5 = -37.5</b>"


def test_rejected_and_malicious_expressions():
    assert process_math_expression("16.11.2026") is None
    assert process_math_expression("2026-11-16") is None
    assert process_math_expression("42") is None

    assert process_math_expression("10 / 0") is None
    assert process_math_expression("2 ** 100") is None
    assert process_math_expression("9 ** 9 ** 9") is None

    # Expressions exceeding 200 characters must be rejected
    assert process_math_expression("1+" * 120 + "1") is None

    assert process_math_expression("__import__('os').system('ls')") is None
    assert process_math_expression("eval('1+1')") is None
    assert process_math_expression("open('/etc/passwd')") is None