import ast
import re

from core.config import BASE_DIR
import core.database as db
import core.language as lang

SOURCE_DIRS = ("core", "handlers", "services")
PLACEHOLDER_RE = re.compile(r"\{(\w+)(?::[^}]*)?\}")


def _extract_placeholders(text: str) -> set[str]:
    return set(PLACEHOLDER_RE.findall(text))


def _collect_referenced_keys_from_code() -> set[str]:
    """Parses all project Python files via AST to extract every literal key passed to get_text()."""
    referenced: set[str] = set()

    for folder in SOURCE_DIRS:
        for py_file in (BASE_DIR / folder).rglob("*.py"):
            tree = ast.parse(py_file.read_text(encoding="utf-8"), filename=str(py_file))
            for node in ast.walk(tree):
                if not isinstance(node, ast.Call):
                    continue

                func_name = None
                if isinstance(node.func, ast.Name):
                    func_name = node.func.id
                elif isinstance(node.func, ast.Attribute):
                    func_name = node.func.attr

                if func_name != "get_text":
                    continue

                if len(node.args) >= 2 and isinstance(node.args[1], ast.Constant) and isinstance(node.args[1].value, str):
                    referenced.add(node.args[1].value)

                for kw in node.keywords:
                    if kw.arg == "key" and isinstance(kw.value, ast.Constant) and isinstance(kw.value.value, str):
                        referenced.add(kw.value.value)

    return referenced


def test_all_code_keys_exist_in_all_translations():
    referenced_keys = _collect_referenced_keys_from_code()
    assert referenced_keys, "AST scanner found no get_text() calls"

    for lang_code, dictionary in lang.TRANSLATIONS.items():
        missing = referenced_keys - set(dictionary.keys())
        assert not missing, f"Keys used in code but missing in '{lang_code}': {sorted(missing)}"


def test_all_languages_have_identical_keys():
    en_keys = set(lang.TRANSLATIONS["en"].keys())
    uk_keys = set(lang.TRANSLATIONS["uk"].keys())
    ru_keys = set(lang.TRANSLATIONS["ru"].keys())

    assert en_keys == uk_keys, f"EN vs UK key diff: {en_keys ^ uk_keys}"
    assert en_keys == ru_keys, f"EN vs RU key diff: {en_keys ^ ru_keys}"


def test_all_languages_have_identical_placeholders():
    en = lang.TRANSLATIONS["en"]
    uk = lang.TRANSLATIONS["uk"]
    ru = lang.TRANSLATIONS["ru"]

    for key, en_text in en.items():
        en_ph = _extract_placeholders(en_text)
        uk_ph = _extract_placeholders(uk[key])
        ru_ph = _extract_placeholders(ru[key])
        assert en_ph == uk_ph == ru_ph, (
            f"Placeholder mismatch for '{key}': en={en_ph}, uk={uk_ph}, ru={ru_ph}"
        )


def test_get_text_fallback_for_unknown_language():
    user_id = 9001
    db.update_setting(user_id, "language", "fr")
    result = lang.get_text(user_id, "start_greeting", name="Alice")
    assert "Alice" in result
    assert "Hello" in result