import os
import uuid
from typing import Dict, Any, Optional
from huggingface_hub import InferenceClient
from config.settings import settings
from config.logging_config import get_logger

logger = get_logger('image_service')

class ImageGenerationService:
    """Service for text-to-image generation using Hugging Face models"""
    
    def __init__(self):
        """Initialize Image Generation Service"""
        self.client = InferenceClient(
            provider="fal-ai",
            api_key=settings.HUGGINGFACEHUB_API_TOKEN
        )
        self.model = settings.IMAGE_GENERATION_MODEL
        logger.info("ImageGenerationService initialized")
    
    def _create_enhanced_prompt(self, description: str, style: str = "") -> str:
        """
        Enhance the user's prompt for better image generation
        
        Args:
            description (str): User's image description
            style (str): Optional style specification
            
        Returns:
            str: Enhanced prompt
        """
        try:
            enhanced_prompt = description
            
            # Add style if provided
            if style:
                enhanced_prompt += f", {style}"
            
            # Add quality enhancers
            quality_terms = [
                "high quality",
                "detailed",
                "professional",
                "8k resolution",
                "sharp focus"
            ]
            
            # Only add quality terms if not already present
            prompt_lower = enhanced_prompt.lower()
            for term in quality_terms:
                if term not in prompt_lower:
                    enhanced_prompt += f", {term}"
                    break  # Add only one quality term to avoid over-enhancement
            
            logger.info(f"Enhanced prompt: {enhanced_prompt}")
            return enhanced_prompt
            
        except Exception as e:
            logger.error(f"Error enhancing prompt: {str(e)}")
            return description
    
    def _generate_filename(self, description: str) -> str:
        """
        Generate a unique filename for the image
        
        Args:
            description (str): Image description for filename
            
        Returns:
            str: Generated filename
        """
        try:
            # Create a safe filename from description
            safe_description = "".join(c for c in description if c.isalnum() or c in (' ', '-', '_')).rstrip()
            safe_description = safe_description.replace(' ', '_')[:50]  # Limit length
            
            # Add unique identifier
            unique_id = str(uuid.uuid4())[:8]
            filename = f"generated_{safe_description}_{unique_id}.png"
            
            return filename
            
        except Exception:
            # Fallback to simple UUID-based filename
            unique_id = str(uuid.uuid4())[:12]
            return f"generated_image_{unique_id}.png"
    
    async def generate_image(
        self,
        description: str,
        style: str = "",
        output_file: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Generate an image from text description
        
        Args:
            description (str): Text description of the image to generate
            style (str): Optional style specification
            output_file (Optional[str]): Output file path (auto-generated if None)
            
        Returns:
            Dict[str, Any]: Result with success status and image details
        """
        try:
            logger.info(f"Generating image: {description[:100]}...")
            
            if not description.strip():
                return {
                    "success": False,
                    "error": "Image description cannot be empty"
                }
            
            # Enhance the prompt
            enhanced_prompt = self._create_enhanced_prompt(description, style)
            
            # Generate output filename if not provided
            if not output_file:
                filename = self._generate_filename(description)
                output_file = os.path.join(settings.TEMP_DIR, filename)
            
            # Generate image using Hugging Face API
            logger.info("Sending request to Hugging Face API...")
            
            try:
                # Generate image using the client
                image = self.client.text_to_image(
                    enhanced_prompt,
                    model=self.model
                )
                
                # Save image to file
                image.save(output_file)
                
                # Verify file was created and get size
                if os.path.exists(output_file):
                    file_size = os.path.getsize(output_file)
                    logger.info(f"Image generated successfully: {output_file} ({file_size} bytes)")
                    
                    return {
                        "success": True,
                        "image_path": output_file,
                        "filename": os.path.basename(output_file),
                        "description": description,
                        "enhanced_prompt": enhanced_prompt,
                        "style": style,
                        "file_size": file_size
                    }
                else:
                    return {
                        "success": False,
                        "error": "Image file was not created"
                    }
                
            except Exception as api_error:
                logger.error(f"Hugging Face API error: {str(api_error)}")
                return {
                    "success": False,
                    "error": f"Image generation API error: {str(api_error)}"
                }
                
        except Exception as e:
            logger.error(f"Error generating image: {str(e)}")
            return {
                "success": False,
                "error": str(e)
            }
    
    def get_supported_styles(self) -> list:
        """Get list of supported image styles"""
        return [
            "photorealistic",
            "digital art",
            "oil painting",
            "watercolor",
            "sketch",
            "cartoon",
            "anime",
            "cyberpunk",
            "steampunk",
            "minimalist",
            "abstract",
            "vintage",
            "futuristic",
            "fantasy",
            "sci-fi"
        ]
    
    def validate_description(self, description: str) -> bool:
        """
        Validate image description
        
        Args:
            description (str): Description to validate
            
        Returns:
            bool: True if valid, False otherwise
        """
        try:
            if not description or not description.strip():
                logger.warning("Empty image description")
                return False
            
            if len(description) > 1000:
                logger.warning(f"Description too long: {len(description)} characters")
                return False
            
            # Check for potentially problematic content
            forbidden_terms = [
                "nsfw", "nude", "naked", "explicit", "sexual",
                "violence", "gore", "blood", "weapon", "gun"
            ]
            
            description_lower = description.lower()
            for term in forbidden_terms:
                if term in description_lower:
                    logger.warning(f"Potentially inappropriate content detected: {term}")
                    return False
            
            return True
            
        except Exception as e:
            logger.error(f"Error validating description: {str(e)}")
            return False
    
    async def generate_multiple_images(
        self,
        descriptions: list,
        style: str = ""
    ) -> Dict[str, Any]:
        """
        Generate multiple images from a list of descriptions
        
        Args:
            descriptions (list): List of image descriptions
            style (str): Style to apply to all images
            
        Returns:
            Dict[str, Any]: Result with success status and list of generated images
        """
        try:
            logger.info(f"Generating {len(descriptions)} images...")
            
            if not descriptions:
                return {
                    "success": False,
                    "error": "No descriptions provided"
                }
            
            if len(descriptions) > 5:  # Reasonable limit
                return {
                    "success": False,
                    "error": "Too many images requested (maximum 5 at once)"
                }
            
            results = []
            successful_count = 0
            
            for i, description in enumerate(descriptions):
                logger.info(f"Generating image {i+1}/{len(descriptions)}")
                
                result = await self.generate_image(description, style)
                results.append({
                    "index": i,
                    "description": description,
                    **result
                })
                
                if result["success"]:
                    successful_count += 1
            
            return {
                "success": successful_count > 0,
                "total_requested": len(descriptions),
                "successful_count": successful_count,
                "failed_count": len(descriptions) - successful_count,
                "results": results
            }
            
        except Exception as e:
            logger.error(f"Error generating multiple images: {str(e)}")
            return {
                "success": False,
                "error": str(e)
            }
    
    def cleanup_old_images(self, max_age_hours: int = 24) -> Dict[str, Any]:
        """
        Clean up old generated images
        
        Args:
            max_age_hours (int): Maximum age in hours for images to keep
            
        Returns:
            Dict[str, Any]: Cleanup results
        """
        try:
            import time
            
            logger.info(f"Cleaning up images older than {max_age_hours} hours")
            
            temp_dir = settings.TEMP_DIR
            if not os.path.exists(temp_dir):
                return {
                    "success": True,
                    "message": "Temp directory does not exist",
                    "deleted_count": 0
                }
            
            current_time = time.time()
            max_age_seconds = max_age_hours * 3600
            deleted_count = 0
            
            for filename in os.listdir(temp_dir):
                if filename.startswith("generated_") and filename.endswith(".png"):
                    file_path = os.path.join(temp_dir, filename)
                    
                    try:
                        file_age = current_time - os.path.getmtime(file_path)
                        
                        if file_age > max_age_seconds:
                            os.remove(file_path)
                            deleted_count += 1
                            logger.info(f"Deleted old image: {filename}")
                            
                    except Exception as e:
                        logger.error(f"Error processing file {filename}: {str(e)}")
            
            return {
                "success": True,
                "deleted_count": deleted_count,
                "message": f"Cleaned up {deleted_count} old images"
            }
            
        except Exception as e:
            logger.error(f"Error cleaning up images: {str(e)}")
            return {
                "success": False,
                "error": str(e),
                "deleted_count": 0
            }

# Create global instance
image_generator = ImageGenerationService()