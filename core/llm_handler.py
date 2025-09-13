import os
from typing import Optional, Dict, Any
from google import genai
from config.settings import settings
from config.logging_config import get_logger

logger = get_logger('ai_agent')

class LLMHandler:
    """Handler for Gemini LLM interactions"""
    
    def __init__(self):
        """Initialize the LLM handler"""
        self.client = genai.Client(api_key=settings.GEMINI_API_KEY)
        self.model = settings.GEMINI_LLM_MODEL
        self.system_prompt = self._get_system_prompt()
        logger.info("LLMHandler initialized")
    
    def _get_system_prompt(self) -> str:
        """Get the system prompt for the AI agent"""
        return """You are an advanced AI assistant that helps users manage their calendar events and email communications through a Telegram bot. Your capabilities include:

**Calendar Operations:**
- Create events with specific dates, times, and details
- Update existing events 
- Delete events
- Retrieve event information
- Set reminders and notifications

**Email Operations:**
- Send emails with perfect formatting
- Retrieve and read emails
- Delete emails
- Create draft emails
- Send meeting reminders via email

**Image Generation:**
- Generate images based on text descriptions
- Edit existing images based on user feedback

**Key Instructions:**
1. Always provide clear, structured responses
2. For calendar events, extract: title, date, time, duration, description, attendees
3. For emails, extract: recipient, subject, body content, purpose
4. When creating meeting events, automatically offer to send email reminders
5. Always confirm actions before executing them
6. Provide both text and audio responses when possible
7. Be conversational and helpful
8. If unclear about user intent, ask clarifying questions

**Response Format:**
Always structure your responses with:
- Clear confirmation of what you understood
- Details of the action to be taken
- Any additional suggestions or options

**Examples:**
User: "Create an event for today at 8:00 AM"
Response: "I'll create an event for today at 8:00 AM. Could you please provide:
- Event title/description
- Duration (how long will it last?)
- Any attendees to invite?

Once you confirm these details, I'll create the event and can also send calendar invitations if needed."

User: "Send email to John about the meeting tomorrow"
Response: "I'll help you send an email to John about tomorrow's meeting. To create the perfect email, I need:
- John's email address
- Specific details about the meeting (time, location, agenda)
- Any special instructions or requests

Should I create a professional meeting reminder email for you?"

Always be proactive in offering related services and maintaining context throughout the conversation."""

    async def process_user_input(
        self, 
        user_input: str, 
        context: Optional[Dict[str, Any]] = None
    ) -> Optional[Dict[str, Any]]:
        """
        Process user input and determine the appropriate action
        
        Args:
            user_input (str): The user's input text
            context (Optional[Dict[str, Any]]): Additional context information
            
        Returns:
            Optional[Dict[str, Any]]: Processed response with action type and details
        """
        try:
            logger.info(f"Processing user input: {user_input[:100]}...")
            
            # Prepare context information
            context_info = ""
            if context:
                context_info = f"Context: {context}\n\n"
            
            # Create the prompt for intent recognition and response generation
            analysis_prompt = f"""
{self.system_prompt}

{context_info}User Input: "{user_input}"

Analyze this input and provide a structured response in the following JSON format:

{{
    "intent": "calendar_create|calendar_update|calendar_delete|calendar_get|email_send|email_get|email_delete|email_draft|image_generate|image_edit|general_chat",
    "confidence": 0.0-1.0,
    "parameters": {{
        // Extracted parameters based on intent
    }},
    "response_text": "Your conversational response to the user",
    "requires_clarification": true/false,
    "clarification_questions": ["question1", "question2"],
    "suggested_actions": ["action1", "action2"]
}}

For calendar operations, extract: title, date, time, duration, description, attendees
For email operations, extract: recipient, recipient_email, subject, body, purpose
For image operations, extract: description, style, modifications
"""

            # Send to Gemini for processing
            response = self.client.models.generate_content(
                model=self.model,
                contents=analysis_prompt
            )
            
            if not response or not response.text:
                logger.error("Empty response from LLM")
                return None
            
            # Parse the response
            try:
                import json
                # Extract JSON from response (handle potential markdown formatting)
                response_text = response.text.strip()
                if response_text.startswith("```json"):
                    response_text = response_text.split("```json")[1].split("```")[0]
                elif response_text.startswith("```"):
                    response_text = response_text.split("```")[1].split("```")[0]
                
                parsed_response = json.loads(response_text)
                
                logger.info(f"LLM analysis complete - Intent: {parsed_response.get('intent')}")
                return parsed_response
                
            except json.JSONDecodeError as e:
                logger.error(f"Failed to parse LLM JSON response: {e}")
                # Fallback: create a general chat response
                return {
                    "intent": "general_chat",
                    "confidence": 0.7,
                    "parameters": {},
                    "response_text": response.text,
                    "requires_clarification": False,
                    "clarification_questions": [],
                    "suggested_actions": []
                }
                
        except Exception as e:
            logger.error(f"Error processing user input with LLM: {str(e)}")
            return None
    
    async def generate_response(
        self, 
        prompt: str, 
        max_tokens: int = 500
    ) -> Optional[str]:
        """
        Generate a general response using the LLM
        
        Args:
            prompt (str): The prompt to send to the LLM
            max_tokens (int): Maximum number of tokens in response
            
        Returns:
            Optional[str]: Generated response text
        """
        try:
            logger.info("Generating LLM response...")
            
            response = self.client.models.generate_content(
                model=self.model,
                contents=prompt
            )
            
            if response and response.text:
                logger.info("LLM response generated successfully")
                return response.text.strip()
            else:
                logger.error("Empty response from LLM")
                return None
                
        except Exception as e:
            logger.error(f"Error generating LLM response: {str(e)}")
            return None
    
    async def create_email_content(
        self,
        purpose: str,
        recipient_name: str,
        additional_details: Dict[str, Any]
    ) -> Optional[Dict[str, str]]:
        """
        Generate professional email content
        
        Args:
            purpose (str): Purpose of the email
            recipient_name (str): Name of the recipient
            additional_details (Dict[str, Any]): Additional context and details
            
        Returns:
            Optional[Dict[str, str]]: Dictionary with 'subject' and 'body'
        """
        try:
            logger.info(f"Creating email content for purpose: {purpose}")
            
            prompt = f"""
Create a professional email with the following details:

Purpose: {purpose}
Recipient: {recipient_name}
Additional Details: {additional_details}

Generate a response in JSON format:
{{
    "subject": "Professional email subject",
    "body": "Professional email body with proper formatting"
}}

Guidelines:
- Use professional tone
- Include proper greeting and closing
- Be clear and concise
- Include all relevant information from additional_details
- Format for easy reading
"""

            response = await self.generate_response(prompt)
            if not response:
                return None
            
            try:
                import json
                # Clean and parse response
                response_text = response.strip()
                if response_text.startswith("```json"):
                    response_text = response_text.split("```json")[1].split("```")[0]
                elif response_text.startswith("```"):
                    response_text = response_text.split("```")[1].split("```")[0]
                
                email_content = json.loads(response_text)
                return email_content
                
            except json.JSONDecodeError:
                logger.error("Failed to parse email content JSON")
                return None
                
        except Exception as e:
            logger.error(f"Error creating email content: {str(e)}")
            return None
    
    async def format_calendar_event_response(
        self,
        event_details: Dict[str, Any],
        action: str = "created"
    ) -> str:
        """
        Format a response for calendar operations
        
        Args:
            event_details (Dict[str, Any]): Event details
            action (str): Action performed (created, updated, deleted, etc.)
            
        Returns:
            str: Formatted response text
        """
        try:
            prompt = f"""
Create a friendly confirmation message for a calendar event that was {action}.

Event Details: {event_details}

Create a conversational response that:
- Confirms the action was completed
- Summarizes the key event details
- Offers helpful next steps or suggestions
- Maintains a helpful, professional tone

Keep it concise but informative.
"""
            
            response = await self.generate_response(prompt)
            return response or f"Calendar event {action} successfully."
            
        except Exception as e:
            logger.error(f"Error formatting calendar response: {str(e)}")
            return f"Calendar event {action} successfully."

# Create global instance
llm_handler = LLMHandler()