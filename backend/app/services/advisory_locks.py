"""
PostgreSQL advisory locks for concurrent extraction protection.

Provides distributed locking to prevent race conditions during entity
merge and normalization operations across multiple extraction sessions.
"""

import hashlib
import logging
import time
from contextlib import contextmanager
from typing import Optional, Generator, Dict, Any
from sqlalchemy.orm import Session
from sqlalchemy import text

logger = logging.getLogger(__name__)


class AdvisoryLockError(Exception):
    """Exception raised when advisory lock operations fail."""
    pass


class AdvisoryLockManager:
    """
    Manager for PostgreSQL advisory locks with automatic cleanup.
    
    Uses PostgreSQL's advisory lock system to coordinate access to shared
    resources across multiple processes/sessions.
    """
    
    def __init__(self, db: Session):
        self.db = db
        self._held_locks = set()  # Track locks held by this instance
    
    def _compute_lock_id(self, resource_key: str) -> int:
        """
        Compute a consistent 32-bit integer lock ID from a resource key.
        
        PostgreSQL advisory locks use bigint (64-bit) but we use 32-bit
        for simplicity and compatibility.
        """
        # Use SHA256 hash and take first 4 bytes as signed 32-bit integer
        hash_bytes = hashlib.sha256(resource_key.encode()).digest()
        lock_id = int.from_bytes(hash_bytes[:4], byteorder='big', signed=True)
        return lock_id
    
    def try_lock(self, resource_key: str, timeout_seconds: Optional[float] = None) -> bool:
        """
        Try to acquire an advisory lock.
        
        Args:
            resource_key: Unique string identifying the resource to lock
            timeout_seconds: Maximum time to wait for lock (None = no wait)
            
        Returns:
            True if lock acquired, False otherwise
            
        Raises:
            AdvisoryLockError: On database errors
        """
        lock_id = self._compute_lock_id(resource_key)
        
        try:
            if timeout_seconds is None:
                # Non-blocking attempt
                result = self.db.execute(
                    text("SELECT pg_try_advisory_lock(:lock_id)"),
                    {"lock_id": lock_id}
                ).scalar()
                
                if result:
                    self._held_locks.add(lock_id)
                    logger.debug(f"Acquired advisory lock for '{resource_key}' (ID: {lock_id})")
                    return True
                else:
                    logger.debug(f"Failed to acquire advisory lock for '{resource_key}' (ID: {lock_id})")
                    return False
            
            else:
                # Blocking with timeout
                start_time = time.time()
                
                while time.time() - start_time < timeout_seconds:
                    result = self.db.execute(
                        text("SELECT pg_try_advisory_lock(:lock_id)"),
                        {"lock_id": lock_id}
                    ).scalar()
                    
                    if result:
                        self._held_locks.add(lock_id)
                        logger.debug(f"Acquired advisory lock for '{resource_key}' (ID: {lock_id}) after {time.time() - start_time:.2f}s")
                        return True
                    
                    # Brief sleep before retry
                    time.sleep(0.1)
                
                logger.debug(f"Timeout waiting for advisory lock '{resource_key}' (ID: {lock_id})")
                return False
                
        except Exception as e:
            logger.error(f"Error acquiring advisory lock for '{resource_key}': {e}")
            raise AdvisoryLockError(f"Failed to acquire lock: {e}")
    
    def release_lock(self, resource_key: str) -> bool:
        """
        Release an advisory lock.
        
        Args:
            resource_key: Resource key used when acquiring the lock
            
        Returns:
            True if lock was released, False if lock wasn't held
            
        Raises:
            AdvisoryLockError: On database errors
        """
        lock_id = self._compute_lock_id(resource_key)
        
        try:
            result = self.db.execute(
                text("SELECT pg_advisory_unlock(:lock_id)"),
                {"lock_id": lock_id}
            ).scalar()
            
            if result:
                self._held_locks.discard(lock_id)
                logger.debug(f"Released advisory lock for '{resource_key}' (ID: {lock_id})")
                return True
            else:
                logger.warning(f"Attempted to release lock '{resource_key}' (ID: {lock_id}) but it wasn't held")
                return False
                
        except Exception as e:
            logger.error(f"Error releasing advisory lock for '{resource_key}': {e}")
            raise AdvisoryLockError(f"Failed to release lock: {e}")
    
    def release_all_locks(self):
        """
        Release all advisory locks held by this session.
        
        This is automatically called by PostgreSQL when the session ends,
        but can be called explicitly for cleanup.
        """
        try:
            self.db.execute(text("SELECT pg_advisory_unlock_all()"))
            self._held_locks.clear()
            logger.debug("Released all advisory locks")
            
        except Exception as e:
            logger.error(f"Error releasing all advisory locks: {e}")
            raise AdvisoryLockError(f"Failed to release all locks: {e}")
    
    @contextmanager
    def lock(self, resource_key: str, timeout_seconds: Optional[float] = 30.0) -> Generator[bool, None, None]:
        """
        Context manager for advisory locks with automatic cleanup.
        
        Args:
            resource_key: Unique string identifying the resource to lock
            timeout_seconds: Maximum time to wait for lock (None = no wait)
            
        Yields:
            True if lock was acquired, False otherwise
            
        Example:
            with lock_manager.lock("competitor:acme") as acquired:
                if acquired:
                    # Do work while holding the lock
                    process_competitor_data()
                else:
                    # Handle case where lock couldn't be acquired
                    logger.warning("Could not acquire lock, skipping")
        """
        acquired = False
        try:
            acquired = self.try_lock(resource_key, timeout_seconds)
            yield acquired
        finally:
            if acquired:
                try:
                    self.release_lock(resource_key)
                except Exception as e:
                    logger.error(f"Error releasing lock in context manager: {e}")
    
    def get_lock_status(self, resource_key: str) -> Dict[str, Any]:
        """
        Get status information about a lock.
        
        Args:
            resource_key: Resource key to check
            
        Returns:
            Dictionary with lock status information
        """
        lock_id = self._compute_lock_id(resource_key)
        
        try:
            # Check if lock is currently held by any session
            result = self.db.execute(
                text("""
                    SELECT 
                        pid,
                        granted,
                        mode,
                        locktype
                    FROM pg_locks 
                    WHERE locktype = 'advisory' 
                    AND objid = :lock_id
                """),
                {"lock_id": lock_id}
            ).fetchall()
            
            status = {
                "resource_key": resource_key,
                "lock_id": lock_id,
                "is_locked": len(result) > 0,
                "held_by_this_session": lock_id in self._held_locks,
                "holders": []
            }
            
            for row in result:
                status["holders"].append({
                    "pid": row.pid,
                    "granted": row.granted,
                    "mode": row.mode,
                    "locktype": row.locktype
                })
            
            return status
            
        except Exception as e:
            logger.error(f"Error getting lock status for '{resource_key}': {e}")
            raise AdvisoryLockError(f"Failed to get lock status: {e}")


