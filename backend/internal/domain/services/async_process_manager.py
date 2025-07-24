"""Async process management system for handling cancellable operations."""

import asyncio
import uuid
import threading
from typing import Dict, Optional, Any
from dataclasses import dataclass
from datetime import datetime


@dataclass
class ProcessInfo:
    """Information about a managed process."""
    process_id: str
    name: str
    started_at: datetime
    cancellation_token: 'AsyncCancellationToken'
    metadata: Optional[Dict[str, Any]] = None


class AsyncCancellationToken:
    """Thread-safe cancellation token for async operations."""
    
    def __init__(self, process_id: str = None):
        self.process_id = process_id or str(uuid.uuid4())
        self._cancelled = False
        self._cancellation_reason: Optional[str] = None
        self._cancellation_event = asyncio.Event()
        self._lock = threading.Lock()
    
    async def cancel(self, reason: str = "Cancelled by user") -> None:
        """Cancel the operation asynchronously."""
        with self._lock:
            if not self._cancelled:
                self._cancelled = True
                self._cancellation_reason = reason
                self._cancellation_event.set()
    
    def cancel_sync(self, reason: str = "Cancelled by user") -> None:
        """Cancel the operation synchronously (thread-safe)."""
        with self._lock:
            if not self._cancelled:
                self._cancelled = True
                self._cancellation_reason = reason
                # Set the event in a thread-safe way
                try:
                    loop = asyncio.get_event_loop()
                    if loop.is_running():
                        loop.call_soon_threadsafe(self._cancellation_event.set)
                    else:
                        asyncio.run_coroutine_threadsafe(
                            self._set_event_async(), loop
                        )
                except RuntimeError:
                    # No event loop running, create a new one
                    asyncio.run(self._set_event_async())
    
    async def _set_event_async(self):
        """Helper to set the cancellation event asynchronously."""
        self._cancellation_event.set()
    
    def is_cancelled(self) -> bool:
        """Check if the operation has been cancelled."""
        with self._lock:
            return self._cancelled
    
    async def wait_for_cancellation(self) -> str:
        """Wait for cancellation and return the reason."""
        await self._cancellation_event.wait()
        with self._lock:
            return self._cancellation_reason or "Unknown cancellation reason"
    
    def reset(self) -> None:
        """Reset the token for reuse."""
        with self._lock:
            self._cancelled = False
            self._cancellation_reason = None
            self._cancellation_event.clear()
    
    @property
    def cancellation_reason(self) -> Optional[str]:
        """Get the cancellation reason."""
        with self._lock:
            return self._cancellation_reason


class AsyncProcessManager:
    """Thread-safe manager for async processes with cancellation support."""
    
    def __init__(self):
        self._processes: Dict[str, ProcessInfo] = {}
        self._lock = threading.Lock()
    
    def start_process(self, name: str, metadata: Optional[Dict[str, Any]] = None) -> tuple[str, AsyncCancellationToken]:
        """
        Start a new process and return its ID and cancellation token.
        
        Args:
            name: Human-readable name for the process
            metadata: Optional metadata dictionary
            
        Returns:
            Tuple of (process_id, cancellation_token)
        """
        process_id = str(uuid.uuid4())
        cancellation_token = AsyncCancellationToken(process_id)
        
        process_info = ProcessInfo(
            process_id=process_id,
            name=name,
            started_at=datetime.now(),
            cancellation_token=cancellation_token,
            metadata=metadata or {}
        )
        
        with self._lock:
            self._processes[process_id] = process_info
        
        return process_id, cancellation_token
    
    async def stop_process(self, process_id: str, reason: str = "Stopped by user") -> bool:
        """
        Stop a specific process by cancelling its token.
        
        Args:
            process_id: ID of the process to stop
            reason: Reason for stopping
            
        Returns:
            True if process was found and cancelled, False otherwise
        """
        with self._lock:
            process_info = self._processes.get(process_id)
        
        if process_info:
            await process_info.cancellation_token.cancel(reason)
            return True
        return False
    
    def stop_process_sync(self, process_id: str, reason: str = "Stopped by user") -> bool:
        """
        Stop a specific process synchronously.
        
        Args:
            process_id: ID of the process to stop
            reason: Reason for stopping
            
        Returns:
            True if process was found and cancelled, False otherwise
        """
        with self._lock:
            process_info = self._processes.get(process_id)
        
        if process_info:
            process_info.cancellation_token.cancel_sync(reason)
            return True
        return False
    
    async def stop_all_processes(self, reason: str = "All processes stopped") -> int:
        """
        Stop all active processes.
        
        Args:
            reason: Reason for stopping all processes
            
        Returns:
            Number of processes that were stopped
        """
        with self._lock:
            process_ids = list(self._processes.keys())
        
        stopped_count = 0
        for process_id in process_ids:
            if await self.stop_process(process_id, reason):
                stopped_count += 1
        
        return stopped_count
    
    def stop_all_processes_sync(self, reason: str = "All processes stopped") -> int:
        """
        Stop all active processes synchronously.
        
        Args:
            reason: Reason for stopping all processes
            
        Returns:
            Number of processes that were stopped
        """
        with self._lock:
            process_ids = list(self._processes.keys())
        
        stopped_count = 0
        for process_id in process_ids:
            if self.stop_process_sync(process_id, reason):
                stopped_count += 1
        
        return stopped_count
    
    def cleanup_process(self, process_id: str) -> bool:
        """
        Remove a completed process from tracking.
        
        Args:
            process_id: ID of the process to clean up
            
        Returns:
            True if process was found and removed, False otherwise
        """
        with self._lock:
            return self._processes.pop(process_id, None) is not None
    
    def get_process_info(self, process_id: str) -> Optional[ProcessInfo]:
        """Get information about a specific process."""
        with self._lock:
            return self._processes.get(process_id)
    
    def get_active_processes(self) -> Dict[str, ProcessInfo]:
        """Get all currently tracked processes."""
        with self._lock:
            return self._processes.copy()
    
    def get_process_count(self) -> int:
        """Get the number of currently tracked processes."""
        with self._lock:
            return len(self._processes)
    
    def is_process_active(self, process_id: str) -> bool:
        """Check if a process is currently being tracked."""
        with self._lock:
            return process_id in self._processes