import re


class ToolRouter:
    KEYWORDS = {
        "system": "battery charge volume sound display network notification system заряд громк звук экран сеть уведомлен",
        "application": "app application launch open quit running active приложение открыть запусти закрой",
        "window": "window focus minimize maximize move resize окно сверни разверни перемести размер",
        "input": "click type keyboard mouse shortcut paste select нажми введи клавиат мышь вставь выдели",
        "file": "file folder directory search read write delete copy move файл папк найди прочитай запиши удали копир",
        "browser": "browser tab page url website браузер вкладк страниц сайт",
        "notes": "note notes заметк",
        "calendar": "calendar event meeting reminder календар встреч напомин",
        "media": "music video spotify player playlist музык видео плейлист",
        "communication": "mail email message telegram slack send письмо сообщен отправ",
        "code": "code git test terminal command project код тест терминал команд проект",
    }
    INTENTS = {
        "open launch запуст открой": "open launch activate",
        "close quit stop закрой заверш": "close quit stop force_quit",
        "active focus foreground актив фокус": "active activate focus front",
        "read show get прочит покаж получ": "read get preview info",
        "write save create запиш сохрани создай": "write save create append",
        "delete remove trash удал очист": "delete remove trash clear",
        "find search найди поиск": "find search",
        "copy duplicate копир дублир": "copy duplicate",
        "move rename перемест переимен": "move rename",
        "volume sound mute громк звук тиш": "volume mute audio",
        "click press tap нажм клик": "click press tap",
        "type paste введ встав": "type paste text",
    }

    def __init__(self, max_tools=18):
        self.max_tools = max_tools

    def select(self, request: str, registry, allowed_names=None) -> list[str]:
        names = list(allowed_names or registry.names())
        query = request.lower()
        words = set(re.findall(r"[\w.-]+", query))
        categories = {name for name, keys in self.KEYWORDS.items() if any(key in query for key in keys.split())}
        intents = {token for keys, values in self.INTENTS.items() if any(key in query for key in keys.split())
                   for token in values.split()}
        scored = []
        for name in names:
            action = registry.get(name)
            category = getattr(getattr(action, "category", None), "value", "")
            text = f"{name} {action.description}".lower()
            score = (4 if category in categories else 0) + sum(word in text for word in words)
            score += 8 * sum(token in text for token in intents)
            scored.append((score, name))
        selected = [name for score, name in sorted(scored, key=lambda item: (-item[0], item[1])) if score]
        if not selected:
            selected = names[:self.max_tools]
        return selected[:self.max_tools]
