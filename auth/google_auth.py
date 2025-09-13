import os
import pickle
from typing import Optional
from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build
from config.settings import settings
from config.logging_config import get_logger

logger = get_logger('ai_agent')

class GoogleAuthService:
    """Service for handling Google OAuth authentication"""
    
    def __init__(self):
        """Initialize Google Auth Service"""
        self.scopes = settings.GOOGLE_SCOPES
        self.credentials_file = settings.CREDENTIALS_FILE
        self.token_file = os.path.join(settings.TEMP_DIR, 'token.pickle')
        self.credentials = None
        logger.info("GoogleAuthService initialized")
    
    def _create_credentials_file(self):
        """Create credentials.json file from environment variables"""
        try:
            credentials_data = {
                "installed": {
                    "client_id": settings.GOOGLE_CLIENT_ID,
                    "client_secret": settings.GOOGLE_CLIENT_SECRET,
                    "auth_uri": "https://accounts.google.com/o/oauth2/auth",
                    "token_uri": "https://oauth2.googleapis.com/token",
                    "redirect_uris": ["urn:ietf:wg:oauth:2.0:oob", "http://localhost"]
                }
            }
            
            import json
            with open(self.credentials_file, 'w') as f:
                json.dump(credentials_data, f, indent=2)
            
            logger.info("Created credentials.json from environment variables")
            return True
            
        except Exception as e:
            logger.error(f"Error creating credentials file: {str(e)}")
            return False
    
    def authenticate(self) -> Optional[Credentials]:
        """
        Authenticate with Google services
        
        Returns:
            Optional[Credentials]: Google credentials object or None if failed
        """
        try:
            creds = None
            
            # Load existing token
            if os.path.exists(self.token_file):
                logger.info("Loading existing authentication token...")
                with open(self.token_file, 'rb') as token:
                    creds = pickle.load(token)
            
            # Check if credentials are valid
            if not creds or not creds.valid:
                if creds and creds.expired and creds.refresh_token:
                    logger.info("Refreshing expired credentials...")
                    creds.refresh(Request())
                else:
                    logger.info("Starting new authentication flow...")
                    
                    # Create credentials file if it doesn't exist
                    if not os.path.exists(self.credentials_file):
                        if not self._create_credentials_file():
                            logger.error("Failed to create credentials file")
                            return None
                    
                    # Run OAuth flow
                    flow = InstalledAppFlow.from_client_secrets_file(
                        self.credentials_file, self.scopes
                    )
                    
                    # Use local server flow for better user experience
                    creds = flow.run_local_server(port=8080, open_browser=False)
                    
                    logger.info("Authentication completed successfully")
                
                # Save credentials for next run
                with open(self.token_file, 'wb') as token:
                    pickle.dump(creds, token)
                
                logger.info("Credentials saved successfully")
            
            self.credentials = creds
            return creds
            
        except Exception as e:
            logger.error(f"Authentication error: {str(e)}")
            return None
    
    def get_calendar_service(self):
        """
        Get authenticated Google Calendar service
        
        Returns:
            Google Calendar service object or None if failed
        """
        try:
            if not self.credentials:
                self.credentials = self.authenticate()
            
            if not self.credentials:
                logger.error("No valid credentials available for Calendar service")
                return None
            
            service = build('calendar', 'v3', credentials=self.credentials)
            logger.info("Calendar service initialized successfully")
            return service
            
        except Exception as e:
            logger.error(f"Error creating Calendar service: {str(e)}")
            return None
    
    def get_gmail_service(self):
        """
        Get authenticated Gmail service
        
        Returns:
            Gmail service object or None if failed
        """
        try:
            if not self.credentials:
                self.credentials = self.authenticate()
            
            if not self.credentials:
                logger.error("No valid credentials available for Gmail service")
                return None
            
            service = build('gmail', 'v1', credentials=self.credentials)
            logger.info("Gmail service initialized successfully")
            return service
            
        except Exception as e:
            logger.error(f"Error creating Gmail service: {str(e)}")
            return None
    
    def revoke_credentials(self) -> bool:
        """
        Revoke stored credentials
        
        Returns:
            bool: True if successful, False otherwise
        """
        try:
            # Remove token file
            if os.path.exists(self.token_file):
                os.remove(self.token_file)
                logger.info("Token file removed")
            
            # Reset credentials
            self.credentials = None
            
            logger.info("Credentials revoked successfully")
            return True
            
        except Exception as e:
            logger.error(f"Error revoking credentials: {str(e)}")
            return False
    
    def is_authenticated(self) -> bool:
        """
        Check if user is currently authenticated
        
        Returns:
            bool: True if authenticated, False otherwise
        """
        try:
            if not self.credentials:
                # Try to load existing credentials
                if os.path.exists(self.token_file):
                    with open(self.token_file, 'rb') as token:
                        self.credentials = pickle.load(token)
            
            if self.credentials and self.credentials.valid:
                return True
            
            if self.credentials and self.credentials.expired and self.credentials.refresh_token:
                # Try to refresh
                self.credentials.refresh(Request())
                return self.credentials.valid
            
            return False
            
        except Exception as e:
            logger.error(f"Error checking authentication status: {str(e)}")
            return False
    
    def get_user_info(self) -> Optional[dict]:
        """
        Get basic user information
        
        Returns:
            Optional[dict]: User info or None if failed
        """
        try:
            if not self.is_authenticated():
                logger.error("User not authenticated")
                return None
            
            # Build People API service to get user info
            people_service = build('people', 'v1', credentials=self.credentials)
            
            # Get user's profile information
            profile = people_service.people().get(
                resourceName='people/me',
                personFields='names,emailAddresses'
            ).execute()
            
            user_info = {
                'name': None,
                'email': None
            }
            
            # Extract name
            if 'names' in profile:
                user_info['name'] = profile['names'][0].get('displayName')
            
            # Extract email
            if 'emailAddresses' in profile:
                user_info['email'] = profile['emailAddresses'][0].get('value')
            
            logger.info(f"Retrieved user info: {user_info['name']} <{user_info['email']}>")
            return user_info
            
        except Exception as e:
            logger.error(f"Error getting user info: {str(e)}")
            return None

# Create global instance
google_auth = GoogleAuthService()