from services.jira_service import create_issue

class EscalationAgent:
    @staticmethod
    def escalate(ticket_data):
        """
        Escalates the ticket to Jira.
        Returns the Jira response.
        """
        # ticket_data already has all the fields formatted for create_issue
        status, error, key, url = create_issue(ticket_data)
        
        return {
            "status": status,
            "error": error,
            "issue_key": key,
            "issue_url": url
        }
