from fastapi import FastAPI, HTTPException, UploadFile, File, Form
from fastapi.responses import JSONResponse, FileResponse
from fastapi.middleware.cors import CORSMiddleware
from typing import Optional, Dict, Any
import os
import uuid
import time
from pydantic import BaseModel

from core.agent_brain import ai_agent
from utils.file_handler import file_handler
from utils.response_formatter import response_formatter
from config.logging_config import get_logger
from config.settings import settings

logger = get_logger('fastapi')

# Pydantic models for request/response
class MessageRequest(BaseModel):
    user_id: str
    message: str
    context: Optional[Dict[str, Any]] = None

class MessageResponse(BaseModel):
    success: bool
    text: Optional[str] = None
    audio_path: Optional[str] = None
    image_path: Optional[str] = None
    data: Optional[Dict[str, Any]] = None
    error: Optional[str] = None

class HealthResponse(BaseModel):
    status: str
    version: str
    services: Dict[str, bool]

# Create FastAPI app
app = FastAPI(
    title="Telegram AI Agent API",
    description="API for the Telegram AI Agent with calendar, email, and image capabilities",
    version="1.0.0"
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # In production, specify actual origins
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.on_event("startup")
async def startup_event():
    """Initialize services on startup"""
    logger.info("🚀 FastAPI server starting up...")
    
    # You can add any initialization logic here
    logger.info("✅ FastAPI server started successfully")

@app.on_event("shutdown")
async def shutdown_event():
    """Cleanup on shutdown"""
    logger.info("🛑 FastAPI server shutting down...")
    
    # Cleanup temporary files
    try:
        cleanup_result = file_handler.cleanup_old_files(max_age_hours=0)
        if cleanup_result["success"]:
            logger.info(f"✅ Shutdown cleanup: {cleanup_result['deleted_count']} files deleted")
    except Exception as e:
        logger.error(f"Error during shutdown cleanup: {str(e)}")
    
    logger.info("✅ FastAPI server shutdown complete")

@app.get("/", response_model=Dict[str, str])
async def root():
    """Root endpoint"""
    return {
        "message": "Telegram AI Agent API",
        "version": "1.0.0",
        "status": "running"
    }

@app.get("/health", response_model=HealthResponse)
async def health_check():
    """Health check endpoint"""
    try:
        # Check various services
        services_status = {
            "ai_agent": True,  # Basic check
            "file_handler": os.path.exists(settings.TEMP_DIR),
            "google_auth": True,  # You could add actual auth check here
        }
        
        all_healthy = all(services_status.values())
        
        return HealthResponse(
            status="healthy" if all_healthy else "degraded",
            version="1.0.0",
            services=services_status
        )
        
    except Exception as e:
        logger.error(f"Health check error: {str(e)}")
        return HealthResponse(
            status="unhealthy",
            version="1.0.0",
            services={"error": str(e)}
        )

@app.post("/message", response_model=MessageResponse)
async def process_message(request: MessageRequest):
    """Process a text message"""
    try:
        logger.info(f"Processing message from user {request.user_id}")
        
        # Process message with AI agent
        response = await ai_agent.process_message(
            user_id=request.user_id,
            message_text=request.message
        )
        
        return MessageResponse(
            success=response.get("success", False),
            text=response.get("text"),
            audio_path=response.get("audio_path"),
            image_path=response.get("image_path"),
            data=response.get("data"),
            error=response.get("error")
        )
        
    except Exception as e:
        logger.error(f"Error processing message: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/message/audio", response_model=MessageResponse)
async def process_audio_message(
    user_id: str = Form(...),
    audio_file: UploadFile = File(...),
    context: Optional[str] = Form(None)
):
    """Process an audio message"""
    try:
        logger.info(f"Processing audio message from user {user_id}")
        
        # Validate audio file
        if not audio_file.content_type or not audio_file.content_type.startswith('audio/'):
            raise HTTPException(status_code=400, detail="File must be an audio file")
        
        # Read audio data
        audio_data = await audio_file.read()
        
        # Save audio file
        audio_path = file_handler.save_telegram_audio(audio_file.filename, audio_data)
        
        if not audio_path:
            raise HTTPException(status_code=400, detail="Failed to save audio file")
        
        try:
            # Process audio with AI agent
            response = await ai_agent.process_message(
                user_id=user_id,
                audio_file_path=audio_path
            )
            
            return MessageResponse(
                success=response.get("success", False),
                text=response.get("text"),
                audio_path=response.get("audio_path"),
                image_path=response.get("image_path"),
                data=response.get("data"),
                error=response.get("error")
            )
            
        finally:
            # Clean up uploaded audio file
            file_handler.delete_file(audio_path)
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error processing audio message: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/image/generate")
async def generate_image(
    user_id: str = Form(...),
    description: str = Form(...),
    style: Optional[str] = Form("")
):
    """Generate an image from text description"""
    try:
        logger.info(f"Generating image for user {user_id}: {description[:50]}...")
        
        from services.image_generator import image_generator
        
        # Generate image
        result = await image_generator.generate_image(description, style)
        
        if result["success"]:
            return JSONResponse(content={
                "success": True,
                "message": "Image generated successfully",
                "image_path": result["image_path"],
                "filename": result["filename"],
                "description": description,
                "style": style
            })
        else:
            raise HTTPException(status_code=400, detail=result.get("error", "Failed to generate image"))
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error generating image: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/image/edit")
async def edit_image(
    user_id: str = Form(...),
    modifications: str = Form(...),
    image_file: UploadFile = File(...)
):
    """Edit an uploaded image"""
    try:
        logger.info(f"Editing image for user {user_id}: {modifications[:50]}...")
        
        # Validate image file
        if not image_file.content_type or not image_file.content_type.startswith('image/'):
            raise HTTPException(status_code=400, detail="File must be an image file")
        
        # Read image data
        image_data = await image_file.read()
        
        # Save image file
        image_path = file_handler.save_telegram_image(image_file.filename, image_data)
        
        if not image_path:
            raise HTTPException(status_code=400, detail="Failed to save image file")
        
        try:
            from services.image_editor import image_editor
            
            # Edit image
            result = await image_editor.edit_image(image_path, modifications)
            
            if result["success"]:
                return JSONResponse(content={
                    "success": True,
                    "message": "Image edited successfully",
                    "image_path": result["image_path"],
                    "filename": result["filename"],
                    "original_image": image_path,
                    "modifications": modifications
                })
            else:
                raise HTTPException(status_code=400, detail=result.get("error", "Failed to edit image"))
                
        finally:
            # Clean up uploaded image file
            file_handler.delete_file(image_path)
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error editing image: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/download/audio/{filename}")
async def download_audio(filename: str):
    """Download generated audio file"""
    try:
        file_path = os.path.join(settings.TEMP_DIR, filename)
        
        if not os.path.exists(file_path):
            raise HTTPException(status_code=404, detail="Audio file not found")
        
        # Validate it's an audio file
        if not any(filename.endswith(ext) for ext in file_handler.supported_audio_formats):
            raise HTTPException(status_code=400, detail="Invalid audio file")
        
        return FileResponse(
            path=file_path,
            filename=filename,
            media_type='audio/wav'
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error downloading audio: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/download/image/{filename}")
async def download_image(filename: str):
    """Download generated image file"""
    try:
        file_path = os.path.join(settings.TEMP_DIR, filename)
        
        if not os.path.exists(file_path):
            raise HTTPException(status_code=404, detail="Image file not found")
        
        # Validate it's an image file
        if not any(filename.endswith(ext) for ext in file_handler.supported_image_formats):
            raise HTTPException(status_code=400, detail="Invalid image file")
        
        return FileResponse(
            path=file_path,
            filename=filename,
            media_type='image/png'
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error downloading image: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/calendar/create")
async def create_calendar_event(
    user_id: str = Form(...),
    title: str = Form(...),
    date: str = Form(...),
    time: str = Form(...),
    duration: str = Form("1 hour"),
    description: str = Form(""),
    attendees: Optional[str] = Form(None)
):
    """Create a calendar event"""
    try:
        logger.info(f"Creating calendar event for user {user_id}: {title}")
        
        from services.calendar_service import calendar_service
        
        # Parse attendees
        attendee_list = []
        if attendees:
            attendee_list = [email.strip() for email in attendees.split(",")]
        
        # Create event
        result = await calendar_service.create_event(
            title=title,
            date=date,
            time=time,
            duration=duration,
            description=description,
            attendees=attendee_list
        )
        
        if result["success"]:
            return JSONResponse(content={
                "success": True,
                "message": "Calendar event created successfully",
                "event_details": result["event_details"]
            })
        else:
            raise HTTPException(status_code=400, detail=result.get("error", "Failed to create event"))
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error creating calendar event: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/calendar/events")
async def get_calendar_events(
    user_id: str,
    date: Optional[str] = None,
    max_results: int = 10
):
    """Get calendar events"""
    try:
        logger.info(f"Getting calendar events for user {user_id}")
        
        from services.calendar_service import calendar_service
        
        # Get events
        result = await calendar_service.get_events(date=date, max_results=max_results)
        
        if result["success"]:
            return JSONResponse(content={
                "success": True,
                "events": result["events"]
            })
        else:
            raise HTTPException(status_code=400, detail=result.get("error", "Failed to get events"))
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting calendar events: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/email/send")
async def send_email(
    user_id: str = Form(...),
    to_email: str = Form(...),
    subject: str = Form(...),
    body: str = Form(...),
    from_email: Optional[str] = Form(None)
):
    """Send an email"""
    try:
        logger.info(f"Sending email for user {user_id} to {to_email}")
        
        from services.email_service import email_service
        
        # Send email
        result = await email_service.send_email(
            to_email=to_email,
            subject=subject,
            body=body,
            from_email=from_email
        )
        
        if result["success"]:
            return JSONResponse(content={
                "success": True,
                "message": "Email sent successfully",
                "details": result["details"]
            })
        else:
            raise HTTPException(status_code=400, detail=result.get("error", "Failed to send email"))
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error sending email: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/email/list")
async def get_emails(
    user_id: str,
    query: Optional[str] = None,
    max_results: int = 10,
    include_body: bool = False
):
    """Get emails"""
    try:
        logger.info(f"Getting emails for user {user_id}")
        
        from services.email_service import email_service
        
        # Get emails
        result = await email_service.get_emails(
            query=query,
            max_results=max_results,
            include_body=include_body
        )
        
        if result["success"]:
            return JSONResponse(content={
                "success": True,
                "emails": result["emails"],
                "total_count": result["total_count"]
            })
        else:
            raise HTTPException(status_code=400, detail=result.get("error", "Failed to get emails"))
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting emails: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/cleanup")
async def cleanup_files(
    user_id: str = Form(...),
    max_age_hours: int = Form(24)
):
    """Clean up temporary files"""
    try:
        logger.info(f"Cleanup initiated by user {user_id}")
        
        # For security, you might want to add user verification here
        # if user_id not in ADMIN_USER_IDS:
        #     raise HTTPException(status_code=403, detail="Insufficient permissions")
        
        # Clean up files
        cleanup_result = file_handler.cleanup_old_files(max_age_hours=max_age_hours)
        
        if cleanup_result["success"]:
            return JSONResponse(content={
                "success": True,
                "message": cleanup_result["message"],
                "deleted_count": cleanup_result["deleted_count"],
                "freed_space_mb": cleanup_result["freed_space_mb"]
            })
        else:
            raise HTTPException(status_code=500, detail=cleanup_result.get("error", "Cleanup failed"))
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error during cleanup: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/stats")
async def get_stats():
    """Get system statistics"""
    try:
        import psutil
        import time
        
        # Get system stats
        stats = {
            "system": {
                "cpu_percent": psutil.cpu_percent(),
                "memory_percent": psutil.virtual_memory().percent,
                "disk_usage": psutil.disk_usage('/').percent if os.name != 'nt' else psutil.disk_usage('C:').percent,
                "uptime": time.time() - psutil.boot_time()
            },
            "temp_directory": {
                "path": settings.TEMP_DIR,
                "exists": os.path.exists(settings.TEMP_DIR),
                "file_count": len(os.listdir(settings.TEMP_DIR)) if os.path.exists(settings.TEMP_DIR) else 0
            },
            "logs_directory": {
                "path": settings.LOGS_DIR,
                "exists": os.path.exists(settings.LOGS_DIR),
                "file_count": len(os.listdir(settings.LOGS_DIR)) if os.path.exists(settings.LOGS_DIR) else 0
            }
        }
        
        return JSONResponse(content=stats)
        
    except Exception as e:
        logger.error(f"Error getting stats: {str(e)}")
        # Return basic stats if psutil is not available
        return JSONResponse(content={
            "temp_directory": {
                "path": settings.TEMP_DIR,
                "exists": os.path.exists(settings.TEMP_DIR)
            },
            "logs_directory": {
                "path": settings.LOGS_DIR,
                "exists": os.path.exists(settings.LOGS_DIR)
            },
            "error": "Detailed system stats unavailable"
        })

@app.exception_handler(404)
async def not_found_handler(request, exc):
    """Handle 404 errors"""
    return JSONResponse(
        status_code=404,
        content={"error": "Endpoint not found", "path": str(request.url)}
    )

@app.exception_handler(500)
async def internal_error_handler(request, exc):
    """Handle 500 errors"""
    logger.error(f"Internal server error: {str(exc)}")
    return JSONResponse(
        status_code=500,
        content={"error": "Internal server error", "detail": str(exc)}
    )

# Add middleware for logging requests
@app.middleware("http")
async def log_requests(request, call_next):
    """Log all HTTP requests"""
    start_time = time.time()
    
    logger.info(f"📨 {request.method} {request.url}")
    
    response = await call_next(request)
    
    process_time = time.time() - start_time
    logger.info(f"✅ {request.method} {request.url} - {response.status_code} - {process_time:.2f}s")
    
    return response

# Create the router instance
router = app