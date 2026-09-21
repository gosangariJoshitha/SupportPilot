def analyze_ticket(ticket_id, title, description, category=None, priority=None):
    text = f"{title} {description}".lower()

    possible_keywords = [
        "vpn", "network", "wifi", "internet", "firewall",
        "authentication", "password", "login", "account", "mfa",
        "timeout", "connection", "dns",
        "install", "software", "application", "browser", "license",
        "laptop", "printer", "monitor", "keyboard", "mouse", "hardware",
        "server", "database", "deploy", "cpu", "memory", "disk", "outage"
    ]

    keywords = [kw for kw in possible_keywords if kw in text]

    return {
        "ticket_id": ticket_id,
        "category": category,
        "priority": priority,
        "keywords": keywords,
        "query": text
    }
