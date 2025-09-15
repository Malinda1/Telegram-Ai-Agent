import base64
import email
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from typing import List, Dict, Any, Optional
from auth.google_auth import google_auth
from config.logging_config import get_logger

logger = get_logger('email_service')

class EmailService:
    """Service for Gmail operations"""
    
    def __init__(self):
        """Initialize Email Service"""
        self.service = None
        logger.info("EmailService initialized")
    
    def _get_service(self):
        """Get or create Gmail service"""
        if not self.service:
            self.service = google_auth.get_gmail_service()
        return self.service
    
    def _create_message(
        self,
        to_email: str,
        subject: str,
        body: str,
        from_email: str = None
    ) -> str:
        """
        Create a message for an email
        
        Args:
            to_email (str): Recipient email address
            subject (str): Email subject
            body (str): Email body
            from_email (str): Sender email (optional)
            
        Returns:
            str: Base64 encoded message
        """
        try:
            # Create message
            message = MIMEMultipart()
            message['to'] = to_email
            message['subject'] = subject
            
            if from_email:
                message['from'] = from_email
            
            # Add body
            if body:
                message.attach(MIMEText(body, 'plain'))
            
            # Encode message
            raw_message = base64.urlsafe_b64encode(message.as_bytes()).decode('utf-8')
            return raw_message
            
        except Exception as e:
            logger.error(f"Error creating email message: {str(e)}")
            raise e
    
    async def send_email(
        self,
        to_email: str,
        subject: str,
        body: str,
        from_email: str = None
    ) -> Dict[str, Any]:
        """
        Send an email
        
        Args:
            to_email (str): Recipient email address
            subject (str): Email subject
            body (str): Email body
            from_email (str): Sender email (optional)
            
        Returns:
            Dict[str, Any]: Result with success status and message details
        """
        try:
            logger.info(f"Sending email to: {to_email}")
            
            service = self._get_service()
            if not service:
                return {
                    "success": False,
                    "error": "Failed to connect to Gmail service"
                }
            
            # Create message
            raw_message = self._create_message(to_email, subject, body, from_email)
            
            # Send message
            message_body = {'raw': raw_message}
            sent_message = service.users().messages().send(
                userId='me',
                body=message_body
            ).execute()
            
            logger.info(f"Email sent successfully. Message ID: {sent_message.get('id')}")
            
            return {
                "success": True,
                "message_id": sent_message.get('id'),
                "thread_id": sent_message.get('threadId'),
                "details": {
                    "to": to_email,
                    "subject": subject,
                    "body_preview": body[:100] + "..." if len(body) > 100 else body
                }
            }
            
        except Exception as e:
            logger.error(f"Error sending email: {str(e)}")
            return {
                "success": False,
                "error": str(e)
            }
    
    async def get_emails(
        self,
        query: str = None,
        max_results: int = 10,
        include_body: bool = False
    ) -> Dict[str, Any]:
        """
        Retrieve emails from Gmail
        
        Args:
            query (str): Gmail search query (optional)
            max_results (int): Maximum number of emails to return
            include_body (bool): Whether to include email body content
            
        Returns:
            Dict[str, Any]: Result with success status and emails list
        """
        try:
            logger.info("Retrieving emails from Gmail")
            
            service = self._get_service()
            if not service:
                return {
                    "success": False,
                    "error": "Failed to connect to Gmail service"
                }
            
            # Search for messages
            search_query = query or 'in:inbox'
            results = service.users().messages().list(
                userId='me',
                q=search_query,
                maxResults=max_results
            ).execute()
            
            messages = results.get('messages', [])
            
            formatted_emails = []
            for message in messages:
                # Get message details
                msg = service.users().messages().get(
                    userId='me',
                    id=message['id'],
                    format='full'
                ).execute()
                
                # Extract headers
                headers = msg.get('payload', {}).get('headers', [])
                subject = next((h['value'] for h in headers if h['name'] == 'Subject'), 'No Subject')
                sender = next((h['value'] for h in headers if h['name'] == 'From'), 'Unknown Sender')
                date = next((h['value'] for h in headers if h['name'] == 'Date'), 'Unknown Date')
                
                email_data = {
                    "id": message['id'],
                    "thread_id": message['threadId'],
                    "subject": subject,
                    "sender": sender,
                    "date": date,
                    "snippet": msg.get('snippet', '')
                }
                
                # Include body if requested
                if include_body:
                    body = self._extract_email_body(msg)
                    email_data["body"] = body
                
                formatted_emails.append(email_data)
            
            logger.info(f"Retrieved {len(formatted_emails)} emails")
            
            return {
                "success": True,
                "emails": formatted_emails,
                "total_count": len(formatted_emails)
            }
            
        except Exception as e:
            logger.error(f"Error retrieving emails: {str(e)}")
            return {
                "success": False,
                "error": str(e)
            }
    
    def _extract_email_body(self, message: Dict[str, Any]) -> str:
        """
        Extract email body from Gmail message
        
        Args:
            message (Dict[str, Any]): Gmail message object
            
        Returns:
            str: Extracted email body
        """
        try:
            payload = message.get('payload', {})
            
            # Handle different payload structures
            if 'parts' in payload:
                # Multipart message
                for part in payload['parts']:
                    if part.get('mimeType') == 'text/plain':
                        data = part.get('body', {}).get('data')
                        if data:
                            return base64.urlsafe_b64decode(data).decode('utf-8')
            else:
                # Single part message
                if payload.get('mimeType') == 'text/plain':
                    data = payload.get('body', {}).get('data')
                    if data:
                        return base64.urlsafe_b64decode(data).decode('utf-8')
            
            # Fallback to snippet
            return message.get('snippet', '')
            
        except Exception as e:
            logger.error(f"Error extracting email body: {str(e)}")
            return message.get('snippet', '')
    
    async def delete_email(self, message_id: str) -> Dict[str, Any]:
        """
        Delete an email
        
        Args:
            message_id (str): ID of the message to delete
            
        Returns:
            Dict[str, Any]: Result with success status
        """
        try:
            logger.info(f"Deleting email: {message_id}")
            
            service = self._get_service()
            if not service:
                return {
                    "success": False,
                    "error": "Failed to connect to Gmail service"
                }
            
            # Delete the message
            service.users().messages().delete(
                userId='me',
                id=message_id
            ).execute()
            
            logger.info(f"Email deleted successfully: {message_id}")
            
            return {
                "success": True,
                "message": "Email deleted successfully"
            }
            
        except Exception as e:
            logger.error(f"Error deleting email: {str(e)}")
            return {
                "success": False,
                "error": str(e)
            }
    
    async def create_draft(
        self,
        to_email: str,
        subject: str,
        body: str
    ) -> Dict[str, Any]:
        """
        Create a draft email
        
        Args:
            to_email (str): Recipient email address
            subject (str): Email subject
            body (str): Email body
            
        Returns:
            Dict[str, Any]: Result with success status and draft details
        """
        try:
            logger.info(f"Creating draft email to: {to_email}")
            
            service = self._get_service()
            if not service:
                return {
                    "success": False,
                    "error": "Failed to connect to Gmail service"
                }
            
            # Create message
            raw_message = self._create_message(to_email, subject, body)
            
            # Create draft
            draft_body = {
                'message': {
                    'raw': raw_message
                }
            }
            
            draft = service.users().drafts().create(
                userId='me',
                body=draft_body
            ).execute()
            
            logger.info(f"Draft created successfully. Draft ID: {draft.get('id')}")
            
            return {
                "success": True,
                "draft_id": draft.get('id'),
                "message_id": draft.get('message', {}).get('id'),
                "details": {
                    "to": to_email,
                    "subject": subject,
                    "body_preview": body[:100] + "..." if len(body) > 100 else body
                }
            }
            
        except Exception as e:
            logger.error(f"Error creating draft: {str(e)}")
            return {
                "success": False,
                "error": str(e)
            }
    
    async def send_meeting_reminder(
        self,
        attendee_email: str,
        meeting_details: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Send a professional meeting reminder email
        
        Args:
            attendee_email (str): Attendee's email address
            meeting_details (Dict[str, Any]): Meeting details
            
        Returns:
            Dict[str, Any]: Result with success status
        """
        try:
            logger.info(f"Sending meeting reminder to: {attendee_email}")
            
            # Extract meeting details
            title = meeting_details.get('title', 'Meeting')
            start_time = meeting_details.get('start_time', 'TBD')
            description = meeting_details.get('description', '')
            link = meeting_details.get('link', '')
            
            # Create professional email content
            subject = f"Meeting Reminder: {title}"
            
            body = f"""Dear Colleague,

This is a friendly reminder about our upcoming meeting:

📅 Meeting: {title}
🕒 Time: {start_time}
"""
            
            if description:
                body += f"📋 Description: {description}\n"
            
            if link:
                body += f"🔗 Calendar Link: {link}\n"
            
            body += """
Please let me know if you have any questions or need to reschedule.

Looking forward to our meeting!

Best regards,
AI Assistant
"""
            
            # Send the email
            result = await self.send_email(attendee_email, subject, body)
            
            if result["success"]:
                logger.info(f"Meeting reminder sent successfully to {attendee_email}")
            
            return result
            
        except Exception as e:
            logger.error(f"Error sending meeting reminder: {str(e)}")
            return {
                "success": False,
                "error": str(e)
            }
    
    async def get_user_email(self) -> Optional[str]:
        """
        Get the authenticated user's email address
        
        Returns:
            Optional[str]: User's email address or None if failed
        """
        try:
            service = self._get_service()
            if not service:
                return None
            
            profile = service.users().getProfile(userId='me').execute()
            return profile.get('emailAddress')
            
        except Exception as e:
            logger.error(f"Error getting user email: {str(e)}")
            return None
        
    # Example of how your main agent should handle email_get intent
# Add this to your main agent processing logic

async def process_email_get(self, analysis_result: Dict[str, Any]) -> Dict[str, Any]:
    """
    Process email retrieval request
    
    Args:
        analysis_result: Result from LLM analysis
        
    Returns:
        Dict with response details
    """
    try:
        parameters = analysis_result.get('parameters', {})
        
        # Extract parameters with defaults
        query = parameters.get('query', 'is:inbox')
        max_results = parameters.get('max_results', 10)
        include_body = parameters.get('include_body', False)
        
        logger.info(f"Getting emails with query: {query}")
        
        # Call the email service
        result = await self.email_service.get_emails(
            query=query,
            max_results=max_results,
            include_body=include_body
        )
        
        if result["success"]:
            emails = result["emails"]
            total_count = result["total_count"]
            
            # Format the response using LLM
            query_type = parameters.get('time_filter', 'emails')
            if query_type == 'today':
                query_type = "today's emails"
            elif 'unread' in query:
                query_type = "unread emails"
            
            formatted_response = await self.llm_handler.format_email_list_response(
                emails, total_count, query_type
            )
            
            return {
                "success": True,
                "response": formatted_response,
                "emails": emails,
                "total_count": total_count
            }
        else:
            error_message = f"Sorry, I couldn't retrieve your emails. Error: {result.get('error', 'Unknown error')}"
            return {
                "success": False,
                "response": error_message,
                "error": result.get('error')
            }
            
    except Exception as e:
        logger.error(f"Error processing email get request: {str(e)}")
        return {
            "success": False,
            "response": "Sorry, I encountered an error while retrieving your emails.",
            "error": str(e)
        }

# Example of main agent processing logic
async def process_user_request(self, user_input: str) -> str:
    """
    Main method to process user requests
    """
    try:
        # Get analysis from LLM
        analysis_result = await self.llm_handler.process_user_input(user_input)
        
        if not analysis_result:
            return "Sorry, I couldn't understand your request."
        
        intent = analysis_result.get('intent')
        logger.info(f"Detected intent: {intent}")
        
        # Route based on intent
        if intent == 'email_get':
            result = await self.process_email_get(analysis_result)
            return result["response"]
            
        elif intent == 'email_send':
            result = await self.process_email_send(analysis_result)
            return result["response"]
            
        elif intent == 'calendar_create':
            result = await self.process_calendar_create(analysis_result)
            return result["response"]
            
        elif intent == 'calendar_get':
            result = await self.process_calendar_get(analysis_result)
            return result["response"]
            
        else:
            # General chat or unsupported intent
            return analysis_result.get('response_text', "I can help you with emails and calendar events. What would you like to do?")
            
    except Exception as e:
        logger.error(f"Error processing user request: {str(e)}")
        return "Sorry, I encountered an error processing your request."

# Make sure your main agent class initialization includes:
def __init__(self):
    from core.llm_handler import llm_handler
    from email_service import email_service
    
    self.llm_handler = llm_handler
    self.email_service = email_service

# Create global instance
email_service = EmailService()