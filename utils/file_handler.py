import os
import shutil
import uuid
from typing import Optional, Dict, Any
from config.settings import settings
from config.logging_config import get_logger

logger = get_logger('ai_agent')

class FileHandler:
    """Utility class for handling file operations"""
    
    def __init__(self):
        """Initialize File Handler"""
        self.temp_dir = settings.TEMP_DIR
        self.max_file_size = 25 * 1024 * 1024  # 25MB
        self.supported_audio_formats = ['.wav', '.mp3', '.m4a', '.ogg', '.flac']
        self.supported_image_formats = ['.png', '.jpg', '.jpeg', '.bmp', '.tiff', '.webp']
    
    def save_telegram_audio(self, file_path: str, file_data: bytes) -> Optional[str]:
        """
        Save audio file from Telegram
        
        Args:
            file_path (str): Original file path/name
            file_data (bytes): File data
            
        Returns:
            Optional[str]: Path to saved file or None if failed
        """
        try:
            # Generate unique filename
            unique_id = str(uuid.uuid4())[:8]
            file_extension = os.path.splitext(file_path)[1].lower()
            
            if not file_extension:
                file_extension = '.ogg'  # Default for Telegram voice messages
            
            filename = f"telegram_audio_{unique_id}{file_extension}"
            output_path = os.path.join(self.temp_dir, filename)
            
            # Check file size
            if len(file_data) > self.max_file_size:
                logger.error(f"Audio file too large: {len(file_data)} bytes")
                return None
            
            # Save file
            with open(output_path, 'wb') as f:
                f.write(file_data)
            
            logger.info(f"Audio file saved: {output_path}")
            return output_path
            
        except Exception as e:
            logger.error(f"Error saving Telegram audio: {str(e)}")
            return None
    
    def save_telegram_image(self, file_path: str, file_data: bytes) -> Optional[str]:
        """
        Save image file from Telegram
        
        Args:
            file_path (str): Original file path/name
            file_data (bytes): File data
            
        Returns:
            Optional[str]: Path to saved file or None if failed
        """
        try:
            # Generate unique filename
            unique_id = str(uuid.uuid4())[:8]
            file_extension = os.path.splitext(file_path)[1].lower()
            
            if not file_extension:
                file_extension = '.jpg'  # Default for Telegram images
            
            filename = f"telegram_image_{unique_id}{file_extension}"
            output_path = os.path.join(self.temp_dir, filename)
            
            # Check file size
            if len(file_data) > self.max_file_size:
                logger.error(f"Image file too large: {len(file_data)} bytes")
                return None
            
            # Save file
            with open(output_path, 'wb') as f:
                f.write(file_data)
            
            logger.info(f"Image file saved: {output_path}")
            return output_path
            
        except Exception as e:
            logger.error(f"Error saving Telegram image: {str(e)}")
            return None
    
    def convert_audio_format(
        self,
        input_path: str,
        target_format: str = 'wav'
    ) -> Optional[str]:
        """
        Convert audio file to different format
        
        Args:
            input_path (str): Path to input audio file
            target_format (str): Target format (wav, mp3, etc.)
            
        Returns:
            Optional[str]: Path to converted file or None if failed
        """
        try:
            from pydub import AudioSegment
            
            if not os.path.exists(input_path):
                logger.error(f"Input audio file not found: {input_path}")
                return None
            
            # Generate output filename
            base_name = os.path.splitext(os.path.basename(input_path))[0]
            output_filename = f"{base_name}_converted.{target_format}"
            output_path = os.path.join(self.temp_dir, output_filename)
            
            # Load and convert audio
            audio = AudioSegment.from_file(input_path)
            
            # Export in target format
            audio.export(output_path, format=target_format)
            
            logger.info(f"Audio converted: {input_path} -> {output_path}")
            return output_path
            
        except Exception as e:
            logger.error(f"Error converting audio format: {str(e)}")
            return None
    
    def get_file_info(self, file_path: str) -> Dict[str, Any]:
        """
        Get information about a file
        
        Args:
            file_path (str): Path to the file
            
        Returns:
            Dict[str, Any]: File information
        """
        try:
            if not os.path.exists(file_path):
                return {"exists": False}
            
            stat = os.stat(file_path)
            file_extension = os.path.splitext(file_path)[1].lower()
            
            info = {
                "exists": True,
                "path": file_path,
                "filename": os.path.basename(file_path),
                "extension": file_extension,
                "size": stat.st_size,
                "size_mb": round(stat.st_size / (1024 * 1024), 2),
                "modified": stat.st_mtime,
                "is_audio": file_extension in self.supported_audio_formats,
                "is_image": file_extension in self.supported_image_formats
            }
            
            return info
            
        except Exception as e:
            logger.error(f"Error getting file info: {str(e)}")
            return {"exists": False, "error": str(e)}
    
    def cleanup_old_files(self, max_age_hours: int = 24) -> Dict[str, Any]:
        """
        Clean up old temporary files
        
        Args:
            max_age_hours (int): Maximum age in hours for files to keep
            
        Returns:
            Dict[str, Any]: Cleanup results
        """
        try:
            import time
            
            logger.info(f"Cleaning up files older than {max_age_hours} hours")
            
            if not os.path.exists(self.temp_dir):
                return {
                    "success": True,
                    "message": "Temp directory does not exist",
                    "deleted_count": 0,
                    "freed_space_mb": 0
                }
            
            current_time = time.time()
            max_age_seconds = max_age_hours * 3600
            deleted_count = 0
            freed_space = 0
            
            for filename in os.listdir(self.temp_dir):
                file_path = os.path.join(self.temp_dir, filename)
                
                try:
                    if os.path.isfile(file_path):
                        file_age = current_time - os.path.getmtime(file_path)
                        
                        if file_age > max_age_seconds:
                            file_size = os.path.getsize(file_path)
                            os.remove(file_path)
                            deleted_count += 1
                            freed_space += file_size
                            logger.info(f"Deleted old file: {filename}")
                            
                except Exception as e:
                    logger.error(f"Error processing file {filename}: {str(e)}")
            
            freed_space_mb = round(freed_space / (1024 * 1024), 2)
            
            return {
                "success": True,
                "deleted_count": deleted_count,
                "freed_space_mb": freed_space_mb,
                "message": f"Cleaned up {deleted_count} files, freed {freed_space_mb} MB"
            }
            
        except Exception as e:
            logger.error(f"Error cleaning up files: {str(e)}")
            return {
                "success": False,
                "error": str(e),
                "deleted_count": 0,
                "freed_space_mb": 0
            }
    
    def delete_file(self, file_path: str) -> bool:
        """
        Delete a specific file
        
        Args:
            file_path (str): Path to file to delete
            
        Returns:
            bool: True if successful, False otherwise
        """
        try:
            if os.path.exists(file_path):
                os.remove(file_path)
                logger.info(f"File deleted: {file_path}")
                return True
            else:
                logger.warning(f"File not found for deletion: {file_path}")
                return False
                
        except Exception as e:
            logger.error(f"Error deleting file: {str(e)}")
            return False
    
    def copy_file(self, source_path: str, destination_path: str) -> bool:
        """
        Copy a file to a new location
        
        Args:
            source_path (str): Source file path
            destination_path (str): Destination file path
            
        Returns:
            bool: True if successful, False otherwise
        """
        try:
            if not os.path.exists(source_path):
                logger.error(f"Source file not found: {source_path}")
                return False
            
            # Create destination directory if it doesn't exist
            dest_dir = os.path.dirname(destination_path)
            if dest_dir:
                os.makedirs(dest_dir, exist_ok=True)
            
            shutil.copy2(source_path, destination_path)
            logger.info(f"File copied: {source_path} -> {destination_path}")
            return True
            
        except Exception as e:
            logger.error(f"Error copying file: {str(e)}")
            return False
    
    def move_file(self, source_path: str, destination_path: str) -> bool:
        """
        Move a file to a new location
        
        Args:
            source_path (str): Source file path
            destination_path (str): Destination file path
            
        Returns:
            bool: True if successful, False otherwise
        """
        try:
            if not os.path.exists(source_path):
                logger.error(f"Source file not found: {source_path}")
                return False
            
            # Create destination directory if it doesn't exist
            dest_dir = os.path.dirname(destination_path)
            if dest_dir:
                os.makedirs(dest_dir, exist_ok=True)
            
            shutil.move(source_path, destination_path)
            logger.info(f"File moved: {source_path} -> {destination_path}")
            return True
            
        except Exception as e:
            logger.error(f"Error moving file: {str(e)}")
            return False
    
    def validate_file(
        self,
        file_path: str,
        expected_type: str = None,
        max_size_mb: int = None
    ) -> Dict[str, Any]:
        """
        Validate a file
        
        Args:
            file_path (str): Path to file to validate
            expected_type (str): Expected file type ('audio', 'image', etc.)
            max_size_mb (int): Maximum file size in MB
            
        Returns:
            Dict[str, Any]: Validation results
        """
        try:
            result = {
                "valid": False,
                "errors": [],
                "warnings": []
            }
            
            # Check if file exists
            if not os.path.exists(file_path):
                result["errors"].append("File does not exist")
                return result
            
            # Get file info
            file_info = self.get_file_info(file_path)
            
            # Check file size
            max_size = max_size_mb or (self.max_file_size / (1024 * 1024))
            if file_info["size_mb"] > max_size:
                result["errors"].append(f"File too large: {file_info['size_mb']} MB (max: {max_size} MB)")
            
            # Check file type
            if expected_type:
                if expected_type == "audio" and not file_info["is_audio"]:
                    result["errors"].append(f"Not an audio file: {file_info['extension']}")
                elif expected_type == "image" and not file_info["is_image"]:
                    result["errors"].append(f"Not an image file: {file_info['extension']}")
            
            # File is valid if no errors
            result["valid"] = len(result["errors"]) == 0
            result["file_info"] = file_info
            
            return result
            
        except Exception as e:
            logger.error(f"Error validating file: {str(e)}")
            return {
                "valid": False,
                "errors": [str(e)],
                "warnings": []
            }
    
    def get_temp_file_path(self, filename: str) -> str:
        """
        Get path for a temporary file
        
        Args:
            filename (str): Desired filename
            
        Returns:
            str: Full path to temporary file
        """
        return os.path.join(self.temp_dir, filename)
    
    def ensure_unique_filename(self, file_path: str) -> str:
        """
        Ensure filename is unique by adding numbers if necessary
        
        Args:
            file_path (str): Desired file path
            
        Returns:
            str: Unique file path
        """
        if not os.path.exists(file_path):
            return file_path
        
        base_path, extension = os.path.splitext(file_path)
        counter = 1
        
        while os.path.exists(f"{base_path}_{counter}{extension}"):
            counter += 1
        
        return f"{base_path}_{counter}{extension}"

# Create global instance
file_handler = FileHandler()