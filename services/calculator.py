import ast
import html
import operator
import re

ALLOWED_OPERATORS = {
    ast.Add: operator.add,
    ast.Sub: operator.sub,
    ast.Mult: operator.mul,
    ast.Div: operator.truediv,
    ast.USub: operator.neg,
    ast.UAdd: operator.pos,
}


def safe_eval(node):
    if isinstance(node, ast.Constant) and isinstance(node.value, (int, float)):
        return node.value
    elif isinstance(node, ast.BinOp) and type(node.op) in ALLOWED_OPERATORS:
        return ALLOWED_OPERATORS[type(node.op)](safe_eval(node.left), safe_eval(node.right))
    elif isinstance(node, ast.UnaryOp) and type(node.op) in ALLOWED_OPERATORS:
        return ALLOWED_OPERATORS[type(node.op)](safe_eval(node.operand))
    elif isinstance(node, ast.Expression):
        return safe_eval(node.body)
    raise ValueError("Unsupported math operation")


def format_calc_result(value: float) -> str:
    if value.is_integer():
        return f"{int(value):,}".replace(",", " ")
    return f"{value:,.8f}".rstrip("0").rstrip(".").replace(",", " ")


def process_math_expression(text: str) -> str | None:
    if not text or len(text) > 200:
        return None

    text = text.strip().replace(",", ".")

    if re.match(r"^\d{1,4}[-\./]\d{1,2}[-\./]\d{1,4}$", text) or re.match(r"^-?\d+(\.\d+)?(-?\d+(\.\d+)?)*$", text):
        return None

    if "**" in text:
        return None

    try:
        tree = ast.parse(text, mode="eval")
        result = safe_eval(tree)
        return f"🧮 <b>{html.escape(text)} = {format_calc_result(result)}</b>"
    except Exception:
        return None