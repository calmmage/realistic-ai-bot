import asyncio
import time
from typing import Any, Dict, List, Optional
from dataclasses import dataclass
import datetime
import random

from aiogram.types import Message, Chat
from loguru import logger
from botspot.utils import answer_safe, reply_safe
from apscheduler.schedulers.asyncio import AsyncIOScheduler


@dataclass
class ActivationEvent:
    timestamp: float
    event_type: str
    user_id: int
    data: Optional[Dict[str, Any]] = None
    job_id: Optional[str] = None


@dataclass
class OutgoingMessage:
    timestamp: float
    content: str
    chat_id: int
    user_id: int
    reply_to_message_id: Optional[int] = None
    is_reply: bool = False


class UserState:
    """Tracks the state for a single user"""

    def __init__(self):
        self.incoming_message_queue = (
            asyncio.Queue()
        )  # Queue for messages from this user
        self.outgoing_message_queue = (
            asyncio.Queue()
        )  # Queue for messages to be sent to this user
        self.last_activation_time = 0.0
        self.is_processing = (
            False  # Flag to track if we're currently processing messages for this user
        )


class ChatCoordinator:
    """
    Chat Coordinator class keeps track of all messages and interactions with the user
    and ensures that we send messages at appropriate moments and with the understanding of full context

    The main goal is to simulate real human-like behavior of the chat-bot

    Here are desired features:
    - "accumulation" when user writes a message - when user writes us, wait a little
    - "offline mode" - have periods of down-time, do not respond, then respond after
    - "another thought" - after user stopped sending messages, think a little more and write something
    - random activations
        - about old conversation topics
        - just 'how are you doing'
        - some proactive new ideas
    - "interruption" - what happens when user interrupts us while we are still responding to a previous message?

    How we are going to implement this:
    - Incoming queue for incoming messages
    - Outgoing queue for outgoing messages
    - Activation queue for activation events
    - main loop that look at all the queues and fixes the state just in case..

    processing of incoming and outgoing messages only happens in activation events

    Basic example:
    -> User sends us a message
    -> we intend to respond at timestamp x. we create an activation event at timestamp x
    -> scheduler runs the job at timestamp x - activation
    -> activation looks at the state of the queues, if no new messages arrived - we proceed as planned
    if new messages - re-evaluate, based on their timestamp and other contextual info
    """

    def __init__(self, app):
        """
        Initialize the ChatCoordinator with references to necessary components.

        Args:
            app: An instance of the App class with configuration and utility methods
        """
        self.app = app

        # Initialize scheduler (use local scheduler for now)
        # In a production app, would use botspot.deps_getters.get_scheduler()
        self.scheduler = AsyncIOScheduler()
        self.scheduler.start()

        # Dictionary to track user states
        self.user_states = {}

        # Track if the coordinator is running
        self.running = False

        logger.info("ChatCoordinator initialized")

    def _get_user_state(self, user_id: int) -> UserState:
        """Get or create a UserState for the given user_id"""
        if user_id not in self.user_states:
            self.user_states[user_id] = UserState()
        return self.user_states[user_id]

    async def start(self):
        """Start the ChatCoordinator's processing loop and initialize resources."""
        if self.running:
            logger.warning("ChatCoordinator is already running")
            return

        self.running = True

        # Schedule periodic check for outgoing messages
        self.scheduler.add_job(
            self._process_all_outgoing_queues,
            "interval",
            seconds=1,
            id="process_outgoing_queue",
            replace_existing=True,
        )

        logger.info("ChatCoordinator started")

    async def stop(self):
        """Stop the ChatCoordinator and clean up resources."""
        if not self.running:
            logger.warning("ChatCoordinator is not running")
            return

        self.running = False

        # Remove the scheduled job
        self.scheduler.remove_job("process_outgoing_queue")

        logger.info("ChatCoordinator stopped")

    async def handle_incoming_message(self, message: Message):
        """
        Handle an incoming message from a user.

        Args:
            message: The aiogram Message object
        """
        if not message.from_user:
            logger.warning("Received message with no from_user")
            return

        user_id = message.from_user.id
        logger.info(f"Received message from user {user_id}")

        # Get the user state
        user_state = self._get_user_state(user_id)

        # Put the message in the user's incoming queue
        await user_state.incoming_message_queue.put(message)

        # Schedule an activation to process this message
        # For now, let's use a simple fixed delay (could be randomized later)
        activation_delay = 1.0  # 1 second delay before we start processing

        # Use current time + delay for the activation timestamp
        activation_time = time.time() + activation_delay

        await self.schedule_activation(
            activation_time=activation_time,
            activation_type="process_incoming",
            user_id=user_id,
            data={"message_id": message.message_id, "chat_id": message.chat.id},
        )

    async def schedule_activation(
        self,
        activation_time: float,
        activation_type: str,
        user_id: int,
        data: Optional[Dict[str, Any]] = None,
    ):
        """
        Schedule an activation event.

        Args:
            activation_time: Unix timestamp when activation should occur
            activation_type: Type of activation (e.g., "process_incoming", "follow_up")
            user_id: The user ID this activation is for
            data: Additional data for the activation
        """
        # Calculate delay in seconds from now
        now = time.time()
        delay = max(0, activation_time - now)

        # Create an activation event
        event = ActivationEvent(
            timestamp=activation_time,
            event_type=activation_type,
            user_id=user_id,
            data=data or {},
        )

        # Schedule the job with apscheduler
        job_id = f"{activation_type}_{user_id}_{activation_time}"
        event.job_id = job_id

        self.scheduler.add_job(
            self._handle_activation,
            "date",
            run_date=time.time() + delay,
            id=job_id,
            replace_existing=True,
            args=[event],
        )

        logger.debug(
            f"Scheduled activation: {activation_type} for user {user_id} at {activation_time} (in {delay:.2f}s)"
        )

    async def _handle_activation(self, event: ActivationEvent):
        """
        Handle an activation event.

        Args:
            event: The activation event to handle
        """
        user_id = event.user_id
        logger.debug(f"Handling activation: {event.event_type} for user {user_id}")

        # Get the user state
        user_state = self._get_user_state(user_id)

        if event.event_type == "process_incoming":
            await self._process_user_incoming_messages(user_id)
        elif event.event_type == "send_message":
            # This activation type would be used for delayed message sending
            if event.data and "message_id" in event.data:
                # Find the message in the outgoing queue and send it
                # For now, just process the outgoing queue
                await self._process_user_outgoing_queue(user_id)
        else:
            logger.warning(f"Unknown activation type: {event.event_type}")

    async def _process_user_incoming_messages(self, user_id: int):
        """Process incoming messages from a specific user's queue."""
        user_state = self._get_user_state(user_id)

        if user_state.incoming_message_queue.empty():
            logger.debug(f"No incoming messages to process for user {user_id}")
            return

        # Set processing flag to prevent concurrent processing
        if user_state.is_processing:
            logger.debug(f"Already processing messages for user {user_id}")
            return

        user_state.is_processing = True

        try:
            # Get a message from the queue
            message = await user_state.incoming_message_queue.get()

            # Extract necessary information
            input_text = message.text or message.caption

            if not input_text:
                logger.warning(
                    f"Received message with no text or caption from user {user_id}"
                )
                user_state.incoming_message_queue.task_done()
                return

            # Get attachments if any
            from botspot.utils.unsorted import get_message_attachments

            attachments = get_message_attachments(message)

            # Generate response using the app's LLM integration
            response_generator = await self.app.generate_response(
                input_text=input_text, user_id=user_id, attachments=attachments
            )

            # Collect the full response
            full_response = ""
            async for chunk in response_generator:
                full_response += chunk

            # Split the response according to app's splitter configuration
            response_parts = self.app.split_message(full_response)

            # Schedule the sending of each part with appropriate delays
            await self._schedule_message_sending(response_parts, message, user_id)

            # Mark the task as done
            user_state.incoming_message_queue.task_done()

            # Update last activation time
            user_state.last_activation_time = time.time()

        finally:
            # Clear processing flag
            user_state.is_processing = False

    async def _schedule_message_sending(
        self, messages: List[str], original_message: Message, user_id: int
    ):
        """
        Schedule messages to be sent with appropriate delays.

        Args:
            messages: List of message parts to send
            original_message: The original message from the user
            user_id: The user ID
        """
        # Calculate send times based on app's delay configuration
        now = time.time()

        # Add delay before first message
        send_time = now + self.app.delay_before_first_message

        for i, message_content in enumerate(messages):
            # Prepare outgoing message
            outgoing = OutgoingMessage(
                timestamp=send_time,
                content=message_content,
                chat_id=original_message.chat.id,
                user_id=user_id,
                reply_to_message_id=original_message.message_id
                if i == 0 and self.app.reply_mode.value == "reply"
                else None,
                is_reply=self.app.reply_mode.value == "reply",
            )

            # Get the user state
            user_state = self._get_user_state(user_id)

            # Add to the user's outgoing queue
            await user_state.outgoing_message_queue.put(outgoing)

            # Calculate delay for next message
            if i < len(messages) - 1:  # Not the last message
                if self.app.delay_mode.value == "simple":
                    delay = self.app.delay_between_messages
                elif self.app.delay_mode.value == "random":
                    delay = random.uniform(
                        self.app.delay_random_min, self.app.delay_random_max
                    )
                else:
                    delay = 0  # No delay for other modes

                send_time += delay

        # Schedule an immediate check of the outgoing queue
        await self._process_user_outgoing_queue(user_id)

    async def _process_all_outgoing_queues(self):
        """Process outgoing message queues for all users"""
        for user_id, user_state in self.user_states.items():
            await self._process_user_outgoing_queue(user_id)

    async def _process_user_outgoing_queue(self, user_id: int):
        """Process the outgoing message queue for a specific user, sending messages whose time has arrived."""
        user_state = self._get_user_state(user_id)

        if user_state.outgoing_message_queue.empty():
            return

        # Get current time
        now = time.time()

        # We need to peek at the queue without removing items
        # Since Queue doesn't support peeking directly, we'll use a temporary list
        messages_to_send = []

        # Get all messages whose send time has arrived
        while not user_state.outgoing_message_queue.empty():
            # Get message but keep it in the queue for now
            message = await user_state.outgoing_message_queue.get()

            if message.timestamp <= now:
                # Time to send this message
                messages_to_send.append(message)
            else:
                # Put it back in the queue and stop checking
                # (assumption: messages are ordered by timestamp)
                await user_state.outgoing_message_queue.put(message)
                break

        # Now send all the messages whose time has arrived
        for message in messages_to_send:
            await self._send_message(message)
            # Mark as done in the queue
            user_state.outgoing_message_queue.task_done()

    async def _send_message(self, message: OutgoingMessage):
        """
        Send a message to the user.

        Args:
            message: The outgoing message to send
        """
        logger.debug(
            f"Sending message to chat {message.chat_id} for user {message.user_id}"
        )

        # Apply markdown transformation if configured
        content = message.content
        if self.app.config.convert_to_markdown:
            from src.utils import markdown_to_html

            content = markdown_to_html(content)

        # Send the message using the appropriate method
        if message.is_reply and message.reply_to_message_id:
            from aiogram.types import Message as AiogramMessage

            # Create a Message object with the necessary fields for reply_safe
            msg = AiogramMessage(
                message_id=message.reply_to_message_id,
                date=datetime.datetime.now(),  # Use current datetime instead of 0
                chat=Chat(
                    id=message.chat_id, type="private"
                ),  # Use Chat object instead of dict
            )
            await reply_safe(msg, content)
        else:
            # For answer_safe, we need to create a Message object for chat_id
            dummy_msg = Message(
                message_id=1,  # Dummy ID
                date=datetime.datetime.now(),
                chat=Chat(id=message.chat_id, type="private"),
            )
            await answer_safe(dummy_msg, content)
