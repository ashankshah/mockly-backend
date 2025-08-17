"""
PostHog Analytics Integration for Mockly Backend
Enables server-side tracking for lean startup metrics
"""

import os
from typing import Dict, Any, Optional
import posthog
from datetime import datetime

class MocklyAnalytics:
    """Analytics manager for Mockly using PostHog"""
    
    def __init__(self):
        self.api_key = os.getenv('POSTHOG_API_KEY')
        self.host = os.getenv('POSTHOG_HOST', 'https://app.posthog.com')
        self.enabled = bool(self.api_key and os.getenv('ENVIRONMENT') != 'development')
        
        if self.enabled:
            posthog.api_key = self.api_key
            posthog.host = self.host
            print(f"📊 PostHog analytics initialized for backend tracking")
        else:
            print(f"📊 PostHog analytics disabled (dev mode or missing API key)")
    
    def track_event(self, user_id: str, event_name: str, properties: Dict[str, Any] = None):
        """Track a custom event"""
        if not self.enabled:
            return
            
        if properties is None:
            properties = {}
            
        properties.update({
            'timestamp': datetime.utcnow().isoformat(),
            'source': 'backend',
            'service': 'mockly-api'
        })
        
        try:
            posthog.capture(user_id, event_name, properties)
        except Exception as e:
            print(f"❌ Analytics tracking error: {e}")
    
    def identify_user(self, user_id: str, properties: Dict[str, Any] = None):
        """Identify a user with properties"""
        if not self.enabled:
            return
            
        if properties is None:
            properties = {}
            
        try:
            posthog.identify(user_id, properties)
        except Exception as e:
            print(f"❌ User identification error: {e}")
    
    def track_user_progress_saved(self, user_id: str, progress_data: Dict[str, Any]):
        """Track when user progress is saved (server-side confirmation)"""
        self.track_event(user_id, 'progress_saved_backend', {
            'content_score': progress_data.get('content_score'),
            'voice_score': progress_data.get('voice_score'),
            'face_score': progress_data.get('face_score'),
            'overall_score': progress_data.get('overall_score'),
            'question_type': progress_data.get('question_type'),
            'session_duration_seconds': progress_data.get('session_duration_seconds'),
            'has_transcript': bool(progress_data.get('transcript')),
            'has_star_analysis': bool(progress_data.get('star_analysis')),
            'has_tips': bool(progress_data.get('tips_provided')),
        })
    
    def track_user_authenticated(self, user_id: str, auth_method: str, user_info: Dict[str, Any] = None):
        """Track successful user authentication"""
        properties = {
            'auth_method': auth_method,
            'login_type': 'oauth' if auth_method in ['google', 'linkedin'] else 'email',
        }
        
        if user_info:
            properties.update({
                'first_login': user_info.get('is_new_user', False),
                'user_email_domain': user_info.get('email', '').split('@')[-1] if user_info.get('email') else None,
            })
        
        self.track_event(user_id, 'user_authenticated_backend', properties)
    
    def track_api_endpoint_used(self, user_id: Optional[str], endpoint: str, method: str, status_code: int):
        """Track API endpoint usage for product analytics"""
        self.track_event(user_id or 'anonymous', 'api_endpoint_used', {
            'endpoint': endpoint,
            'method': method,
            'status_code': status_code,
            'endpoint_category': self._categorize_endpoint(endpoint),
        })
    
    def track_analysis_completed(self, user_id: Optional[str], analysis_type: str, analysis_data: Dict[str, Any]):
        """Track when AI analysis is completed"""
        self.track_event(user_id or 'anonymous', 'analysis_completed_backend', {
            'analysis_type': analysis_type,
            'transcript_length': len(analysis_data.get('transcript', '')),
            'content_score': analysis_data.get('content_score'),
            'voice_score': analysis_data.get('voice_score'),
            'face_score': analysis_data.get('face_score'),
            'processing_time_seconds': analysis_data.get('processing_time'),
            'has_star_analysis': bool(analysis_data.get('star_analysis')),
            'tips_count': len(analysis_data.get('tips', [])) if analysis_data.get('tips') else 0,
        })
    
    def _categorize_endpoint(self, endpoint: str) -> str:
        """Categorize API endpoints for better analytics"""
        if '/auth/' in endpoint:
            return 'authentication'
        elif '/users/' in endpoint:
            return 'user_management'
        elif 'analysis' in endpoint:
            return 'ai_analysis'
        elif '/progress' in endpoint:
            return 'progress_tracking'
        else:
            return 'other'

# Global analytics instance
analytics = MocklyAnalytics()

# Convenience functions for common tracking
def track_user_progress_saved(user_id: str, progress_data: Dict[str, Any]):
    """Track user progress save - convenience function"""
    analytics.track_user_progress_saved(user_id, progress_data)

def track_user_authenticated(user_id: str, auth_method: str, user_info: Dict[str, Any] = None):
    """Track user authentication - convenience function"""
    analytics.track_user_authenticated(user_id, auth_method, user_info)

def track_analysis_completed(user_id: Optional[str], analysis_type: str, analysis_data: Dict[str, Any]):
    """Track analysis completion - convenience function"""
    analytics.track_analysis_completed(user_id, analysis_type, analysis_data)

def identify_user(user_id: str, properties: Dict[str, Any]):
    """Identify user - convenience function"""
    analytics.identify_user(user_id, properties)
