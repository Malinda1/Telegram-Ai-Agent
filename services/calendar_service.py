import os
from datetime import datetime, timedelta
from typing import List, Dict, Any, Optional
from dateutil import parser
import pytz
from auth.google_auth import google_auth
from config.logging_config import get_logger

logger = get_logger('calendar_service')

class CalendarService:
    """Service for Google Calendar operations"""
    
    def __init__(self):
        """Initialize Calendar Service"""
        self.service = None
        # Set Sri Lanka timezone
        self.local_timezone = pytz.timezone('Asia/Colombo')
        logger.info("CalendarService initialized")
    
    def _get_service(self):
        """Get or create Google Calendar service"""
        if not self.service:
            self.service = google_auth.get_calendar_service()
        return self.service
    
    def _parse_datetime(self, date_str: str, time_str: str = None) -> Optional[datetime]:
        """
        Parse date and time strings into datetime object with proper timezone
        
        Args:
            date_str (str): Date string (e.g., "today", "tomorrow", "2024-01-15")
            time_str (str): Time string (e.g., "8:00 AM", "14:30")
            
        Returns:
            Optional[datetime]: Parsed datetime with local timezone or None if failed
        """
        try:
            # Get current time in local timezone
            now = datetime.now(self.local_timezone)
            
            # Handle relative dates
            if date_str.lower() == "today":
                target_date = now.date()
            elif date_str.lower() == "tomorrow":
                target_date = (now + timedelta(days=1)).date()
            elif date_str.lower() == "yesterday":
                target_date = (now - timedelta(days=1)).date()
            else:
                # Try to parse absolute date
                parsed_date = parser.parse(date_str, fuzzy=True)
                target_date = parsed_date.date()
            
            # Parse time if provided
            if time_str:
                try:
                    # Parse time string
                    time_parsed = parser.parse(time_str, fuzzy=True)
                    target_time = time_parsed.time()
                except:
                    # Default to current time if parsing fails
                    target_time = now.time()
            else:
                # Default to current time
                target_time = now.time()
            
            # Combine date and time with local timezone
            naive_datetime = datetime.combine(target_date, target_time)
            result = self.local_timezone.localize(naive_datetime)
            
            logger.info(f"Parsed datetime: {result}")
            return result
            
        except Exception as e:
            logger.error(f"Error parsing datetime: {str(e)}")
            return None
    
    def _parse_duration(self, duration_str: str) -> timedelta:
        """
        Parse duration string into timedelta
        
        Args:
            duration_str (str): Duration string (e.g., "1 hour", "30 minutes", "2h")
            
        Returns:
            timedelta: Parsed duration (default: 1 hour)
        """
        try:
            duration_str = duration_str.lower().strip()
            
            # Default duration
            default_duration = timedelta(hours=1)
            
            if not duration_str:
                return default_duration
            
            # Handle common patterns
            if "minute" in duration_str:
                minutes = int(''.join(filter(str.isdigit, duration_str)))
                return timedelta(minutes=minutes)
            elif "hour" in duration_str:
                hours = int(''.join(filter(str.isdigit, duration_str)))
                return timedelta(hours=hours)
            elif "day" in duration_str:
                days = int(''.join(filter(str.isdigit, duration_str)))
                return timedelta(days=days)
            elif duration_str.endswith("h"):
                hours = int(duration_str[:-1])
                return timedelta(hours=hours)
            elif duration_str.endswith("m"):
                minutes = int(duration_str[:-1])
                return timedelta(minutes=minutes)
            else:
                # Try to extract number and assume hours
                import re
                numbers = re.findall(r'\d+', duration_str)
                if numbers:
                    hours = int(numbers[0])
                    return timedelta(hours=hours)
            
            return default_duration
            
        except Exception as e:
            logger.error(f"Error parsing duration: {str(e)}")
            return timedelta(hours=1)
    
    async def create_event(
        self,
        title: str,
        date: str,
        time: str,
        duration: str = "1 hour",
        description: str = "",
        attendees: List[str] = None
    ) -> Dict[str, Any]:
        """
        Create a new calendar event
        
        Args:
            title (str): Event title
            date (str): Event date
            time (str): Event time
            duration (str): Event duration
            description (str): Event description
            attendees (List[str]): List of attendee emails
            
        Returns:
            Dict[str, Any]: Result with success status and event details
        """
        try:
            logger.info(f"Creating calendar event: {title}")
            
            service = self._get_service()
            if not service:
                return {
                    "success": False,
                    "error": "Failed to connect to Google Calendar service"
                }
            
            # Parse start datetime (now with proper timezone)
            start_datetime = self._parse_datetime(date, time)
            if not start_datetime:
                return {
                    "success": False,
                    "error": "Invalid date or time format"
                }
            
            # Parse duration and calculate end time
            duration_delta = self._parse_duration(duration)
            end_datetime = start_datetime + duration_delta
            
            # Prepare attendees
            attendee_list = []
            if attendees:
                for email in attendees:
                    attendee_list.append({"email": email.strip()})
            
            # Create event object with proper timezone
            event_body = {
                "summary": title,
                "description": description,
                "start": {
                    "dateTime": start_datetime.isoformat(),
                    "timeZone": "Asia/Colombo"  # Changed from UTC to Sri Lanka timezone
                },
                "end": {
                    "dateTime": end_datetime.isoformat(),
                    "timeZone": "Asia/Colombo"  # Changed from UTC to Sri Lanka timezone
                }
            }
            
            # Add attendees if provided
            if attendee_list:
                event_body["attendees"] = attendee_list
                event_body["guestsCanSeeOtherGuests"] = True
                event_body["sendNotifications"] = True
            
            # Create the event
            event = service.events().insert(
                calendarId='primary',
                body=event_body,
                sendNotifications=True
            ).execute()
            
            event_details = {
                "id": event.get("id"),
                "title": title,
                "start_time": start_datetime.strftime("%Y-%m-%d %H:%M %Z"),
                "end_time": end_datetime.strftime("%Y-%m-%d %H:%M %Z"),
                "duration": duration,
                "description": description,
                "attendees": attendees or [],
                "link": event.get("htmlLink")
            }
            
            logger.info(f"Event created successfully: {event.get('id')}")
            
            return {
                "success": True,
                "event_details": event_details,
                "google_event": event
            }
            
        except Exception as e:
            logger.error(f"Error creating calendar event: {str(e)}")
            return {
                "success": False,
                "error": str(e)
            }
    
    async def get_events(
        self,
        date: str = None,
        max_results: int = 10
    ) -> Dict[str, Any]:
        """
        Get calendar events
        
        Args:
            date (str): Specific date to get events for (optional)
            max_results (int): Maximum number of events to return
            
        Returns:
            Dict[str, Any]: Result with success status and events list
        """
        try:
            logger.info("Retrieving calendar events")
            
            service = self._get_service()
            if not service:
                return {
                    "success": False,
                    "error": "Failed to connect to Google Calendar service"
                }
            
            # Set time boundaries with proper timezone
            if date:
                start_date = self._parse_datetime(date, "00:00")
                end_date = start_date + timedelta(days=1)
            else:
                now = datetime.now(self.local_timezone)
                start_date = now
                end_date = start_date + timedelta(days=7)  # Next 7 days
            
            time_min = start_date.isoformat()
            time_max = end_date.isoformat()
            
            # Get events
            events_result = service.events().list(
                calendarId='primary',
                timeMin=time_min,
                timeMax=time_max,
                maxResults=max_results,
                singleEvents=True,
                orderBy='startTime'
            ).execute()
            
            events = events_result.get('items', [])
            
            # Format events
            formatted_events = []
            for event in events:
                start = event['start'].get('dateTime', event['start'].get('date'))
                end = event['end'].get('dateTime', event['end'].get('date'))
                
                # Parse start time
                if 'T' in start:
                    start_dt = parser.parse(start)
                    # Convert to local timezone if needed
                    if start_dt.tzinfo is None:
                        start_dt = self.local_timezone.localize(start_dt)
                    elif start_dt.tzinfo != self.local_timezone:
                        start_dt = start_dt.astimezone(self.local_timezone)
                    start_time = start_dt.strftime("%Y-%m-%d %H:%M %Z")
                else:
                    start_time = start + " (All Day)"
                
                formatted_event = {
                    "id": event.get("id"),
                    "title": event.get("summary", "Untitled"),
                    "start_time": start_time,
                    "description": event.get("description", ""),
                    "link": event.get("htmlLink"),
                    "attendees": [
                        attendee.get("email") 
                        for attendee in event.get("attendees", [])
                    ]
                }
                
                formatted_events.append(formatted_event)
            
            logger.info(f"Retrieved {len(formatted_events)} events")
            
            return {
                "success": True,
                "events": formatted_events
            }
            
        except Exception as e:
            logger.error(f"Error retrieving calendar events: {str(e)}")
            return {
                "success": False,
                "error": str(e)
            }
    
    async def update_event(
        self,
        event_id: str,
        title: str = None,
        date: str = None,
        time: str = None,
        duration: str = None,
        description: str = None,
        attendees: List[str] = None
    ) -> Dict[str, Any]:
        """
        Update an existing calendar event
        
        Args:
            event_id (str): ID of the event to update
            title (str): New title (optional)
            date (str): New date (optional)
            time (str): New time (optional)
            duration (str): New duration (optional)
            description (str): New description (optional)
            attendees (List[str]): New attendee list (optional)
            
        Returns:
            Dict[str, Any]: Result with success status and updated event details
        """
        try:
            logger.info(f"Updating calendar event: {event_id}")
            
            service = self._get_service()
            if not service:
                return {
                    "success": False,
                    "error": "Failed to connect to Google Calendar service"
                }
            
            # Get the existing event
            existing_event = service.events().get(
                calendarId='primary',
                eventId=event_id
            ).execute()
            
            # Update fields
            if title:
                existing_event['summary'] = title
            
            if description is not None:
                existing_event['description'] = description
            
            if date and time:
                start_datetime = self._parse_datetime(date, time)
                if start_datetime:
                    existing_event['start']['dateTime'] = start_datetime.isoformat()
                    existing_event['start']['timeZone'] = "Asia/Colombo"
                    
                    if duration:
                        duration_delta = self._parse_duration(duration)
                        end_datetime = start_datetime + duration_delta
                        existing_event['end']['dateTime'] = end_datetime.isoformat()
                        existing_event['end']['timeZone'] = "Asia/Colombo"
            
            if attendees is not None:
                attendee_list = []
                for email in attendees:
                    attendee_list.append({"email": email.strip()})
                existing_event['attendees'] = attendee_list
            
            # Update the event
            updated_event = service.events().update(
                calendarId='primary',
                eventId=event_id,
                body=existing_event,
                sendNotifications=True
            ).execute()
            
            logger.info(f"Event updated successfully: {event_id}")
            
            return {
                "success": True,
                "event_details": {
                    "id": updated_event.get("id"),
                    "title": updated_event.get("summary"),
                    "link": updated_event.get("htmlLink")
                }
            }
            
        except Exception as e:
            logger.error(f"Error updating calendar event: {str(e)}")
            return {
                "success": False,
                "error": str(e)
            }
    
    async def delete_event(self, event_id: str) -> Dict[str, Any]:
        """
        Delete a calendar event
        
        Args:
            event_id (str): ID of the event to delete
            
        Returns:
            Dict[str, Any]: Result with success status
        """
        try:
            logger.info(f"Deleting calendar event: {event_id}")
            
            service = self._get_service()
            if not service:
                return {
                    "success": False,
                    "error": "Failed to connect to Google Calendar service"
                }
            
            # Delete the event
            service.events().delete(
                calendarId='primary',
                eventId=event_id,
                sendNotifications=True
            ).execute()
            
            logger.info(f"Event deleted successfully: {event_id}")
            
            return {
                "success": True,
                "message": "Event deleted successfully"
            }
            
        except Exception as e:
            logger.error(f"Error deleting calendar event: {str(e)}")
            return {
                "success": False,
                "error": str(e)
            }

# Create global instance
calendar_service = CalendarService()