import asyncio
import logging
from typing import Dict, List, Callable, Any, Awaitable

logger = logging.getLogger("EventBroker")
logger.setLevel(logging.INFO)

class EventBroker:
    def __init__(self):
        # Maps event_type (str) to list of async callbacks
        self._subscribers: Dict[str, List[Callable[[Dict[str, Any]], Awaitable[None]]]] = {}

    def subscribe(self, event_type: str, callback: Callable[[Dict[str, Any]], Awaitable[None]]):
        if event_type not in self._subscribers:
            self._subscribers[event_type] = []
        self._subscribers[event_type].append(callback)
        logger.info(f"Subscribed callback to event: {event_type}")

    async def publish(self, event_type: str, payload: Dict[str, Any]):
        logger.info(f"Publishing event: {event_type} with payload keys: {list(payload.keys())}")
        
        # Exact match handlers
        handlers = list(self._subscribers.get(event_type, []))
        
        # Wildcard match handlers (e.g., "twin.*" or "*")
        for registered_type, registered_handlers in self._subscribers.items():
            if registered_type.endswith(".*") and event_type.startswith(registered_type[:-2]):
                handlers.extend(registered_handlers)
            elif registered_type == "*":
                handlers.extend(registered_handlers)
                
        if not handlers:
            return

        # Execute all handlers concurrently in background tasks to avoid blocking the main thread
        tasks = []
        for handler in handlers:
            # We copy the payload to prevent multi-threaded modification side effects
            payload_copy = payload.copy()
            payload_copy["event_type"] = event_type
            
            task = asyncio.create_task(self._safe_execute(handler, payload_copy))
            tasks.append(task)
            
        await asyncio.gather(*tasks, return_exceptions=True)

    async def _safe_execute(self, handler: Callable[[Dict[str, Any]], Awaitable[None]], payload: Dict[str, Any]):
        try:
            await handler(payload)
        except Exception as e:
            logger.error(f"Error executing event handler {handler.__name__} for event {payload.get('event_type')}: {e}", exc_info=True)

# Global event broker instance
event_broker = EventBroker()
