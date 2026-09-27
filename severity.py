def predict_severity(ticket):
    text = ticket.lower()

    critical_words = [
        "server down",
        "entire company",
        "production down",
        "security breach",
        "database down",
        "all employees unable to work"
    ]

    high_words = [
        "vpn",
        "cannot connect",
        "connection failing",
        "network",
        "firewall",
        "wifi",
        "internet",
        "authentication",
        "login failed",
        "outage",
        "deployment failure",
        "urgent",
        "cannot work",
        "business stopped",
        "client meeting"
    ]

    medium_words = [
        "slow",
        "error",
        "problem",
        "issue",
        "application crash",
        "browser",
        "software",
        "printer",
        "monitor",
        "hardware"
    ]

    if any(word in text for word in critical_words):
        return "Critical"

    if any(word in text for word in high_words):
        return "High"

    if any(word in text for word in medium_words):
        return "Medium"

    return "Low"
