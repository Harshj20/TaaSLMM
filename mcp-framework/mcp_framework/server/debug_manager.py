"""Debug Context Manager - Learns from errors and suggests fixes."""

import hashlib
from typing import Dict, Any, List, Optional
from datetime import datetime

from mcp_framework.storage.database import get_db_manager
from mcp_framework.storage.models import ErrorSignature, Resolution
import structlog

logger = structlog.get_logger()


class DebugHint:
    """Debug hint suggestion."""
    
    def __init__(
        self,
        suggestion: str,
        confidence: float,
        historical_success_rate: float,
        resolution_data: Dict[str, Any]
    ):
        self.suggestion = suggestion
        self.confidence = confidence
        self.historical_success_rate = historical_success_rate
        self.resolution_data = resolution_data
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            "suggestion": self.suggestion,
            "confidence": self.confidence,
            "success_rate": self.historical_success_rate,
            "resolution": self.resolution_data
        }


class DebugContextManager:
    """Manages debug context and error learning."""
    
    def __init__(self):
        """Initialize debug context manager."""
        self.db_manager = get_db_manager()
    
    def _compute_error_signature(
        self,
        error_type: str,
        error_message: str,
        tool_name: Optional[str] = None
    ) -> str:
        """
        Compute a unique signature hash for an error.
        
        Args:
            error_type: Exception type name
            error_message: Error message
            tool_name: Optional tool name
        
        Returns:
            Signature hash
        """
        # Normalize error message (remove dynamic parts like IDs, timestamps)
        normalized = error_message
        
        # Remove UUIDs
        import re
        normalized = re.sub(r'[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}', '<UUID>', normalized)
        
        # Remove file paths with line numbers
        normalized = re.sub(r'File ".*", line \d+', 'File "<PATH>", line <NUM>', normalized)
        
        # Create signature
        sig_string = f"{error_type}:{tool_name or 'UNKNOWN'}:{normalized}"
        
        return hashlib.sha256(sig_string.encode()).hexdigest()
    
    async def capture_error(
        self,
        error: Exception,
        tool_name: str,
        inputs: Dict[str, Any],
        stack_trace: Optional[str] = None
    ) -> str:
        """
        Capture an error for learning.
        
        Args:
            error: The exception that occurred
            tool_name: Name of the tool that failed
            inputs: Tool inputs that caused the error
            stack_trace: Optional stack trace
        
        Returns:
            Error signature ID
        """
        error_type = type(error).__name__
        error_message = str(error)
        
        # Compute signature
        signature_hash = self._compute_error_signature(error_type, error_message, tool_name)
        
        logger.info(f"Capturing error: {error_type} in {tool_name}")
        
        with self.db_manager.get_session() as session:
            # Check if signature exists
            error_sig = session.query(ErrorSignature).filter_by(
                signature_hash=signature_hash
            ).first()
            
            if error_sig:
                # Update existing signature
                error_sig.occurrence_count += 1
                error_sig.last_seen = datetime.utcnow()
                logger.info(f"Updated error signature (count: {error_sig.occurrence_count})")
            else:
                # Create new signature
                error_sig = ErrorSignature(
                    error_type=error_type,
                    error_message=error_message,
                    stack_trace=stack_trace or "",
                    signature_hash=signature_hash
                )
                session.add(error_sig)
                logger.info(f"Created new error signature: {signature_hash[:8]}")
            
            return error_sig.id
    
    async def add_resolution(
        self,
        error_signature_id: str,
        resolution_type: str,
        resolution_data: Dict[str, Any]
    ) -> str:
        """
        Add a resolution for an error signature.
        
        Args:
            error_signature_id: Error signature ID
            resolution_type: Type of resolution (e.g., "parameter_change", "dependency_fix")
            resolution_data: Resolution details
        
        Returns:
            Resolution ID
        """
        with self.db_manager.get_session() as session:
            resolution = Resolution(
                error_signature_id=error_signature_id,
                resolution_type=resolution_type,
                resolution_data=resolution_data
            )
            session.add(resolution)
            
            logger.info(f"Added resolution for error {error_signature_id[:8]}")
            return resolution.id
    
    async def mark_resolution_success(self, resolution_id: str, success: bool = True) -> None:
        """
        Mark a resolution as successful or failed.
        
        Args:
            resolution_id: Resolution ID
            success: Whether the resolution worked
        """
        with self.db_manager.get_session() as session:
            resolution = session.query(Resolution).filter_by(id=resolution_id).first()
            
            if resolution:
                resolution.applied_count += 1
                if success:
                    resolution.success_count += 1
                
                # Update success rate
                resolution.success_rate = resolution.success_count / resolution.applied_count
                
                logger.info(
                    f"Resolution {resolution_id[:8]} success rate: "
                    f"{resolution.success_rate:.2%} ({resolution.success_count}/{resolution.applied_count})"
                )
    
    async def get_debug_hints(
        self,
        error: Exception,
        tool_name: str,
        min_confidence: float = 0.5
    ) -> List[DebugHint]:
        """
        Get debug hints for an error.
        
        Args:
            error: The exception
            tool_name: Tool that failed
            min_confidence: Minimum confidence threshold
        
        Returns:
            List of debug hints
        """
        error_type = type(error).__name__
        error_message = str(error)
        
        # Compute signature
        signature_hash = self._compute_error_signature(error_type, error_message, tool_name)
        
        hints = []
        
        with self.db_manager.get_session() as session:
            # Find matching error signature
            error_sig = session.query(ErrorSignature).filter_by(
                signature_hash=signature_hash
            ).first()
            
            if not error_sig:
                logger.info("No historical data for this error")
                return hints
            
            # Get resolutions with success rate > threshold
            resolutions = session.query(Resolution).filter(
                Resolution.error_signature_id == error_sig.id,
                Resolution.success_rate >= min_confidence
            ).order_by(Resolution.success_rate.desc()).all()
            
            for resolution in resolutions:
                hint = DebugHint(
                    suggestion=self._generate_suggestion(resolution),
                    confidence=resolution.success_rate,
                    historical_success_rate=resolution.success_rate,
                    resolution_data=resolution.resolution_data
                )
                hints.append(hint)
            
            if hints:
                logger.info(f"Found {len(hints)} debug hints for error")
            
        return hints
    
    def _generate_suggestion(self, resolution: Resolution) -> str:
        """Generate human-readable suggestion from resolution."""
        res_type = resolution.resolution_type
        data = resolution.resolution_data
        
        if res_type == "parameter_change":
            param = data.get("parameter")
            value = data.get("new_value")
            return f"Try changing parameter '{param}' to {value}"
        
        elif res_type == "dependency_fix":
            dep = data.get("dependency")
            return f"Install or update dependency: {dep}"
        
        elif res_type == "input_modification":
            field = data.get("field")
            suggestion = data.get("suggestion")
            return f"Modify input field '{field}': {suggestion}"
        
        else:
            return f"Apply {res_type} resolution"
    
    async def get_system_stats(self) -> Dict[str, Any]:
        """Get debug system statistics."""
        with self.db_manager.get_session() as session:
            total_errors = session.query(ErrorSignature).count()
            total_resolutions = session.query(Resolution).count()
            
            # Get error types distribution
            from sqlalchemy import func
            error_types = session.query(
                ErrorSignature.error_type,
                func.count(ErrorSignature.id)
            ).group_by(ErrorSignature.error_type).all()
            
            return {
                "total_unique_errors": total_errors,
                "total_resolutions": total_resolutions,
                "error_types": {et: count for et, count in error_types}
            }


# Global instance
_debug_manager: Optional[DebugContextManager] = None


def get_debug_manager() -> DebugContextManager:
    """Get global debug context manager."""
    global _debug_manager
    if _debug_manager is None:
        _debug_manager = DebugContextManager()
    return _debug_manager
