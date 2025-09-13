import logging
import logging.handlers
import os
from datetime import datetime
from config.settings import settings

def setup_logging():
    """Setup logging configuration for the application"""
    
    # Create logs directory if it doesn't exist
    os.makedirs(settings.LOGS_DIR, exist_ok=True)
    
    # Create formatters
    detailed_formatter = logging.Formatter(
        '%(asctime)s - %(name)s - %(levelname)s - %(funcName)s:%(lineno)d - %(message)s'
    )
    
    simple_formatter = logging.Formatter(
        '%(asctime)s - %(levelname)s - %(message)s'
    )
    
    # Setup root logger
    root_logger = logging.getLogger()
    root_logger.setLevel(logging.INFO)
    
    # Clear any existing handlers
    for handler in root_logger.handlers[:]:
        root_logger.removeHandler(handler)
    
    # Console handler
    console_handler = logging.StreamHandler()
    console_handler.setLevel(logging.INFO)
    console_handler.setFormatter(simple_formatter)
    root_logger.addHandler(console_handler)
    
    # File handler for general logs
    general_log_file = os.path.join(settings.LOGS_DIR, 'telegram_agent.log')
    file_handler = logging.handlers.RotatingFileHandler(
        general_log_file,
        maxBytes=10*1024*1024,  # 10MB
        backupCount=5
    )
    file_handler.setLevel(logging.INFO)
    file_handler.setFormatter(detailed_formatter)
    root_logger.addHandler(file_handler)
    
    # Error file handler
    error_log_file = os.path.join(settings.LOGS_DIR, 'errors.log')
    error_handler = logging.handlers.RotatingFileHandler(
        error_log_file,
        maxBytes=10*1024*1024,  # 10MB
        backupCount=5
    )
    error_handler.setLevel(logging.ERROR)
    error_handler.setFormatter(detailed_formatter)
    root_logger.addHandler(error_handler)
    
    # Create specific loggers for different modules
    loggers = [
        'telegram_bot',
        'ai_agent',
        'calendar_service',
        'email_service',
        'speech_service',
        'image_service',
        'fastapi'
    ]
    
    for logger_name in loggers:
        logger = logging.getLogger(logger_name)
        logger.setLevel(logging.INFO)
        
        # Create separate log file for each service
        service_log_file = os.path.join(settings.LOGS_DIR, f'{logger_name}.log')
        service_handler = logging.handlers.RotatingFileHandler(
            service_log_file,
            maxBytes=5*1024*1024,  # 5MB
            backupCount=3
        )
        service_handler.setLevel(logging.INFO)
        service_handler.setFormatter(detailed_formatter)
        logger.addHandler(service_handler)
    
    logging.info("✅ Logging configuration setup complete")

def get_logger(name: str) -> logging.Logger:
    """Get a logger instance with the specified name"""
    return logging.getLogger(name)

# Setup logging when this module is imported
setup_logging()