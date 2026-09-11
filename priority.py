def calculate_priority(severity, business_impact):
    # Normalize inputs
    severity = severity.capitalize()
    business_impact = business_impact.capitalize()
    
    if severity == "Critical" and business_impact == "High":
        return "P1"
    elif severity == "High" and business_impact == "High":
        return "P1"
    elif severity == "High":
        return "P2"
    elif severity == "Medium":
        return "P3"
    else:
        return "P4"
