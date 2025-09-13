from typing import Dict, Any, Optional, List
from config.logging_config import get_logger

logger = get_logger('ai_agent')

class ResponseFormatter:
    """Utility class for formatting AI agent responses"""
    
    def __init__(self):
        """Initialize Response Formatter"""
        self.success_emojis = ["✅", "🎉", "👍", "💚"]
        self.error_emojis = ["❌", "⚠️", "🔴", "💥"]
        self.info_emojis = ["ℹ️", "📋", "📌", "💡"]
    
    def create_success_response(
        self,
        message: str,
        data: Optional[Dict[str, Any]] = None,
        audio_path: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Create a success response
        
        Args:
            message (str): Success message
            data (Optional[Dict[str, Any]]): Additional data
            audio_path (Optional[str]): Path to audio response
            
        Returns:
            Dict[str, Any]: Formatted success response
        """
        response = {
            "success": True,
            "text": f"✅ {message}",
            "timestamp": self._get_timestamp(),
            "type": "success"
        }
        
        if data:
            response["data"] = data
        
        if audio_path:
            response["audio_path"] = audio_path
        
        return response
    
    def create_error_response(
        self,
        message: str,
        error_code: Optional[str] = None,
        audio_path: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Create an error response
        
        Args:
            message (str): Error message
            error_code (Optional[str]): Error code
            audio_path (Optional[str]): Path to audio response
            
        Returns:
            Dict[str, Any]: Formatted error response
        """
        response = {
            "success": False,
            "text": f"❌ {message}",
            "timestamp": self._get_timestamp(),
            "type": "error"
        }
        
        if error_code:
            response["error_code"] = error_code
        
        if audio_path:
            response["audio_path"] = audio_path
        
        return response
    
    def create_info_response(
        self,
        message: str,
        data: Optional[Dict[str, Any]] = None,
        audio_path: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Create an info response
        
        Args:
            message (str): Info message
            data (Optional[Dict[str, Any]]): Additional data
            audio_path (Optional[str]): Path to audio response
            
        Returns:
            Dict[str, Any]: Formatted info response
        """
        response = {
            "success": True,
            "text": f"ℹ️ {message}",
            "timestamp": self._get_timestamp(),
            "type": "info"
        }
        
        if data:
            response["data"] = data
        
        if audio_path:
            response["audio_path"] = audio_path
        
        return response
    
    def create_clarification_response(
        self,
        message: str,
        questions: List[str],
        audio_path: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Create a clarification response
        
        Args:
            message (str): Clarification message
            questions (List[str]): List of clarifying questions
            audio_path (Optional[str]): Path to audio response
            
        Returns:
            Dict[str, Any]: Formatted clarification response
        """
        response = {
            "success": False,
            "text": f"🤔 {message}",
            "timestamp": self._get_timestamp(),
            "type": "clarification",
            "requires_clarification": True,
            "clarification_questions": questions
        }
        
        if audio_path:
            response["audio_path"] = audio_path
        
        return response
    
    def format_calendar_response(
        self,
        action: str,
        event_details: Dict[str, Any],
        audio_path: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Format a calendar operation response
        
        Args:
            action (str): Action performed (created, updated, deleted, etc.)
            event_details (Dict[str, Any]): Event details
            audio_path (Optional[str]): Path to audio response
            
        Returns:
            Dict[str, Any]: Formatted calendar response
        """
        title = event_details.get("title", "Event")
        start_time = event_details.get("start_time", "")
        
        message = f"📅 Calendar event '{title}' {action} successfully"
        if start_time:
            message += f" for {start_time}"
        
        response = {
            "success": True,
            "text": message,
            "timestamp": self._get_timestamp(),
            "type": "calendar",
            "action": action,
            "event_details": event_details
        }
        
        if audio_path:
            response["audio_path"] = audio_path
        
        return response
    
    def format_email_response(
        self,
        action: str,
        email_details: Dict[str, Any],
        audio_path: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Format an email operation response
        
        Args:
            action (str): Action performed (sent, retrieved, deleted, etc.)
            email_details (Dict[str, Any]): Email details
            audio_path (Optional[str]): Path to audio response
            
        Returns:
            Dict[str, Any]: Formatted email response
        """
        if action == "sent":
            to_email = email_details.get("to", "recipient")
            subject = email_details.get("subject", "")
            message = f"📧 Email sent successfully to {to_email}"
            if subject:
                message += f"\nSubject: {subject}"
        elif action == "retrieved":
            count = email_details.get("count", 0)
            message = f"📬 Retrieved {count} emails successfully"
        else:
            message = f"📧 Email {action} successfully"
        
        response = {
            "success": True,
            "text": message,
            "timestamp": self._get_timestamp(),
            "type": "email",
            "action": action,
            "email_details": email_details
        }
        
        if audio_path:
            response["audio_path"] = audio_path
        
        return response
    
    def format_image_response(
        self,
        action: str,
        image_details: Dict[str, Any],
        audio_path: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Format an image operation response
        
        Args:
            action (str): Action performed (generated, edited, etc.)
            image_details (Dict[str, Any]): Image details
            audio_path (Optional[str]): Path to audio response
            
        Returns:
            Dict[str, Any]: Formatted image response
        """
        if action == "generated":
            description = image_details.get("description", "image")
            message = f"🎨 Image generated successfully based on: '{description}'"
        elif action == "edited":
            modifications = image_details.get("modifications", "modifications")
            message = f"✏️ Image edited successfully with: '{modifications}'"
        else:
            message = f"🎨 Image {action} successfully"
        
        response = {
            "success": True,
            "text": message,
            "timestamp": self._get_timestamp(),
            "type": "image",
            "action": action,
            "image_details": image_details
        }
        
        if audio_path:
            response["audio_path"] = audio_path
        
        return response
    
    def format_list_response(
        self,
        title: str,
        items: List[Dict[str, Any]],
        audio_path: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Format a list response (e.g., events, emails)
        
        Args:
            title (str): List title
            items (List[Dict[str, Any]]): List items
            audio_path (Optional[str]): Path to audio response
            
        Returns:
            Dict[str, Any]: Formatted list response
        """
        count = len(items)
        
        if count == 0:
            message = f"📋 No {title.lower()} found"
        else:
            message = f"📋 Found {count} {title.lower()}:\n\n"
            
            for i, item in enumerate(items[:5]):  # Show max 5 items
                if "title" in item and "start_time" in item:
                    # Calendar event format
                    message += f"{i+1}. {item['title']} - {item['start_time']}\n"
                elif "subject" in item and "sender" in item:
                    # Email format
                    message += f"{i+1}. {item['subject']} - From: {item['sender']}\n"
                else:
                    # Generic format
                    message += f"{i+1}. {str(item)[:100]}...\n"
            
            if count > 5:
                message += f"\n... and {count - 5} more items"
        
        response = {
            "success": True,
            "text": message,
            "timestamp": self._get_timestamp(),
            "type": "list",
            "title": title,
            "items": items,
            "count": count
        }
        
        if audio_path:
            response["audio_path"] = audio_path
        
        return response
    
    def format_help_response(self, audio_path: Optional[str] = None) -> Dict[str, Any]:
        """
        Format a help response
        
        Args:
            audio_path (Optional[str]): Path to audio response
            
        Returns:
            Dict[str, Any]: Formatted help response
        """
        help_text = """🤖 **AI Assistant Help**

I can help you with:

**📅 Calendar Operations:**
• Create events: "Create meeting tomorrow at 9 AM"
• View events: "Show my events for today"
• Update events: "Change meeting time to 10 AM"
• Delete events: "Cancel my 3 PM meeting"

**📧 Email Operations:**
• Send emails: "Send email to john@example.com about the project"
• Read emails: "Show my latest emails"
• Create drafts: "Draft email to team about deadline"

**🎨 Image Operations:**
• Generate images: "Create image of sunset over mountains"
• Edit images: "Change the sky color to purple"

**🎤 Audio Support:**
• Send voice messages - I'll convert them to text
• Get audio responses back

**Examples:**
• "Create event today at 8 AM meeting with John"
• "Send email to sarah@company.com about quarterly review"
• "Generate image of a futuristic city"

Just tell me what you'd like to do in natural language!"""

        response = {
            "success": True,
            "text": help_text,
            "timestamp": self._get_timestamp(),
            "type": "help"
        }
        
        if audio_path:
            response["audio_path"] = audio_path
        
        return response
    
    def format_multi_step_response(
        self,
        steps: List[Dict[str, Any]],
        audio_path: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Format a multi-step operation response
        
        Args:
            steps (List[Dict[str, Any]]): List of completed steps
            audio_path (Optional[str]): Path to audio response
            
        Returns:
            Dict[str, Any]: Formatted multi-step response
        """
        successful_steps = [step for step in steps if step.get("success", False)]
        failed_steps = [step for step in steps if not step.get("success", True)]
        
        message = f"🔄 **Multi-step Operation Complete**\n\n"
        message += f"✅ Successful: {len(successful_steps)}\n"
        message += f"❌ Failed: {len(failed_steps)}\n\n"
        
        if successful_steps:
            message += "**Completed Steps:**\n"
            for i, step in enumerate(successful_steps):
                message += f"{i+1}. {step.get('description', 'Step completed')}\n"
        
        if failed_steps:
            message += "\n**Failed Steps:**\n"
            for i, step in enumerate(failed_steps):
                error = step.get('error', 'Unknown error')
                message += f"{i+1}. {step.get('description', 'Step failed')}: {error}\n"
        
        response = {
            "success": len(successful_steps) > 0,
            "text": message,
            "timestamp": self._get_timestamp(),
            "type": "multi_step",
            "steps": steps,
            "successful_count": len(successful_steps),
            "failed_count": len(failed_steps)
        }
        
        if audio_path:
            response["audio_path"] = audio_path
        
        return response
    
    def add_suggestions(
        self,
        response: Dict[str, Any],
        suggestions: List[str]
    ) -> Dict[str, Any]:
        """
        Add suggestions to an existing response
        
        Args:
            response (Dict[str, Any]): Existing response
            suggestions (List[str]): List of suggestions
            
        Returns:
            Dict[str, Any]: Response with suggestions added
        """
        if suggestions:
            response["text"] += f"\n\n💡 **Suggestions:**\n"
            for i, suggestion in enumerate(suggestions[:3]):  # Max 3 suggestions
                response["text"] += f"• {suggestion}\n"
            
            response["suggestions"] = suggestions
        
        return response
    
    def add_quick_actions(
        self,
        response: Dict[str, Any],
        actions: List[Dict[str, str]]
    ) -> Dict[str, Any]:
        """
        Add quick action buttons to response
        
        Args:
            response (Dict[str, Any]): Existing response
            actions (List[Dict[str, str]]): List of quick actions
            
        Returns:
            Dict[str, Any]: Response with quick actions added
        """
        if actions:
            response["quick_actions"] = actions
        
        return response
    
    def _get_timestamp(self) -> str:
        """Get current timestamp"""
        from datetime import datetime
        return datetime.now().isoformat()
    
    def clean_text_for_tts(self, text: str) -> str:
        """
        Clean text for better text-to-speech output
        
        Args:
            text (str): Text to clean
            
        Returns:
            str: Cleaned text
        """
        # Remove markdown formatting
        cleaned = text.replace("**", "").replace("*", "")
        
        # Remove emojis for TTS (keep letters/numbers/punctuation)
        import re
        cleaned = re.sub(r'[^\w\s\.,\?!;:\-\(\)]', '', cleaned)
        
        # Clean up multiple spaces
        cleaned = re.sub(r'\s+', ' ', cleaned).strip()
        
        return cleaned
    
    def truncate_for_display(self, text: str, max_length: int = 200) -> str:
        """
        Truncate text for display purposes
        
        Args:
            text (str): Text to truncate
            max_length (int): Maximum length
            
        Returns:
            str: Truncated text
        """
        if len(text) <= max_length:
            return text
        
        # Find a good breaking point
        truncated = text[:max_length]
        
        # Try to break at word boundary
        last_space = truncated.rfind(' ')
        if last_space > max_length * 0.8:  # If space is not too far back
            truncated = truncated[:last_space]
        
        return truncated + "..."
    
    def format_validation_errors(
        self,
        errors: List[str],
        audio_path: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Format validation error response
        
        Args:
            errors (List[str]): List of validation errors
            audio_path (Optional[str]): Path to audio response
            
        Returns:
            Dict[str, Any]: Formatted validation error response
        """
        if len(errors) == 1:
            message = f"⚠️ Validation Error: {errors[0]}"
        else:
            message = f"⚠️ Validation Errors:\n"
            for i, error in enumerate(errors):
                message += f"{i+1}. {error}\n"
        
        response = {
            "success": False,
            "text": message,
            "timestamp": self._get_timestamp(),
            "type": "validation_error",
            "errors": errors
        }
        
        if audio_path:
            response["audio_path"] = audio_path
        
        return response

# Create global instance
response_formatter = ResponseFormatter()