import os
import uuid
from typing import Dict, Any, Optional
from huggingface_hub import InferenceClient
from config.settings import settings
from config.logging_config import get_logger

logger = get_logger('image_service')

class ImageEditingService:
    """Service for image-to-image editing using Hugging Face models"""
    
    def __init__(self):
        """Initialize Image Editing Service"""
        self.client = InferenceClient(
            api_key=settings.HUGGINGFACEHUB_API_TOKEN
        )
        self.model = settings.IMAGE_EDIT_MODEL
        logger.info("ImageEditingService initialized")
    
    def _create_edit_prompt(self, modifications: str) -> str:
        """
        Create an enhanced prompt for image editing
        
        Args:
            modifications (str): User's modification request
            
        Returns:
            str: Enhanced editing prompt
        """
        try:
            # Enhance the modification prompt
            enhanced_prompt = modifications
            
            # Add quality preservation terms
            quality_terms = [
                "maintain quality",
                "preserve details",
                "high resolution"
            ]
            
            prompt_lower = enhanced_prompt.lower()
            for term in quality_terms:
                if "quality" not in prompt_lower and "detail" not in prompt_lower:
                    enhanced_prompt += f", {term}"
                    break
            
            logger.info(f"Enhanced edit prompt: {enhanced_prompt}")
            return enhanced_prompt
            
        except Exception as e:
            logger.error(f"Error enhancing edit prompt: {str(e)}")
            return modifications
    
    def _generate_edit_filename(self, original_path: str, modifications: str) -> str:
        """
        Generate filename for edited image
        
        Args:
            original_path (str): Path to original image
            modifications (str): Modification description
            
        Returns:
            str: Generated filename
        """
        try:
            # Get original filename without extension
            original_name = os.path.splitext(os.path.basename(original_path))[0]
            
            # Create safe modification description
            safe_mods = "".join(c for c in modifications if c.isalnum() or c in (' ', '-', '_')).rstrip()
            safe_mods = safe_mods.replace(' ', '_')[:30]  # Limit length
            
            # Add unique identifier
            unique_id = str(uuid.uuid4())[:8]
            filename = f"{original_name}_edited_{safe_mods}_{unique_id}.png"
            
            return filename
            
        except Exception:
            # Fallback to simple UUID-based filename
            unique_id = str(uuid.uuid4())[:12]
            return f"edited_image_{unique_id}.png"
    
    def _validate_input_image(self, image_path: str) -> bool:
        """
        Validate input image file
        
        Args:
            image_path (str): Path to input image
            
        Returns:
            bool: True if valid, False otherwise
        """
        try:
            if not image_path or not os.path.exists(image_path):
                logger.error(f"Input image does not exist: {image_path}")
                return False
            
            # Check file size (reasonable limit)
            file_size = os.path.getsize(image_path)
            max_size = 10 * 1024 * 1024  # 10MB
            
            if file_size > max_size:
                logger.error(f"Input image too large: {file_size} bytes (max: {max_size})")
                return False
            
            # Check file extension
            valid_extensions = ['.png', '.jpg', '.jpeg', '.bmp', '.tiff']
            file_extension = os.path.splitext(image_path)[1].lower()
            
            if file_extension not in valid_extensions:
                logger.error(f"Unsupported image format: {file_extension}")
                return False
            
            return True
            
        except Exception as e:
            logger.error(f"Error validating input image: {str(e)}")
            return False
    
    async def edit_image(
        self,
        input_image_path: str,
        modifications: str,
        output_file: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Edit an image based on text instructions
        
        Args:
            input_image_path (str): Path to the input image
            modifications (str): Text description of desired modifications
            output_file (Optional[str]): Output file path (auto-generated if None)
            
        Returns:
            Dict[str, Any]: Result with success status and edited image details
        """
        try:
            logger.info(f"Editing image: {input_image_path}")
            logger.info(f"Modifications: {modifications[:100]}...")
            
            # Validate inputs
            if not modifications.strip():
                return {
                    "success": False,
                    "error": "Modification description cannot be empty"
                }
            
            if not self._validate_input_image(input_image_path):
                return {
                    "success": False,
                    "error": "Invalid input image file"
                }
            
            # Enhance the modification prompt
            enhanced_prompt = self._create_edit_prompt(modifications)
            
            # Generate output filename if not provided
            if not output_file:
                filename = self._generate_edit_filename(input_image_path, modifications)
                output_file = os.path.join(settings.TEMP_DIR, filename)
            
            # Read input image
            try:
                with open(input_image_path, "rb") as image_file:
                    input_image_data = image_file.read()
                
                logger.info("Sending image edit request to Hugging Face API...")
                
                # Edit image using the client
                edited_image = self.client.image_to_image(
                    input_image_data,
                    prompt=enhanced_prompt,
                    model=self.model
                )
                
                # Save edited image
                edited_image.save(output_file)
                
                # Verify file was created and get size
                if os.path.exists(output_file):
                    file_size = os.path.getsize(output_file)
                    logger.info(f"Image edited successfully: {output_file} ({file_size} bytes)")
                    
                    return {
                        "success": True,
                        "image_path": output_file,
                        "filename": os.path.basename(output_file),
                        "original_image": input_image_path,
                        "modifications": modifications,
                        "enhanced_prompt": enhanced_prompt,
                        "file_size": file_size
                    }
                else:
                    return {
                        "success": False,
                        "error": "Edited image file was not created"
                    }
                
            except Exception as api_error:
                logger.error(f"Hugging Face API error: {str(api_error)}")
                return {
                    "success": False,
                    "error": f"Image editing API error: {str(api_error)}"
                }
                
        except Exception as e:
            logger.error(f"Error editing image: {str(e)}")
            return {
                "success": False,
                "error": str(e)
            }
    
    def get_supported_modifications(self) -> list:
        """Get list of common modification types"""
        return [
            "change colors",
            "add objects",
            "remove objects",
            "change background",
            "change style",
            "add text",
            "change lighting",
            "change weather",
            "add effects",
            "change materials",
            "resize elements",
            "change perspective",
            "add people",
            "remove people",
            "change expressions"
        ]
    
    def validate_modifications(self, modifications: str) -> bool:
        """
        Validate modification request
        
        Args:
            modifications (str): Modification description to validate
            
        Returns:
            bool: True if valid, False otherwise
        """
        try:
            if not modifications or not modifications.strip():
                logger.warning("Empty modification description")
                return False
            
            if len(modifications) > 500:
                logger.warning(f"Modification description too long: {len(modifications)} characters")
                return False
            
            # Check for potentially problematic content
            forbidden_terms = [
                "nsfw", "nude", "naked", "explicit", "sexual",
                "violence", "gore", "blood", "weapon", "gun"
            ]
            
            modifications_lower = modifications.lower()
            for term in forbidden_terms:
                if term in modifications_lower:
                    logger.warning(f"Potentially inappropriate modification detected: {term}")
                    return False
            
            return True
            
        except Exception as e:
            logger.error(f"Error validating modifications: {str(e)}")
            return False
    
    async def batch_edit_images(
        self,
        image_paths: list,
        modifications: str
    ) -> Dict[str, Any]:
        """
        Apply the same modifications to multiple images
        
        Args:
            image_paths (list): List of image file paths
            modifications (str): Modification description to apply to all images
            
        Returns:
            Dict[str, Any]: Result with success status and list of edited images
        """
        try:
            logger.info(f"Batch editing {len(image_paths)} images...")
            
            if not image_paths:
                return {
                    "success": False,
                    "error": "No image paths provided"
                }
            
            if len(image_paths) > 5:  # Reasonable limit
                return {
                    "success": False,
                    "error": "Too many images for batch editing (maximum 5 at once)"
                }
            
            if not self.validate_modifications(modifications):
                return {
                    "success": False,
                    "error": "Invalid modification description"
                }
            
            results = []
            successful_count = 0
            
            for i, image_path in enumerate(image_paths):
                logger.info(f"Editing image {i+1}/{len(image_paths)}: {image_path}")
                
                result = await self.edit_image(image_path, modifications)
                results.append({
                    "index": i,
                    "original_path": image_path,
                    **result
                })
                
                if result["success"]:
                    successful_count += 1
            
            return {
                "success": successful_count > 0,
                "total_requested": len(image_paths),
                "successful_count": successful_count,
                "failed_count": len(image_paths) - successful_count,
                "modifications": modifications,
                "results": results
            }
            
        except Exception as e:
            logger.error(f"Error batch editing images: {str(e)}")
            return {
                "success": False,
                "error": str(e)
            }
    
    def create_before_after_comparison(
        self,
        original_path: str,
        edited_path: str,
        output_path: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Create a side-by-side comparison of original and edited images
        
        Args:
            original_path (str): Path to original image
            edited_path (str): Path to edited image
            output_path (Optional[str]): Output path for comparison image
            
        Returns:
            Dict[str, Any]: Result with comparison image details
        """
        try:
            from PIL import Image
            
            logger.info("Creating before/after comparison...")
            
            # Validate input files
            if not os.path.exists(original_path) or not os.path.exists(edited_path):
                return {
                    "success": False,
                    "error": "One or both images do not exist"
                }
            
            # Generate output filename if not provided
            if not output_path:
                unique_id = str(uuid.uuid4())[:8]
                filename = f"comparison_{unique_id}.png"
                output_path = os.path.join(settings.TEMP_DIR, filename)
            
            # Load images
            original_img = Image.open(original_path)
            edited_img = Image.open(edited_path)
            
            # Resize images to same height (use smaller height)
            min_height = min(original_img.height, edited_img.height)
            
            # Calculate new widths maintaining aspect ratio
            original_width = int((original_img.width * min_height) / original_img.height)
            edited_width = int((edited_img.width * min_height) / edited_img.height)
            
            # Resize images
            original_resized = original_img.resize((original_width, min_height))
            edited_resized = edited_img.resize((edited_width, min_height))
            
            # Create comparison image
            comparison_width = original_width + edited_width + 10  # 10px gap
            comparison_img = Image.new('RGB', (comparison_width, min_height), (255, 255, 255))
            
            # Paste images side by side
            comparison_img.paste(original_resized, (0, 0))
            comparison_img.paste(edited_resized, (original_width + 10, 0))
            
            # Save comparison
            comparison_img.save(output_path)
            
            logger.info(f"Comparison image created: {output_path}")
            
            return {
                "success": True,
                "comparison_path": output_path,
                "original_path": original_path,
                "edited_path": edited_path,
                "filename": os.path.basename(output_path)
            }
            
        except Exception as e:
            logger.error(f"Error creating comparison image: {str(e)}")
            return {
                "success": False,
                "error": str(e)
            }

# Create global instance
image_editor = ImageEditingService()