import os
import re
from typing import Optional, Dict, Any, List
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
        return """You are an AI assistant that helps with calendar management, email management, and image creation/editing. Your job is to extract information from user requests and respond intelligently.

**CRITICAL RULES:**
1. ALWAYS extract as much information as possible from the user's message
2. NEVER ask for information that's already provided
3. Use smart defaults for missing information
4. Provide structured JSON responses for processing

**Smart Defaults:**
- Event Duration: 1 hour for meetings/interviews, 30 minutes for calls
- Event Title: Generate from context (e.g., "Interview Meeting", "Business Meeting")
- Time: Assume PM for business hours (1-6), AM for early times (6-11)
- Location: "Virtual/Online" unless specified
- Email Subject: Generate from context when not provided
- Email Body: Use provided message or generate professional content
- Image Style: "realistic" unless specified
- Image Size: "1024x1024" unless specified
- Image Quality: "high" unless specified

**Intent Recognition:**
- calendar_create: Creating events, meetings, appointments
- calendar_get: Checking schedule, viewing events
- calendar_update: Modifying existing events
- calendar_delete: Removing events
- email_send: Sending emails, reminders, messages
- email_get: Retrieving, checking, reading emails
- image_create: Creating new images from text descriptions (text-to-image)
- image_edit: Editing existing images with text prompts (image-to-image)
- image_generate: General image generation requests
- general_chat: Everything else

**Image Creation Parameters:**
For image creation requests, extract:
- prompt: Detailed description of the image to create (REQUIRED)
- style: Art style (e.g., "realistic", "cartoon", "anime", "oil painting", "digital art", "photographic")
- size: Image dimensions (e.g., "1024x1024", "512x512", "1024x512")
- quality: Image quality ("high", "medium", "low")
- negative_prompt: What to avoid in the image
- num_images: Number of images to generate (default: 1)
- aspect_ratio: Image aspect ratio if specified

**Image Editing Parameters:**
For image editing requests, extract:
- source_image: Path or reference to the source image
- edit_prompt: Description of the changes to make
- mask_prompt: Area to edit (if specific area mentioned)
- style: Target style for editing
- strength: How strong the edit should be (0.1 to 1.0)

**Email Send Parameters:**
For email sending requests, extract:
- to_email: Recipient email address (REQUIRED)
- subject: Email subject line (generate if not provided)
- body: Email message content
- message_content: Raw message to be sent
- purpose: Purpose/context of the email

**Email Get Parameters:**
For email retrieval requests, extract:
- query: Gmail search terms (e.g., "today", "unread", "from:someone@email.com")
- max_results: Number of emails (default: 10)
- include_body: Whether to include full email content (default: false)
- time_filter: Time-based filters like "today", "this week", "yesterday"

**Response Format:**
Always respond with valid JSON in this exact format:
{
    "intent": "intent_type",
    "confidence": 0.95,
    "parameters": {
        "extracted_parameters": "here"
    },
    "response_text": "Your conversational response",
    "requires_clarification": false,
    "clarification_questions": [],
    "suggested_actions": []
}

**Parameter Extraction Examples:**

Input: "create an image of a boy flying in the sky"
Parameters: {
    "prompt": "a boy flying in the sky",
    "style": "realistic",
    "size": "1024x1024",
    "quality": "high",
    "num_images": 1
}

Input: "I want to create a Image boy flying the sky"
Parameters: {
    "prompt": "boy flying the sky",
    "style": "realistic",
    "size": "1024x1024",
    "quality": "high",
    "num_images": 1
}

Input: "generate a cartoon style image of a cat sitting on a chair"
Parameters: {
    "prompt": "cat sitting on a chair",
    "style": "cartoon",
    "size": "1024x1024",
    "quality": "high",
    "num_images": 1
}

Input: "create 3 images of a sunset over mountains in oil painting style"
Parameters: {
    "prompt": "sunset over mountains",
    "style": "oil painting",
    "size": "1024x1024",
    "quality": "high",
    "num_images": 3
}

Input: "edit this image to make the sky more blue"
Parameters: {
    "edit_prompt": "make the sky more blue",
    "style": "realistic",
    "strength": 0.7
}

Input: "send email to john@example.com with subject hello and message this is a test"
Parameters: {
    "to_email": "john@example.com",
    "subject": "hello",
    "body": "this is a test",
    "message_content": "this is a test"
}

Input: "create event interview meeting tomorrow at 4 PM"
Parameters: {
    "title": "Interview Meeting",
    "date": "tomorrow", 
    "time": "4 PM",
    "duration": "1 hour"
}

Input: "What emails came today?"
Parameters: {
    "query": "is:inbox newer_than:1d",
    "max_results": 20,
    "include_body": false,
    "time_filter": "today"
}"""

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
            
            # First try regex-based extraction for common patterns (faster and more reliable)
            email_result = self._extract_email_intent(user_input)
            if email_result:
                logger.info("Email intent detected via regex")
                return email_result
            
            # Check for image-related keywords
            image_result = self._extract_image_intent(user_input)
            if image_result:
                logger.info("Image intent detected via regex")
                return image_result
            
            # Create a focused prompt for intent recognition
            analysis_prompt = f"""
{self.system_prompt}

User Input: "{user_input}"

Analyze this input and extract all possible information. Respond with JSON only (no extra text):

Examples:
Input: "create an image of a boy flying in the sky"
Output: {{
    "intent": "image_create",
    "confidence": 0.95,
    "parameters": {{
        "prompt": "a boy flying in the sky",
        "style": "realistic",
        "size": "1024x1024",
        "quality": "high",
        "num_images": 1
    }},
    "response_text": "I'll create an image of a boy flying in the sky for you.",
    "requires_clarification": false,
    "clarification_questions": [],
    "suggested_actions": ["create_image"]
}}

Input: "I want to create a Image boy flying the sky"
Output: {{
    "intent": "image_create",
    "confidence": 0.95,
    "parameters": {{
        "prompt": "boy flying the sky",
        "style": "realistic",
        "size": "1024x1024",
        "quality": "high",
        "num_images": 1
    }},
    "response_text": "I'll create an image of a boy flying in the sky for you.",
    "requires_clarification": false,
    "clarification_questions": [],
    "suggested_actions": ["create_image"]
}}

Input: "send email to john@example.com with subject hello and message this is a test"
Output: {{
    "intent": "email_send",
    "confidence": 0.95,
    "parameters": {{
        "to_email": "john@example.com",
        "subject": "hello",
        "body": "this is a test",
        "message_content": "this is a test"
    }},
    "response_text": "I'll send an email to john@example.com with subject 'hello' and your message.",
    "requires_clarification": false,
    "clarification_questions": [],
    "suggested_actions": ["send_email"]
}}

Now analyze: "{user_input}"
"""

            # Send to Gemini for processing
            response = self.client.models.generate_content(
                model=self.model,
                contents=analysis_prompt
            )
            
            if not response or not response.text:
                logger.error("Empty response from LLM")
                return self._create_fallback_response(user_input)
            
            # Parse the JSON response
            return self._parse_llm_response(response.text, user_input)
                
        except Exception as e:
            logger.error(f"Error processing user input with LLM: {str(e)}")
            return self._create_fallback_response(user_input)
    
    def _extract_image_intent(self, user_input: str) -> Optional[Dict[str, Any]]:
        """
        Extract image creation intent using regex patterns
        
        Args:
            user_input (str): User input text
            
        Returns:
            Optional[Dict[str, Any]]: Extracted image parameters or None
        """
        try:
            user_lower = user_input.lower()
            
            # Check for image creation keywords
            image_create_keywords = [
                'create', 'generate', 'make', 'draw', 'paint', 'design', 'produce'
            ]
            image_nouns = [
                'image', 'picture', 'photo', 'artwork', 'drawing', 'painting', 'illustration'
            ]
            
            # Check if it's an image creation request
            has_create_keyword = any(keyword in user_lower for keyword in image_create_keywords)
            has_image_keyword = any(keyword in user_lower for keyword in image_nouns)
            
            # Also check for direct patterns like "I want to create a Image"
            direct_patterns = [
                r'(?:create|generate|make|draw)\s+(?:an?\s+)?(?:image|picture|photo|artwork|drawing|painting|illustration)',
                r'(?:i\s+want\s+to\s+)?(?:create|generate|make|draw)\s+(?:a\s+)?(?:image|picture|photo)',
                r'(?:text\s+to\s+image|image\s+generation|ai\s+art)'
            ]
            
            is_image_request = has_create_keyword and has_image_keyword
            for pattern in direct_patterns:
                if re.search(pattern, user_lower):
                    is_image_request = True
                    break
            
            if not is_image_request:
                return None
            
            # Extract the prompt (description of what to create)
            prompt = self._extract_image_prompt(user_input)
            if not prompt:
                return None
            
            # Extract style if mentioned
            style = "realistic"  # default
            style_patterns = {
                'cartoon': r'cartoon|anime|animated',
                'realistic': r'realistic|photographic|photo',
                'digital art': r'digital\s+art|digital',
                'oil painting': r'oil\s+painting|painting',
                'watercolor': r'watercolor|water\s+color',
                'sketch': r'sketch|pencil|drawing',
                'abstract': r'abstract',
                'vintage': r'vintage|retro|old',
                'modern': r'modern|contemporary'
            }
            
            for style_name, pattern in style_patterns.items():
                if re.search(pattern, user_lower):
                    style = style_name
                    break
            
            # Extract number of images
            num_images = 1
            num_match = re.search(r'(\d+)\s+images?', user_lower)
            if num_match:
                num_images = int(num_match.group(1))
                num_images = min(num_images, 4)  # Limit to 4 images max
            
            # Extract size if mentioned
            size = "1024x1024"  # default
            size_patterns = [
                r'(\d+x\d+)',
                r'(\d+\s*[x×]\s*\d+)',
            ]
            
            for pattern in size_patterns:
                match = re.search(pattern, user_input)
                if match:
                    size = match.group(1).replace(' ', '').replace('×', 'x')
                    break
            
            return {
                "intent": "image_create",
                "confidence": 0.9,
                "parameters": {
                    "prompt": prompt,
                    "style": style,
                    "size": size,
                    "quality": "high",
                    "num_images": num_images
                },
                "response_text": f"I'll create {'an image' if num_images == 1 else f'{num_images} images'} of {prompt} in {style} style for you.",
                "requires_clarification": False,
                "clarification_questions": [],
                "suggested_actions": ["create_image"]
            }
            
        except Exception as e:
            logger.error(f"Error in regex image extraction: {str(e)}")
            return None
    
    def _extract_image_prompt(self, user_input: str) -> Optional[str]:
        """Extract the image description from user input"""
        try:
            # Remove common prefixes and extract the actual description
            cleaned_input = user_input.lower()
            
            # Patterns to remove from the beginning
            removal_patterns = [
                r'^(?:i\s+want\s+to\s+)?(?:create|generate|make|draw|paint|design|produce)\s+(?:an?\s+)?(?:image|picture|photo|artwork|drawing|painting|illustration)\s+(?:of\s+)?',
                r'^(?:create|generate|make|draw|paint|design|produce)\s+(?:an?\s+)?(?:image|picture|photo|artwork|drawing|painting|illustration)\s+(?:of\s+)?',
                r'^(?:i\s+want\s+to\s+)?(?:create|generate|make|draw)\s+(?:a\s+)?(?:image|picture|photo)\s+',
                r'^(?:can\s+you\s+)?(?:create|generate|make|draw)\s+'
            ]
            
            description = user_input
            for pattern in removal_patterns:
                description = re.sub(pattern, '', description, flags=re.IGNORECASE).strip()
            
            # Remove style information and other modifiers to get clean prompt
            style_removals = [
                r'\s+in\s+(?:cartoon|realistic|digital\s+art|oil\s+painting|watercolor|sketch|abstract|vintage|modern)\s+style',
                r'\s+style\s*$',
                r'\s+(?:\d+x\d+|\d+\s*[x×]\s*\d+)',
                r'\s+(?:high|low|medium)\s+quality',
                r'\s+\d+\s+images?'
            ]
            
            for pattern in style_removals:
                description = re.sub(pattern, '', description, flags=re.IGNORECASE).strip()
            
            # Clean up extra spaces and common words
            description = re.sub(r'\s+', ' ', description).strip()
            description = re.sub(r'^(?:a\s+|an\s+|the\s+)', '', description, flags=re.IGNORECASE).strip()
            
            return description if len(description) > 2 else None
            
        except Exception as e:
            logger.error(f"Error extracting image prompt: {str(e)}")
            return None

    def _extract_email_intent(self, user_input: str) -> Optional[Dict[str, Any]]:
        """
        Extract email sending intent using regex patterns
        
        Args:
            user_input (str): User input text
            
        Returns:
            Optional[Dict[str, Any]]: Extracted email parameters or None
        """
        try:
            user_lower = user_input.lower()
            
            # Check for email sending keywords
            email_send_keywords = ['send', 'email', 'mail', 'message', 'write to', 'contact']
            if not any(keyword in user_lower for keyword in email_send_keywords):
                return None
            
            # Extract email addresses
            email_pattern = r'([a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,})'
            emails = re.findall(email_pattern, user_input)
            
            if not emails:
                return None
            
            to_email = emails[0]  # Take the first email found
            
            # Extract subject and body
            subject = None
            body = None
            message_content = None
            
            # Look for explicit subject patterns
            subject_patterns = [
                r'with\s+subject\s+["\']?([^"\']+)["\']?',
                r'subject:\s*["\']?([^"\']+)["\']?',
                r'subject\s+["\']?([^"\']+)["\']?'
            ]
            
            for pattern in subject_patterns:
                match = re.search(pattern, user_input, re.IGNORECASE)
                if match:
                    subject = match.group(1).strip()
                    break
            
            # Extract message content
            message_patterns = [
                r'say\s+to\s+him\s+(.+?)(?:\s+(?:with|and)|$)',
                r'say\s+to\s+her\s+(.+?)(?:\s+(?:with|and)|$)',
                r'say\s+(.+?)(?:\s+(?:with|and)|$)',
                r'message\s+["\']?([^"\']+)["\']?',
                r'tell\s+(?:him|her|them)\s+(.+?)(?:\s+(?:with|and)|$)',
                r'write\s+(.+?)(?:\s+(?:with|and)|$)'
            ]
            
            for pattern in message_patterns:
                match = re.search(pattern, user_input, re.IGNORECASE)
                if match:
                    message_content = match.group(1).strip()
                    # Clean up common endings
                    message_content = re.sub(r'\s+to\s+' + re.escape(to_email) + r'.*$', '', message_content, flags=re.IGNORECASE)
                    body = message_content
                    break
            
            # If no specific message found, try to extract everything after "email to"
            if not body:
                after_email_pattern = r'email\s+to\s+' + re.escape(to_email) + r'\s+(.+?)$'
                match = re.search(after_email_pattern, user_input, re.IGNORECASE)
                if match:
                    remaining_text = match.group(1).strip()
                    # Remove common words like "say", "tell", "with"
                    remaining_text = re.sub(r'^(?:say\s+to\s+(?:him|her|them)\s+|tell\s+(?:him|her|them)\s+|say\s+|tell\s+|with\s+)', '', remaining_text, flags=re.IGNORECASE)
                    if remaining_text:
                        body = remaining_text
                        message_content = remaining_text
            
            # Generate default subject if not found
            if not subject:
                if message_content and len(message_content) > 5:
                    # Use first few words as subject
                    words = message_content.split()[:4]
                    subject = ' '.join(words).title()
                else:
                    subject = "Message from AI Assistant"
            
            # Generate default body if not found
            if not body:
                body = "Hello, this is a message from your AI assistant."
                message_content = body
            
            return {
                "intent": "email_send",
                "confidence": 0.9,
                "parameters": {
                    "to_email": to_email,
                    "subject": subject,
                    "body": body,
                    "message_content": message_content,
                    "purpose": "direct message"
                },
                "response_text": f"I'll send an email to {to_email} with the subject '{subject}' and your message.",
                "requires_clarification": False,
                "clarification_questions": [],
                "suggested_actions": ["send_email"]
            }
            
        except Exception as e:
            logger.error(f"Error in regex email extraction: {str(e)}")
            return None
    
    def _parse_llm_response(self, response_text: str, user_input: str) -> Dict[str, Any]:
        """Parse LLM response and extract JSON"""
        try:
            import json
            
            # Clean the response text
            response_text = response_text.strip()
            
            # Try to find JSON in the response
            json_patterns = [
                r'```json\s*(.*?)\s*```',  # JSON in code blocks
                r'```\s*(.*?)\s*```',      # Generic code blocks
                r'(\{.*\})',               # Direct JSON objects
            ]
            
            json_text = None
            for pattern in json_patterns:
                match = re.search(pattern, response_text, re.DOTALL)
                if match:
                    json_text = match.group(1)
                    break
            
            if not json_text:
                json_text = response_text
            
            # Parse JSON
            parsed_response = json.loads(json_text)
            
            # Validate required fields
            if not isinstance(parsed_response, dict):
                raise ValueError("Response is not a dictionary")
            
            # Ensure required fields exist
            parsed_response.setdefault("intent", "general_chat")
            parsed_response.setdefault("confidence", 0.7)
            parsed_response.setdefault("parameters", {})
            parsed_response.setdefault("response_text", "I'll help you with that.")
            parsed_response.setdefault("requires_clarification", False)
            parsed_response.setdefault("clarification_questions", [])
            parsed_response.setdefault("suggested_actions", [])
            
            logger.info(f"LLM analysis complete - Intent: {parsed_response.get('intent')}")
            return parsed_response
            
        except (json.JSONDecodeError, ValueError) as e:
            logger.error(f"Failed to parse LLM JSON response: {e}")
            logger.error(f"Raw response: {response_text}")
            return self._create_fallback_response(user_input)
    
    def _create_fallback_response(self, user_input: str) -> Dict[str, Any]:
        """Create a fallback response when parsing fails"""
        
        # Simple keyword-based intent detection as fallback
        user_lower = user_input.lower()
        
        # Check for image creation keywords first
        image_create_keywords = ['create', 'generate', 'make', 'draw', 'paint', 'design', 'produce']
        image_nouns = ['image', 'picture', 'photo', 'artwork', 'drawing', 'painting', 'illustration']
        
        if any(keyword in user_lower for keyword in image_create_keywords) and any(keyword in user_lower for keyword in image_nouns):
            # Try to extract image prompt
            prompt = self._extract_image_prompt(user_input)
            if prompt:
                return {
                    "intent": "image_create",
                    "confidence": 0.8,
                    "parameters": {
                        "prompt": prompt,
                        "style": "realistic",
                        "size": "1024x1024",
                        "quality": "high",
                        "num_images": 1
                    },
                    "response_text": f"I'll create an image of {prompt} for you.",
                    "requires_clarification": False,
                    "clarification_questions": [],
                    "suggested_actions": ["create_image"]
                }
        
        # Check for email sending keywords
        email_send_keywords = ['send', 'email', 'mail', 'message', 'write to', 'contact']
        if any(keyword in user_lower for keyword in email_send_keywords):
            # Try to extract email address
            email_pattern = r'([a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,})'
            emails = re.findall(email_pattern, user_input)
            
            if emails:
                to_email = emails[0]
                
                # Try to extract message content
                message_content = ""
                message_patterns = [
                    r'say\s+to\s+(?:him|her|them)\s+(.+?)(?:\s+(?:with|and)|$)',
                    r'say\s+(.+?)(?:\s+(?:with|and)|$)',
                    r'message\s+["\']?([^"\']+)["\']?',
                    r'tell\s+(?:him|her|them)\s+(.+?)(?:\s+(?:with|and)|$)'
                ]
                
                for pattern in message_patterns:
                    match = re.search(pattern, user_input, re.IGNORECASE)
                    if match:
                        message_content = match.group(1).strip()
                        break
                
                if not message_content:
                    message_content = "Hello, this is a message from your AI assistant."
                
                # Generate subject
                words = message_content.split()[:4]
                subject = ' '.join(words).title() if words else "Message"
                
                return {
                    "intent": "email_send",
                    "confidence": 0.8,
                    "parameters": {
                        "to_email": to_email,
                        "subject": subject,
                        "body": message_content,
                        "message_content": message_content,
                        "purpose": "direct message"
                    },
                    "response_text": f"I'll send an email to {to_email} with your message.",
                    "requires_clarification": False,
                    "clarification_questions": [],
                    "suggested_actions": ["send_email"]
                }
        
        # Check for email-related keywords for retrieval
        email_keywords = ['email', 'emails', 'inbox', 'unread', 'messages', 'mail']
        email_action_keywords = ['show', 'check', 'get', 'read', 'list', 'came', 'received']
        
        if any(word in user_lower for word in email_keywords) and any(word in user_lower for word in email_action_keywords):
            # Extract basic email parameters
            parameters = {
                "max_results": 10,
                "include_body": False
            }
            
            # Determine query based on keywords
            if 'today' in user_lower:
                parameters["query"] = "is:inbox newer_than:1d"
                parameters["time_filter"] = "today"
                parameters["max_results"] = 20
            elif 'unread' in user_lower:
                parameters["query"] = "is:unread"
            elif 'yesterday' in user_lower:
                parameters["query"] = "is:inbox newer_than:2d older_than:1d"
                parameters["time_filter"] = "yesterday"
            else:
                parameters["query"] = "is:inbox"
            
            return {
                "intent": "email_get",
                "confidence": 0.8,
                "parameters": parameters,
                "response_text": "I'll check your emails for you.",
                "requires_clarification": False,
                "clarification_questions": [],
                "suggested_actions": ["get_emails"]
            }
        
        # Check for calendar creation keywords
        elif any(word in user_lower for word in ['create', 'add', 'schedule', 'meeting', 'event', 'appointment']):
            # Try to extract basic info for calendar creation
            
            # Extract potential time patterns
            time_patterns = [
                r'(\d{1,2}:\d{2}\s*(?:am|pm))',
                r'(\d{1,2}\s*(?:am|pm))',
                r'(\d{1,2}:\d{2})',
            ]
            
            time_found = None
            for pattern in time_patterns:
                match = re.search(pattern, user_input, re.IGNORECASE)
                if match:
                    time_found = match.group(1)
                    break
            
            # Extract date patterns
            date_patterns = [
                r'(tomorrow)',
                r'(today)',
                r'(next\s+\w+)',
                r'(\w+day)',
            ]
            
            date_found = None
            for pattern in date_patterns:
                match = re.search(pattern, user_input, re.IGNORECASE)
                if match:
                    date_found = match.group(1)
                    break
            
            # Extract email patterns
            email_pattern = r'([a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,})'
            emails = re.findall(email_pattern, user_input)
            
            # Determine title
            title = "Meeting"
            if "interview" in user_lower:
                title = "Interview Meeting"
            elif "call" in user_lower:
                title = "Call"
            elif "appointment" in user_lower:
                title = "Appointment"
            
            parameters = {"title": title}
            if date_found:
                parameters["date"] = date_found
            if time_found:
                parameters["time"] = time_found
            if emails:
                parameters["attendees"] = emails
            parameters["duration"] = "1 hour"
            
            return {
                "intent": "calendar_create",
                "confidence": 0.8,
                "parameters": parameters,
                "response_text": f"I'll create a {title}" + 
                                (f" for {date_found}" if date_found else "") +
                                (f" at {time_found}" if time_found else "") +
                                (f" with {', '.join(emails)}" if emails else "") +
                                ". Shall I proceed?",
                "requires_clarification": False,
                "clarification_questions": [],
                "suggested_actions": ["create_calendar_event"]
            }
        
        return {
            "intent": "general_chat",
            "confidence": 0.7,
            "parameters": {},
            "response_text": "I can help you with calendar events, emails, and image creation. Could you be more specific about what you'd like me to do?",
            "requires_clarification": False,
            "clarification_questions": [],
            "suggested_actions": []
        }
    
    # Rest of the methods remain the same...
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
    
    async def create_image_prompt_enhancement(
        self,
        basic_prompt: str,
        style: str = "realistic",
        additional_details: Optional[Dict[str, Any]] = None
    ) -> str:
        """
        Enhance a basic image prompt with more detailed descriptions
        
        Args:
            basic_prompt (str): Basic image description
            style (str): Desired art style
            additional_details (Optional[Dict[str, Any]]): Additional context
            
        Returns:
            str: Enhanced prompt for better image generation
        """
        try:
            logger.info(f"Enhancing image prompt: {basic_prompt}")
            
            enhancement_prompt = f"""
You are an expert at creating detailed prompts for AI image generation. 
Enhance this basic prompt to create a more detailed and effective image generation prompt.

Basic prompt: "{basic_prompt}"
Style: {style}
Additional details: {additional_details or {}}

Guidelines for enhancement:
- Add relevant visual details (lighting, composition, colors)
- Include style-specific keywords
- Add quality enhancers
- Keep the core concept intact
- Make it suitable for AI image generation
- Don't make it overly complex

Return only the enhanced prompt, no additional text.
"""

            enhanced = await self.generate_response(enhancement_prompt, max_tokens=200)
            return enhanced.strip() if enhanced else basic_prompt
            
        except Exception as e:
            logger.error(f"Error enhancing image prompt: {str(e)}")
            return basic_prompt
    
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

    async def format_email_list_response(
        self,
        emails: List[Dict[str, Any]],
        total_count: int,
        query_type: str = "emails"
    ) -> str:
        """
        Format a response for email listing operations
        
        Args:
            emails (List[Dict[str, Any]]): List of email objects
            total_count (int): Total number of emails found
            query_type (str): Type of query (e.g., "today's emails", "unread emails")
            
        Returns:
            str: Formatted response text
        """
        try:
            if not emails:
                return f"No {query_type} found."
            
            response = f"Found {total_count} {query_type}:\n\n"
            
            for i, email in enumerate(emails[:10], 1):  # Show max 10 emails in summary
                sender = email.get('sender', 'Unknown Sender')
                # Clean sender name (remove email part if present)
                if '<' in sender:
                    sender = sender.split('<')[0].strip()
                
                subject = email.get('subject', 'No Subject')
                snippet = email.get('snippet', '')
                date = email.get('date', '')
                
                # Format date if available
                formatted_date = ""
                if date:
                    try:
                        from datetime import datetime
                        # Basic date formatting - you might want to improve this
                        formatted_date = f" - {date.split(',')[1].strip() if ',' in date else date}"
                    except:
                        formatted_date = f" - {date}"
                
                response += f"{i}. **{subject}**\n"
                response += f"   From: {sender}{formatted_date}\n"
                if snippet:
                    response += f"   Preview: {snippet[:80]}{'...' if len(snippet) > 80 else ''}\n"
                response += "\n"
            
            if total_count > 10:
                response += f"... and {total_count - 10} more emails.\n"
            
            response += "\nWould you like me to help you with any specific email operations?"
            
            return response
            
        except Exception as e:
            logger.error(f"Error formatting email list response: {str(e)}")
            return f"Found {total_count} {query_type}. Use specific commands to interact with them."
    
    async def format_image_creation_response(
        self,
        image_details: Dict[str, Any],
        success: bool = True,
        image_path: Optional[str] = None
    ) -> str:
        """
        Format a response for image creation operations
        
        Args:
            image_details (Dict[str, Any]): Image creation details
            success (bool): Whether the operation was successful
            image_path (Optional[str]): Path to the created image
            
        Returns:
            str: Formatted response text
        """
        try:
            if not success:
                return f"I encountered an issue creating the image. Please try again with a different prompt."
            
            prompt = image_details.get('prompt', 'your request')
            style = image_details.get('style', 'realistic')
            num_images = image_details.get('num_images', 1)
            
            response = f"✅ Successfully created {'an image' if num_images == 1 else f'{num_images} images'} of '{prompt}' in {style} style!"
            
            if image_path:
                response += f"\n\n📁 Image saved at: {image_path}"
            
            response += f"\n\n🎨 Style: {style.title()}"
            response += f"\n📐 Size: {image_details.get('size', '1024x1024')}"
            response += f"\n⚡ Quality: {image_details.get('quality', 'high').title()}"
            
            response += "\n\nWould you like me to create any variations or make any adjustments to the image?"
            
            return response
            
        except Exception as e:
            logger.error(f"Error formatting image creation response: {str(e)}")
            return "Image created successfully!"

# Create global instance
llm_handler = LLMHandler()