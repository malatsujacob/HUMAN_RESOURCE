DEPARTMENT_CATALOG = (
    {"code": "TECH", "name": "Tech"},
    {"code": "FINANCE", "name": "Finance"},
    {"code": "SALES", "name": "Sales"},
    {"code": "CUSTOMER_SUPPORT", "name": "Customer Support"},
    {"code": "SECURITY", "name": "Security"},
    {"code": "CATERING", "name": "Catering"},
    {"code": "MARKETING", "name": "Marketing"},
    {"code": "ADMINISTRATION", "name": "Administration/Management"},
)

_DEPARTMENT_ALIASES = {
    "TECH": ("TECH", "TECHNOLOGY", "IT", "INFORMATION TECHNOLOGY"),
    "FINANCE": ("FINANCE", "ACCOUNTING", "FINANCE AND ACCOUNTING"),
    "SALES": ("SALES",),
    "CUSTOMER_SUPPORT": ("CUSTOMER SUPPORT", "CUSTOMER_SERVICE", "CUSTOMER SERVICES"),
    "SECURITY": ("SECURITY",),
    "CATERING": ("CATERING",),
    "MARKETING": ("MARKETING",),
    "ADMINISTRATION": (
        "ADMINISTRATION",
        "ADMIN",
        "MANAGEMENT",
        "ADMINISTRATION/MANAGEMENT",
        "ADMINISTRATION AND MANAGEMENT",
    ),
}


def _department_key(value: str | None) -> str:
    return "".join(character for character in (value or "").casefold() if character.isalnum())


_DEPARTMENT_CODES_BY_ALIAS = {
    _department_key(alias): code
    for code, aliases in _DEPARTMENT_ALIASES.items()
    for alias in aliases
}
_DEPARTMENT_NAMES = {department["code"]: department["name"] for department in DEPARTMENT_CATALOG}


def canonical_department_code(value: str | None) -> str | None:
    if not value:
        return None
    return _DEPARTMENT_CODES_BY_ALIAS.get(_department_key(value))


def canonical_department_name(value: str | None) -> str | None:
    code = canonical_department_code(value)
    return _DEPARTMENT_NAMES.get(code) if code else None
