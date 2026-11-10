"""Keep secure UI field values out of higher-level action results."""


def redact_secure_values(value):
    if isinstance(value, list):
        return [redact_secure_values(item) for item in value]
    if isinstance(value, dict):
        result = {key: redact_secure_values(item) for key, item in value.items()}
        identity = f"{result.get('role', '')} {result.get('subrole', '')}".casefold()
        if "secure" in identity or "password" in identity:
            result["value"] = "[REDACTED]"
        return result
    return value
