"""User Session Manager - Maintains conversation context."""

from typing import Dict, Any, Optional, List
from datetime import datetime
import uuid

from mcp_framework.storage.database import get_db_manager
from mcp_framework.storage.models import Session, SessionEvent
import structlog

logger = structlog.get_logger()


class SessionContextManager:
    """Manages user session context and history."""
    
    def __init__(self):
        """Initialize session manager."""
        self.db_manager = get_db_manager()
        self.active_sessions: Dict[str, str] = {}  # user_id -> session_id
    
    async def create_session(self, user_id: str, initial_context: Dict[str, Any] = None) -> str:
        """
        Create a new session for a user.
        
        Args:
            user_id: User identifier
            initial_context: Optional initial context
        
        Returns:
            Session ID
        """
        session_id = str(uuid.uuid4())
        
        with self.db_manager.get_session() as db_session:
            session = Session(
                id=session_id,
                user_id=user_id,
                context=initial_context or {},
                is_active=True
            )
            db_session.add(session)
        
        # Track active session
        self.active_sessions[user_id] = session_id
        
        logger.info(f"Created session {session_id[:8]} for user {user_id}")
        return session_id
    
    async def get_or_create_session(self, user_id: str) -> str:
        """Get active session or create new one."""
        # Check if user has active session
        if user_id in self.active_sessions:
            session_id = self.active_sessions[user_id]
            
            # Verify session still exists and is active
            with self.db_manager.get_session() as db_session:
                session = db_session.query(Session).filter_by(
                    id=session_id,
                    is_active=True
                ).first()
                
                if session:
                    return session_id
        
        # Create new session
        return await self.create_session(user_id)
    
    async def add_event(
        self,
        session_id: str,
        event_type: str,
        event_data: Dict[str, Any]
    ) -> None:
        """
        Add an event to session history.
        
        Args:
            session_id: Session ID
            event_type: Type of event (e.g., "user_message", "tool_call", "workflow_start")
            event_data: Event payload
        """
        with self.db_manager.get_session() as db_session:
            event = SessionEvent(
                session_id=session_id,
                event_type=event_type,
                event_data=event_data
            )
            db_session.add(event)
        
        logger.debug(f"Added {event_type} event to session {session_id[:8]}")
    
    async def get_context(self, session_id: str) -> Dict[str, Any]:
        """
        Get session context.
        
        Args:
            session_id: Session ID
        
        Returns:
            Session context dictionary
        """
        with self.db_manager.get_session() as db_session:
            session = db_session.query(Session).filter_by(id=session_id).first()
            
            if not session:
                return {}
            
            return session.context or {}
    
    async def update_context(
        self,
        session_id: str,
        context_updates: Dict[str, Any],
        merge: bool = True
    ) -> None:
        """
        Update session context.
        
        Args:
            session_id: Session ID
            context_updates: Context updates
            merge: Whether to merge with existing context (True) or replace (False)
        """
        with self.db_manager.get_session() as db_session:
            session = db_session.query(Session).filter_by(id=session_id).first()
            
            if session:
                if merge:
                    current_context = session.context or {}
                    current_context.update(context_updates)
                    session.context = current_context
                else:
                    session.context = context_updates
                
                session.updated_at = datetime.utcnow()
    
    async def get_history(
        self,
        session_id: str,
        event_types: Optional[List[str]] = None,
        limit: int = 50
    ) -> List[Dict[str, Any]]:
        """
        Get session event history.
        
        Args:
            session_id: Session ID
            event_types: Optional filter by event types
            limit: Maximum events to return
        
        Returns:
            List of events
        """
        with self.db_manager.get_session() as db_session:
            query = db_session.query(SessionEvent).filter_by(session_id=session_id)
            
            if event_types:
                query = query.filter(SessionEvent.event_type.in_(event_types))
            
            events = query.order_by(SessionEvent.timestamp.desc()).limit(limit).all()
            
            return [
                {
                    "type": event.event_type,
                    "data": event.event_data,
                    "timestamp": event.timestamp.isoformat()
                }
                for event in reversed(events)  # Chronological order
            ]
    
    async def get_preferences(self, session_id: str) -> Dict[str, Any]:
        """Get user preferences from session."""
        with self.db_manager.get_session() as db_session:
            session = db_session.query(Session).filter_by(id=session_id).first()
            
            if session:
                return session.preferences or {}
            return {}
    
    async def update_preferences(
        self,
        session_id: str,
        preferences: Dict[str, Any]
    ) -> None:
        """Update user preferences."""
        with self.db_manager.get_session() as db_session:
            session = db_session.query(Session).filter_by(id=session_id).first()
            
            if session:
                current_prefs = session.preferences or {}
                current_prefs.update(preferences)
                session.preferences = current_prefs
    
    async def close_session(self, session_id: str) -> None:
        """Close a session."""
        with self.db_manager.get_session() as db_session:
            session = db_session.query(Session).filter_by(id=session_id).first()
            
            if session:
                session.is_active = False
                
                # Remove from active tracking
                if session.user_id in self.active_sessions:
                    del self.active_sessions[session.user_id]
                
                logger.info(f"Closed session {session_id[:8]}")


# Global instance
_session_manager: Optional[SessionContextManager] = None


def get_session_manager() -> SessionContextManager:
    """Get global session manager."""
    global _session_manager
    if _session_manager is None:
        _session_manager = SessionContextManager()
    return _session_manager