# Convenience functions for common lock patterns
def competitor_lock_key(competitor: str) -> str:
    """Generate lock key for competitor-level operations."""
    return f"competitor:{competitor.lower()}"


def entity_type_lock_key(competitor: str, entity_type: str) -> str:
    """Generate lock key for competitor + entity type operations."""
    return f"competitor:{competitor.lower()}:entity:{entity_type.lower()}"


def extraction_session_lock_key(session_id: int) -> str:
    """Generate lock key for extraction session operations."""
    return f"extraction_session:{session_id}"


@contextmanager
def competitor_lock(db: Session, competitor: str, timeout_seconds: float = 30.0) -> Generator[bool, None, None]:
    """
    Convenience context manager for competitor-level locking.
    
    Args:
        db: Database session
        competitor: Competitor name
        timeout_seconds: Lock timeout
        
    Yields:
        True if lock acquired, False otherwise
        
    Example:
        with competitor_lock(db, "acme") as acquired:
            if acquired:
                # Safely merge entities for ACME
                merge_competitor_entities(competitor_data)
    """
    lock_manager = AdvisoryLockManager(db)
    lock_key = competitor_lock_key(competitor)
    
    with lock_manager.lock(lock_key, timeout_seconds) as acquired:
        yield acquired


@contextmanager  
def entity_type_lock(
    db: Session, 
    competitor: str, 
    entity_type: str, 
    timeout_seconds: float = 30.0
) -> Generator[bool, None, None]:
    """
    Convenience context manager for competitor + entity type locking.
    
    Args:
        db: Database session
        competitor: Competitor name
        entity_type: Entity type (Company, Product, etc.)
        timeout_seconds: Lock timeout
        
    Yields:
        True if lock acquired, False otherwise
    """
    lock_manager = AdvisoryLockManager(db)
    lock_key = entity_type_lock_key(competitor, entity_type)
    
    with lock_manager.lock(lock_key, timeout_seconds) as acquired:
        yield acquired


# Health check function
def advisory_locks_health_check(db: Session) -> Dict[str, Any]:
    """
    Check the health of the advisory lock system.
    
    Returns:
        Health status dictionary
    """
    try:
        # Test basic advisory lock functionality
        test_lock_id = 999999  # Use a specific test ID
        
        # Try to acquire a test lock
        acquire_result = db.execute(
            text("SELECT pg_try_advisory_lock(:lock_id)"),
            {"lock_id": test_lock_id}
        ).scalar()
        
        if not acquire_result:
            return {
                "status": "unhealthy",
                "error": "Could not acquire test advisory lock"
            }
        
        # Release the test lock
        release_result = db.execute(
            text("SELECT pg_advisory_unlock(:lock_id)"),
            {"lock_id": test_lock_id}
        ).scalar()
        
        if not release_result:
            return {
                "status": "degraded",
                "warning": "Could not release test advisory lock"
            }
        
        # Get current advisory lock count
        lock_count = db.execute(
            text("SELECT COUNT(*) FROM pg_locks WHERE locktype = 'advisory'")
        ).scalar()
        
        return {
            "status": "healthy",
            "current_advisory_locks": lock_count,
            "test_passed": True
        }
        
    except Exception as e:
        return {
            "status": "unhealthy",
            "error": str(e),
            "test_passed": False
        }
