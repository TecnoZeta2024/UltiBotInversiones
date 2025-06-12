import asyncio
import logging
from collections import defaultdict
from typing import Callable, List, Dict, Type, Awaitable

from src.ultibot_backend.core.domain_models.events import BaseEvent as Event
from src.ultibot_backend.core.ports import IEventPublisher

logger = logging.getLogger(__name__)

Handler = Callable[[Event], Awaitable[None]]

class AsyncEventBroker(IEventPublisher):
    """
    An asynchronous event broker that facilitates communication between different
    parts of the system using an event-driven approach.
    """

    def __init__(self):
        self._handlers: Dict[Type[Event], List[Handler]] = defaultdict(list)

    async def publish(self, event: Event):
        """
        Publishes an event to all its registered handlers.
        """
        event_type = type(event)
        if event_type in self._handlers:
            logger.info(f"Publishing event: {event_type.__name__} to {len(self._handlers[event_type])} handler(s)")
            tasks = [handler(event) for handler in self._handlers[event_type]]
            await asyncio.gather(*tasks)
        else:
            logger.debug(f"No handlers registered for event: {event_type.__name__}")

    def subscribe(self, event_type: Type[Event], handler: Handler):
        """
        Subscribes a handler to a specific event type.
        """
        self._handlers[event_type].append(handler)
        logger.info(f"Handler {handler.__name__} subscribed to event {event_type.__name__}")

    def unsubscribe(self, event_type: Type[Event], handler: Handler):
        """
        Unsubscribes a handler from a specific event type.
        """
        if handler in self._handlers.get(event_type, []):
            self._handlers[event_type].remove(handler)
            logger.info(f"Handler {handler.__name__} unsubscribed from event {event_type.__name__}")
