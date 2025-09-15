import os
from typing import Dict, Any, Optional, Tuple
from core.llm_handler import llm_handler
from core.speech_to_text import stt_service
from core.text_to_speech import tts_service
from services.calendar_service import calendar_service
from services.email_service import email_service
from services.image_generator import image_generator
from services.image_editor import image_editor
from utils.response_formatter import ResponseFormatter
from config.settings import settings
from config.logging_config import get_logger

logger = get_logger('ai_agent')

class AIAgentBrain:
    """Main AI Agent that coordinates all services"""
    
    def __init__(self):
        """Initialize the AI Agent Brain"""
        self.response_formatter = ResponseFormatter()
        self.conversation_context = {}
        logger.info("AIAgentBrain initialized")
    
    async def process_message(
        self, 
        user_id: str, 
        message_text: Optional[str] = None,
        audio_file_path: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Process user message (text or audio) and return appropriate response
        
        Args:
            user_id (str): Unique identifier for the user
            message_text (Optional[str]): Text message from user
            audio_file_path (Optional[str]): Path to audio file from user
            
        Returns:
            Dict[str, Any]: Response containing text and audio paths
        """
        try:
            logger.info(f"Processing message from user {user_id}")
            
            # Step 1: Convert audio to text if provided
            if audio_file_path and not message_text:
                logger.info("Converting audio to text...")
                message_text = await stt_service.transcribe_audio(audio_file_path)
                
                if not message_text:
                    return self.response_formatter.create_error_response(
                        "Sorry, I couldn't understand the audio. Please try again."
                    )
            
            if not message_text:
                return self.response_formatter.create_error_response(
                    "Please provide either text or audio input."
                )
            
            # Step 2: Get user context
            context = self.conversation_context.get(user_id, {})
            
            # Step 3: Process with LLM to determine intent and extract parameters
            logger.info("Processing input with LLM...")
            llm_response = await llm_handler.process_user_input(message_text, context)
            
            if not llm_response:
                return self.response_formatter.create_error_response(
                    "Sorry, I couldn't process your request. Please try again."
                )
            
            # Log the LLM response for debugging
            logger.info(f"LLM Response: {llm_response}")
            
            # Step 4: Update conversation context
            self.conversation_context[user_id] = {
                "last_intent": llm_response.get("intent"),
                "last_parameters": llm_response.get("parameters", {}),
                "conversation_history": context.get("conversation_history", [])
            }
            
            # Step 5: Execute the appropriate action based on intent
            intent = llm_response.get("intent")
            parameters = llm_response.get("parameters", {})
            
            logger.info(f"Executing action for intent: {intent}")
            
            if intent.startswith("calendar_"):
                response = await self._handle_calendar_operation(intent, parameters, user_id)
            elif intent.startswith("email_"):
                response = await self._handle_email_operation(intent, parameters, user_id)
            elif intent.startswith("image_"):
                response = await self._handle_image_operation(intent, parameters, user_id)
            else:
                # General chat response
                response = {
                    "text": llm_response.get("response_text", "I'm here to help!"),
                    "success": True,
                    "requires_clarification": llm_response.get("requires_clarification", False),
                    "clarification_questions": llm_response.get("clarification_questions", [])
                }
            
            # Step 6: Generate audio response
            if response.get("success") and response.get("text"):
                logger.info("Generating audio response...")
                audio_path = await tts_service.generate_speech_for_response(response["text"])
                if audio_path:
                    response["audio_path"] = audio_path
            
            return response
            
        except Exception as e:
            logger.error(f"Error in process_message: {str(e)}")
            return self.response_formatter.create_error_response(
                "An error occurred while processing your request."
            )
    
    async def _handle_calendar_operation(
        self, 
        intent: str, 
        parameters: Dict[str, Any], 
        user_id: str
    ) -> Dict[str, Any]:
        """Handle calendar-related operations"""
        try:
            logger.info(f"Handling calendar operation: {intent}")
            
            if intent == "calendar_create":
                # Extract event details
                title = parameters.get("title")
                date = parameters.get("date")
                time = parameters.get("time")
                duration = parameters.get("duration", "1 hour")
                description = parameters.get("description", "")
                attendees = parameters.get("attendees", [])
                
                # Check for required parameters
                missing_params = []
                if not title:
                    missing_params.append("event title")
                if not date:
                    missing_params.append("date")
                if not time:
                    missing_params.append("time")
                
                if missing_params:
                    return {
                        "text": f"To create the event, I need: {', '.join(missing_params)}. Please provide these details.",
                        "success": False,
                        "requires_clarification": True,
                        "clarification_questions": [f"What is the {param}?" for param in missing_params]
                    }
                
                # Create the event
                event_result = await calendar_service.create_event(
                    title=title,
                    date=date,
                    time=time,
                    duration=duration,
                    description=description,
                    attendees=attendees
                )
                
                if event_result["success"]:
                    response_text = await llm_handler.format_calendar_event_response(
                        event_result["event_details"], "created"
                    )
                    
                    # Ask if user wants to send email reminders
                    if attendees:
                        response_text += f"\n\nWould you like me to send email reminders to the attendees ({', '.join(attendees)})?"
                    
                    return {
                        "text": response_text,
                        "success": True,
                        "event_details": event_result["event_details"]
                    }
                else:
                    return {
                        "text": f"Sorry, I couldn't create the event. {event_result.get('error', 'Unknown error')}",
                        "success": False
                    }
            
            elif intent == "calendar_get":
                # Get events based on parameters
                date = parameters.get("date")
                events_result = await calendar_service.get_events(date=date)
                
                if events_result["success"]:
                    events = events_result["events"]
                    if events:
                        response_text = f"Here are your events"
                        if date:
                            response_text += f" for {date}"
                        response_text += ":\n\n"
                        
                        for event in events:
                            response_text += f"• {event.get('title', 'Untitled')} - {event.get('start_time', 'Time TBD')}\n"
                    else:
                        response_text = "No events found"
                        if date:
                            response_text += f" for {date}"
                        response_text += "."
                    
                    return {
                        "text": response_text,
                        "success": True,
                        "events": events
                    }
                else:
                    return {
                        "text": f"Sorry, I couldn't retrieve your events. {events_result.get('error', 'Unknown error')}",
                        "success": False
                    }
            
            # Handle other calendar operations (update, delete) similarly...
            else:
                return {
                    "text": f"Calendar operation '{intent}' is not yet implemented.",
                    "success": False
                }
                
        except Exception as e:
            logger.error(f"Error handling calendar operation: {str(e)}")
            return {
                "text": "Sorry, there was an error with the calendar operation.",
                "success": False
            }
    
    async def _handle_email_operation(
        self, 
        intent: str, 
        parameters: Dict[str, Any], 
        user_id: str
    ) -> Dict[str, Any]:
        """Handle email-related operations"""
        try:
            logger.info(f"Handling email operation: {intent}")
            logger.info(f"Email parameters received: {parameters}")
            
            if intent == "email_send":
                # FIXED: Look for the correct parameter names that the LLM handler uses
                recipient_email = parameters.get("to_email")  # Changed from recipient_email
                subject = parameters.get("subject")
                body = parameters.get("body")
                message_content = parameters.get("message_content")
                purpose = parameters.get("purpose")
                
                # Use message_content as body if body is not available
                if not body and message_content:
                    body = message_content
                
                logger.info(f"Extracted email params - to: {recipient_email}, subject: {subject}, body: {body}")
                
                # Check for required parameters
                if not recipient_email:
                    return {
                        "text": "I need the recipient's email address to send the email.",
                        "success": False,
                        "requires_clarification": True,
                        "clarification_questions": ["What is the recipient's email address?"]
                    }
                
                # Generate email content if not provided
                if not subject or not body:
                    if purpose or message_content:
                        email_content = await llm_handler.create_email_content(
                            purpose=purpose or "message",
                            recipient_name="there",
                            additional_details=parameters
                        )
                        
                        if email_content:
                            subject = subject or email_content.get("subject")
                            body = body or email_content.get("body")
                
                # Provide defaults if still missing
                if not subject:
                    if body and len(body) > 5:
                        # Use first few words as subject
                        words = body.split()[:4]
                        subject = ' '.join(words).title()
                    else:
                        subject = "Message from AI Assistant"
                
                if not body:
                    body = "Hello, this is a message from your AI assistant."
                
                logger.info(f"Final email params - to: {recipient_email}, subject: {subject}")
                
                # Send the email
                email_result = await email_service.send_email(
                    to_email=recipient_email,
                    subject=subject,
                    body=body
                )
                
                if email_result["success"]:
                    response_text = f"✅ Email sent successfully to {recipient_email}!\n\n"
                    response_text += f"Subject: {subject}\n"
                    response_text += f"Preview: {body[:100]}..."
                    
                    return {
                        "text": response_text,
                        "success": True,
                        "email_details": {
                            "to": recipient_email,
                            "subject": subject,
                            "body": body
                        }
                    }
                else:
                    return {
                        "text": f"Sorry, I couldn't send the email. {email_result.get('error', 'Unknown error')}",
                        "success": False
                    }
            
            elif intent == "email_get":
                # Handle email retrieval
                query = parameters.get("query", "is:inbox")
                max_results = parameters.get("max_results", 10)
                include_body = parameters.get("include_body", False)
                
                logger.info(f"Getting emails with query: {query}")
                
                # Call the email service
                result = await email_service.get_emails(
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
                    
                    formatted_response = await llm_handler.format_email_list_response(
                        emails, total_count, query_type
                    )
                    
                    return {
                        "text": formatted_response,
                        "success": True,
                        "emails": emails,
                        "total_count": total_count
                    }
                else:
                    error_message = f"Sorry, I couldn't retrieve your emails. Error: {result.get('error', 'Unknown error')}"
                    return {
                        "text": error_message,
                        "success": False,
                        "error": result.get('error')
                    }
            
            # Handle other email operations similarly...
            else:
                return {
                    "text": f"Email operation '{intent}' is not yet implemented.",
                    "success": False
                }
                
        except Exception as e:
            logger.error(f"Error handling email operation: {str(e)}")
            return {
                "text": "Sorry, there was an error with the email operation.",
                "success": False
            }
    
    async def _handle_image_operation(
        self, 
        intent: str, 
        parameters: Dict[str, Any], 
        user_id: str
    ) -> Dict[str, Any]:
        """Handle image-related operations"""
        try:
            logger.info(f"Handling image operation: {intent}")
            
            if intent == "image_generate":
                description = parameters.get("description")
                style = parameters.get("style", "")
                
                if not description:
                    return {
                        "text": "I need a description of the image you want me to create.",
                        "success": False,
                        "requires_clarification": True,
                        "clarification_questions": ["What image would you like me to generate?"]
                    }
                
                # Generate the image
                image_result = await image_generator.generate_image(description, style)
                
                if image_result["success"]:
                    return {
                        "text": f"🎨 I've created an image based on: '{description}'\n\nImage saved and ready to send!",
                        "success": True,
                        "image_path": image_result["image_path"],
                        "description": description
                    }
                else:
                    return {
                        "text": f"Sorry, I couldn't generate the image. {image_result.get('error', 'Unknown error')}",
                        "success": False
                    }
            
            elif intent == "image_edit":
                modifications = parameters.get("modifications")
                input_image = parameters.get("input_image")
                
                if not modifications:
                    return {
                        "text": "Please describe what changes you'd like me to make to the image.",
                        "success": False,
                        "requires_clarification": True,
                        "clarification_questions": ["What modifications would you like me to make?"]
                    }
                
                # Edit the image
                edit_result = await image_editor.edit_image(input_image, modifications)
                
                if edit_result["success"]:
                    return {
                        "text": f"🎨 I've modified the image based on: '{modifications}'\n\nEdited image is ready!",
                        "success": True,
                        "image_path": edit_result["image_path"],
                        "modifications": modifications
                    }
                else:
                    return {
                        "text": f"Sorry, I couldn't edit the image. {edit_result.get('error', 'Unknown error')}",
                        "success": False
                    }
            
            else:
                return {
                    "text": f"Image operation '{intent}' is not yet implemented.",
                    "success": False
                }
                
        except Exception as e:
            logger.error(f"Error handling image operation: {str(e)}")
            return {
                "text": "Sorry, there was an error with the image operation.",
                "success": False
            }

# Create global instance
ai_agent = AIAgentBrain()