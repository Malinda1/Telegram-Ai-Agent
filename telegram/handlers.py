import os
from telegram import Update
from telegram.ext import ContextTypes
from core.agent_brain import ai_agent
from utils.file_handler import file_handler
from utils.response_formatter import response_formatter
from config.logging_config import get_logger

logger = get_logger('telegram_bot')

class TelegramHandlers:
    """Telegram bot message handlers"""
    
    def __init__(self):
        """Initialize Telegram Handlers"""
        logger.info("TelegramHandlers initialized")
    
    async def start_handler(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle /start command"""
        try:
            user = update.effective_user
            user_name = user.first_name or "there"
            
            welcome_message = f"""👋 Hello {user_name}! 

I'm your AI Assistant, ready to help with:

📅 **Calendar Management**
• Create, update, and manage your events
• Send meeting reminders

📧 **Email Operations** 
• Send professional emails
• Read and organize your inbox

🎨 **Image Generation**
• Create images from text descriptions
• Edit existing images

🎤 **Voice Support**
• Send voice messages - I'll understand them
• Get audio responses back

**Quick Start Examples:**
• "Create a meeting tomorrow at 9 AM"
• "Send email to john@example.com about the project"
• "Generate an image of a sunset"

Type /help anytime for more detailed instructions!

How can I help you today?"""

            await update.message.reply_text(welcome_message)
            logger.info(f"Start command handled for user: {user.id}")
            
        except Exception as e:
            logger.error(f"Error in start handler: {str(e)}")
            await update.message.reply_text("Sorry, there was an error. Please try again.")
    
    async def help_handler(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle /help command"""
        try:
            help_response = response_formatter.format_help_response()
            await update.message.reply_text(help_response["text"], parse_mode='Markdown')
            
            logger.info(f"Help command handled for user: {update.effective_user.id}")
            
        except Exception as e:
            logger.error(f"Error in help handler: {str(e)}")
            await update.message.reply_text("Sorry, there was an error showing help. Please try again.")
    
    async def text_message_handler(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle text messages"""
        try:
            user_id = str(update.effective_user.id)
            message_text = update.message.text
            
            logger.info(f"Processing text message from user {user_id}: {message_text[:100]}...")
            
            # Show typing indicator
            await context.bot.send_chat_action(chat_id=update.effective_chat.id, action="typing")
            
            # Process message with AI agent
            response = await ai_agent.process_message(user_id=user_id, message_text=message_text)
            
            # Send text response
            if response.get("text"):
                await update.message.reply_text(response["text"])
            
            # Send audio response if available
            if response.get("audio_path") and os.path.exists(response["audio_path"]):
                try:
                    with open(response["audio_path"], 'rb') as audio_file:
                        await update.message.reply_audio(audio=audio_file)
                    
                    # Clean up audio file
                    file_handler.delete_file(response["audio_path"])
                    
                except Exception as e:
                    logger.error(f"Error sending audio response: {str(e)}")
            
            # Send image if available
            if response.get("image_path") and os.path.exists(response["image_path"]):
                try:
                    with open(response["image_path"], 'rb') as image_file:
                        caption = response.get("description", "Generated image")
                        await update.message.reply_photo(photo=image_file, caption=caption)
                    
                    logger.info(f"Image sent successfully: {response['image_path']}")
                    
                except Exception as e:
                    logger.error(f"Error sending image: {str(e)}")
            
            logger.info(f"Text message processed successfully for user {user_id}")
            
        except Exception as e:
            logger.error(f"Error in text message handler: {str(e)}")
            await update.message.reply_text("Sorry, I encountered an error processing your message. Please try again.")
    
    async def voice_message_handler(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle voice messages"""
        try:
            user_id = str(update.effective_user.id)
            voice = update.message.voice
            
            logger.info(f"Processing voice message from user {user_id}")
            
            # Show typing indicator
            await context.bot.send_chat_action(chat_id=update.effective_chat.id, action="typing")
            
            # Download voice file
            voice_file = await voice.get_file()
            voice_data = await voice_file.download_as_bytearray()
            
            # Save voice file
            audio_path = file_handler.save_telegram_audio(voice_file.file_path, voice_data)
            
            if not audio_path:
                await update.message.reply_text("Sorry, I couldn't process your voice message. Please try again.")
                return
            
            # Process voice message with AI agent
            response = await ai_agent.process_message(user_id=user_id, audio_file_path=audio_path)
            
            # Clean up original audio file
            file_handler.delete_file(audio_path)
            
            # Send text response
            if response.get("text"):
                await update.message.reply_text(response["text"])
            
            # Send audio response if available
            if response.get("audio_path") and os.path.exists(response["audio_path"]):
                try:
                    with open(response["audio_path"], 'rb') as audio_file:
                        await update.message.reply_audio(audio=audio_file)
                    
                    # Clean up response audio file
                    file_handler.delete_file(response["audio_path"])
                    
                except Exception as e:
                    logger.error(f"Error sending audio response: {str(e)}")
            
            # Send image if available
            if response.get("image_path") and os.path.exists(response["image_path"]):
                try:
                    with open(response["image_path"], 'rb') as image_file:
                        caption = response.get("description", "Generated image")
                        await update.message.reply_photo(photo=image_file, caption=caption)
                    
                    logger.info(f"Image sent successfully: {response['image_path']}")
                    
                except Exception as e:
                    logger.error(f"Error sending image: {str(e)}")
            
            logger.info(f"Voice message processed successfully for user {user_id}")
            
        except Exception as e:
            logger.error(f"Error in voice message handler: {str(e)}")
            await update.message.reply_text("Sorry, I couldn't process your voice message. Please try again.")
    
    async def photo_message_handler(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle photo messages (for image editing)"""
        try:
            user_id = str(update.effective_user.id)
            photo = update.message.photo[-1]  # Get highest resolution photo
            caption = update.message.caption or ""
            
            logger.info(f"Processing photo message from user {user_id}")
            
            # Show typing indicator
            await context.bot.send_chat_action(chat_id=update.effective_chat.id, action="typing")
            
            # Download photo
            photo_file = await photo.get_file()
            photo_data = await photo_file.download_as_bytearray()
            
            # Save photo file
            image_path = file_handler.save_telegram_image(photo_file.file_path, photo_data)
            
            if not image_path:
                await update.message.reply_text("Sorry, I couldn't process your image. Please try again.")
                return
            
            # If caption contains editing instructions, process as image edit
            if caption and any(word in caption.lower() for word in ['edit', 'change', 'modify', 'update', 'turn']):
                # Process as image editing request
                message_text = f"Edit this image: {caption}"
                
                # Include the uploaded image path in the response for the image editing service
                response = await ai_agent.process_message(
                    user_id=user_id,
                    message_text=message_text
                )
                
                # If this is an image edit request, use the uploaded image
                if response.get("success") and "image_edit" in str(response.get("data", {})):
                    try:
                        from services.image_editor import image_editor
                        edit_result = await image_editor.edit_image(image_path, caption)
                        
                        if edit_result["success"]:
                            response["image_path"] = edit_result["image_path"]
                            response["text"] = f"🎨 I've edited your image based on: '{caption}'\n\nHere's the result!"
                        else:
                            response["text"] = f"Sorry, I couldn't edit your image: {edit_result.get('error', 'Unknown error')}"
                            
                    except Exception as e:
                        logger.error(f"Error editing uploaded image: {str(e)}")
                        response["text"] = "Sorry, I encountered an error while editing your image."
                    
            else:
                # Just acknowledge the image
                response = {
                    "success": True,
                    "text": "📸 I received your image! If you'd like me to edit it, please send it again with a caption describing what changes you want me to make.\n\nExample: Send the image with caption 'change the sky to purple' or 'make it look like a painting'"
                }
            
            # Send text response
            if response.get("text"):
                await update.message.reply_text(response["text"])
            
            # Send edited image if available
            if response.get("image_path") and os.path.exists(response["image_path"]):
                try:
                    with open(response["image_path"], 'rb') as image_file:
                        await update.message.reply_photo(photo=image_file, caption="Here's your edited image!")
                    
                    logger.info(f"Edited image sent successfully")
                    
                except Exception as e:
                    logger.error(f"Error sending edited image: {str(e)}")
            
            # Clean up uploaded image
            file_handler.delete_file(image_path)
            
            # Clean up generated image if exists
            if response.get("image_path"):
                file_handler.delete_file(response["image_path"])
            
            logger.info(f"Photo message processed successfully for user {user_id}")
            
        except Exception as e:
            logger.error(f"Error in photo message handler: {str(e)}")
            await update.message.reply_text("Sorry, I couldn't process your image. Please try again.")
    
    async def document_message_handler(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle document messages"""
        try:
            user_id = str(update.effective_user.id)
            document = update.message.document
            
            logger.info(f"Processing document from user {user_id}: {document.file_name}")
            
            # Check if it's an audio or image file
            file_extension = os.path.splitext(document.file_name)[1].lower()
            
            if file_extension in file_handler.supported_audio_formats:
                # Handle as audio file
                await self._handle_audio_document(update, context, user_id, document)
            elif file_extension in file_handler.supported_image_formats:
                # Handle as image file
                await self._handle_image_document(update, context, user_id, document)
            else:
                await update.message.reply_text(
                    f"Sorry, I don't support {file_extension} files yet. "
                    f"I can work with audio files ({', '.join(file_handler.supported_audio_formats)}) "
                    f"and image files ({', '.join(file_handler.supported_image_formats)})."
                )
            
        except Exception as e:
            logger.error(f"Error in document message handler: {str(e)}")
            await update.message.reply_text("Sorry, I couldn't process your file. Please try again.")
    
    async def _handle_audio_document(self, update: Update, context: ContextTypes.DEFAULT_TYPE, user_id: str, document):
        """Handle audio document"""
        try:
            # Show typing indicator
            await context.bot.send_chat_action(chat_id=update.effective_chat.id, action="typing")
            
            # Download audio file
            audio_file = await document.get_file()
            audio_data = await audio_file.download_as_bytearray()
            
            # Save audio file
            audio_path = file_handler.save_telegram_audio(document.file_name, audio_data)
            
            if not audio_path:
                await update.message.reply_text("Sorry, I couldn't process your audio file. Please try again.")
                return
            
            # Process audio with AI agent
            response = await ai_agent.process_message(user_id=user_id, audio_file_path=audio_path)
            
            # Clean up original audio file
            file_handler.delete_file(audio_path)
            
            # Send response
            if response.get("text"):
                await update.message.reply_text(response["text"])
            
            # Send audio response if available
            if response.get("audio_path") and os.path.exists(response["audio_path"]):
                try:
                    with open(response["audio_path"], 'rb') as audio_response:
                        await update.message.reply_audio(audio=audio_response)
                    
                    file_handler.delete_file(response["audio_path"])
                    
                except Exception as e:
                    logger.error(f"Error sending audio response: {str(e)}")
            
            # Send image if available
            if response.get("image_path") and os.path.exists(response["image_path"]):
                try:
                    with open(response["image_path"], 'rb') as image_file:
                        caption = response.get("description", "Generated image")
                        await update.message.reply_photo(photo=image_file, caption=caption)
                    
                    file_handler.delete_file(response["image_path"])
                    
                except Exception as e:
                    logger.error(f"Error sending image: {str(e)}")
            
        except Exception as e:
            logger.error(f"Error handling audio document: {str(e)}")
            await update.message.reply_text("Sorry, I couldn't process your audio file.")
    
    async def _handle_image_document(self, update: Update, context: ContextTypes.DEFAULT_TYPE, user_id: str, document):
        """Handle image document"""
        try:
            caption = update.message.caption or ""
            
            # Show typing indicator
            await context.bot.send_chat_action(chat_id=update.effective_chat.id, action="typing")
            
            # Download image file
            image_file = await document.get_file()
            image_data = await image_file.download_as_bytearray()
            
            # Save image file
            image_path = file_handler.save_telegram_image(document.file_name, image_data)
            
            if not image_path:
                await update.message.reply_text("Sorry, I couldn't process your image file. Please try again.")
                return
            
            # Process similar to photo handler
            if caption and any(word in caption.lower() for word in ['edit', 'change', 'modify', 'update', 'turn']):
                try:
                    from services.image_editor import image_editor
                    edit_result = await image_editor.edit_image(image_path, caption)
                    
                    if edit_result["success"]:
                        response = {
                            "success": True,
                            "text": f"🎨 I've edited your image based on: '{caption}'\n\nHere's the result!",
                            "image_path": edit_result["image_path"]
                        }
                    else:
                        response = {
                            "success": False,
                            "text": f"Sorry, I couldn't edit your image: {edit_result.get('error', 'Unknown error')}"
                        }
                        
                except Exception as e:
                    logger.error(f"Error editing image document: {str(e)}")
                    response = {
                        "success": False,
                        "text": "Sorry, I encountered an error while editing your image."
                    }
            else:
                response = {
                    "success": True,
                    "text": "📸 I received your image file! If you'd like me to edit it, please send it again with a caption describing what changes you want me to make."
                }
            
            # Send response
            if response.get("text"):
                await update.message.reply_text(response["text"])
            
            # Send edited image if available
            if response.get("image_path") and os.path.exists(response["image_path"]):
                try:
                    with open(response["image_path"], 'rb') as edited_image:
                        await update.message.reply_photo(photo=edited_image, caption="Here's your edited image!")
                    
                    file_handler.delete_file(response["image_path"])
                    
                except Exception as e:
                    logger.error(f"Error sending edited image: {str(e)}")
            
            # Clean up uploaded image
            file_handler.delete_file(image_path)
            
        except Exception as e:
            logger.error(f"Error handling image document: {str(e)}")
            await update.message.reply_text("Sorry, I couldn't process your image file.")
    
    async def unknown_handler(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle unknown commands"""
        try:
            await update.message.reply_text(
                "🤔 I don't recognize that command. Try:\n\n"
                "• /start - Get started\n"
                "• /help - Show help\n"
                "• Just send me a message describing what you need!"
            )
            
            logger.info(f"Unknown command handled for user: {update.effective_user.id}")
            
        except Exception as e:
            logger.error(f"Error in unknown handler: {str(e)}")
    
    async def error_handler(self, update: object, context: ContextTypes.DEFAULT_TYPE):
        """Handle errors"""
        try:
            logger.error(f"Update {update} caused error {context.error}")
            
            # Try to send error message to user if possible
            if isinstance(update, Update) and update.effective_chat:
                try:
                    await context.bot.send_message(
                        chat_id=update.effective_chat.id,
                        text="😔 Sorry, something went wrong on my end. Please try again in a moment."
                    )
                except:
                    pass  # Ignore if we can't send error message
            
        except Exception as e:
            logger.error(f"Error in error handler: {str(e)}")
    
    async def cleanup_handler(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle /cleanup command (admin only - you can add user verification)"""
        try:
            user_id = update.effective_user.id
            
            # For security, you might want to check if user is admin
            # ADMIN_USER_IDS = [123456789, 987654321]  # Add your admin user IDs
            # if user_id not in ADMIN_USER_IDS:
            #     await update.message.reply_text("❌ You don't have permission to use this command.")
            #     return
            
            logger.info(f"Cleanup command initiated by user {user_id}")
            
            # Show processing message
            await update.message.reply_text("🧹 Cleaning up temporary files...")
            
            # Clean up old files
            cleanup_result = file_handler.cleanup_old_files(max_age_hours=24)
            
            if cleanup_result["success"]:
                message = (
                    f"✅ **Cleanup Complete**\n\n"
                    f"Deleted files: {cleanup_result['deleted_count']}\n"
                    f"Space freed: {cleanup_result['freed_space_mb']} MB"
                )
            else:
                message = f"❌ Cleanup failed: {cleanup_result.get('error', 'Unknown error')}"
            
            await update.message.reply_text(message)
            
        except Exception as e:
            logger.error(f"Error in cleanup handler: {str(e)}")
            await update.message.reply_text("❌ Error during cleanup. Check logs for details.")

# Create global instance
telegram_handlers = TelegramHandlers()