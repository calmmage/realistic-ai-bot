import asyncio
import random
from enum import Enum
from textwrap import dedent
from typing import Union

from aiogram.types import Message
from botspot.components.data.user_data import User
from botspot.llm_provider import astream_llm
from botspot.utils import answer_safe, reply_safe, typing_status, markdown_to_html
from loguru import logger
from pydantic_settings import BaseSettings
from pydantic import SecretStr

# from dev.chat_coordinator_claude import ChatCoordinator


class UserSettings(User):
    # todo: move from AppSettings and wire in
    model: str = "claude-3-5-haiku"


class SplitterMode(Enum):
    """Mode for splitting messages"""

    NONE = "none"  # do not split
    SIMPLE = "simple"  # just split by \n\n
    SIMPLE_IMPROVED = "simple_improved"  # same as simple, but add heuristics to re-join messages - not too short, not too long.
    MARKDOWN = "markdown"  # split by markdown headers
    STRUCTURED = "structured"  # explicitly request
    MULTI_QUERY = "multi_query"  # do multiple queries to llm - first generate a response, then split it into parts.


class DelayMode(Enum):
    """Mode for delaying messages"""

    NONE = "none"  # do not delay responses
    SIMPLE = "simple"  # delay by a fixed amount of time
    # todo: simple_proportional to message length
    RANDOM = "random"  # delay by a random amount of time
    # todo: random_proportional to message length
    STRUCTURED = "structured"  # explicitly request


class ReplyMode(Enum):
    reply = "reply"  # reply to the user's message
    answer = "answer"  # answer the user's message


class ParallelMessageHandlingMode(Enum):
    ignore = "ignore"  # allow native aiogram approach of handling parallel messages - process each message separately and independently
    interrupt = (
        "interrupt"  # interrupt the current message processing if a new one arrives
    )
    queue = "queue"  # queue the messages and process them one by one


supported_models = [
    # "gpt-4o",
    # "claude-3-5-haiku",
    # "claude-3-5-sonnet",
    # "claude-3-7",
    # "grok-3",
    # "gemini-2.5",
    "claude-3.5-haiku",
    "claude-3.5-sonnet",
    "claude-3.7",
    # OpenAI Models
    # Cheap
    "gpt-4o-mini",
    # "o4-mini",
    "gpt-4.1-nano",
    # Mid
    "gpt-4o",
    # "gpt-4.1",
    # Max
    "o3",
    # "gpt-4",
    # "o1-pro",
    # Google Models
    "gemini-2.5-flash",
    "gemini-2.5-pro",
    # "gemini-2.5-exp",
    # xAI Models
    "grok-3-mini",
    "grok-3",
]


class AppConfig(BaseSettings):
    """Basic app configuration"""

    telegram_bot_token: SecretStr
    # model: str = "claude-3.7" # enable for attachments
    model: str = "claude-3-5-haiku"  # for testing
    # model = Field(default="gpt-4o", choices=supported_models)
    # splitter_mode: SplitterMode = SplitterMode.NONE
    # splitter_mode: SplitterMode = SplitterMode.SIMPLE
    splitter_mode: SplitterMode = SplitterMode.SIMPLE_IMPROVED
    splitter_min_message_length: int = 200  # minimum message length to split

    # whether to convert messages to markdown before sending
    convert_to_markdown: bool = True

    # region: delay mode
    # delay_mode: DelayMode = DelayMode.NONE
    # delay_mode: DelayMode = DelayMode.SIMPLE
    delay_mode: DelayMode = DelayMode.RANDOM
    delay_before_first_message: float = 0.0  # it takes time to start generating, so..
    delay_simple: float = 5.0  # delay between messages
    delay_random_min: float = 0.0  # minimum delay between messages
    delay_random_max: float = 10.0  # maximum delay between messages
    # endregion: delay mode

    # region: reply mode
    reply_mode: ReplyMode = ReplyMode.answer
    # todo: wire in
    parallel_message_handling_mode: ParallelMessageHandlingMode = (
        ParallelMessageHandlingMode.ignore
    )
    # todo: wire in
    auto_switch_to_reply: bool = True  # automatically switch to reply mode when user sends multple parallel messages
    # endregion: reply mode

    # todo: wire in
    display_typing_status: bool = True  # display typing status

    class Config:
        env_file = "../.env"
        env_file_encoding = "utf-8"
        extra = "ignore"


# todo: system instructions per splitter mode
split_instructions = {
    SplitterMode.NONE: "",  # no extra formatting instructions necessary
    SplitterMode.SIMPLE: "Use \n\n to separate parts of the response.",
    SplitterMode.SIMPLE_IMPROVED: "Use \n\n to separate parts of the response.",  #
    SplitterMode.MARKDOWN: "Use markdown headers to separate parts of the response.",
    SplitterMode.STRUCTURED: dedent(
        """
        We want to split the response to the user into multiple parts grouped by meaning
        - and send them out one by one with a delay so that user has time to read each part.
        """
    ),
}


class App:
    name = "Mini Botspot Template"

    def __init__(self, **kwargs):
        self.config = AppConfig(**kwargs)
        # Initialize the chat coordinator with a reference to this App instance
        # self.chat_coordinator = ChatCoordinator(self)
        logger.info(
            f"Initialized {self.name} with model={self.model}, splitter={self.splitter_mode}, delay={self.delay_mode}"
        )

    # async def startup(self):
    #     """Start the chat coordinator"""
    #     await self.chat_coordinator.start()
    #     logger.info("App startup completed")
    #
    # async def shutdown(self):
    #     """Stop the chat coordinator"""
    #     await self.chat_coordinator.stop()
    #     logger.info("App shutdown completed")

    # region: properties
    @property
    def model(self):
        return self.config.model

    @model.setter
    def model(self, model: str):
        if model not in supported_models:
            logger.error(f"Attempted to set unsupported model: {model}")
            raise ValueError(
                f"Model {model} is not supported. Supported models: {supported_models}"
            )
        logger.info(f"Changing model from {self.config.model} to {model}")
        self.config.model = model

    @property
    def splitter_mode(self) -> SplitterMode:
        return self.config.splitter_mode

    @splitter_mode.setter
    def splitter_mode(self, mode: Union[str, SplitterMode]):
        if isinstance(mode, str):
            mode = SplitterMode(mode)
        logger.info(
            f"Changing splitter mode from {self.config.splitter_mode} to {mode}"
        )
        self.config.splitter_mode = mode

    @property
    def delay_mode(self) -> DelayMode:
        return self.config.delay_mode

    @delay_mode.setter
    def delay_mode(self, mode: Union[str, DelayMode]):
        if isinstance(mode, str):
            mode = DelayMode(mode)
        logger.info(f"Changing delay mode from {self.config.delay_mode} to {mode}")
        self.config.delay_mode = mode

    @property
    def system_message(self) -> str:
        system_message = "You're a helpful assistant."
        system_message += "\n\n" + split_instructions[self.splitter_mode]
        return system_message

    @property
    def reply_mode(self) -> ReplyMode:
        return self.config.reply_mode

    @reply_mode.setter
    def reply_mode(self, mode: Union[str, ReplyMode]):
        if isinstance(mode, str):
            mode = ReplyMode(mode)
        self.config.reply_mode = mode

    @property
    def delay_between_messages(self) -> float:
        return self.config.delay_simple

    @delay_between_messages.setter
    def delay_between_messages(self, delay: float):
        self.config.delay_simple = delay

    @property
    def delay_before_first_message(self) -> float:
        return self.config.delay_before_first_message

    @delay_before_first_message.setter
    def delay_before_first_message(self, delay: float):
        self.config.delay_before_first_message = delay

    @property
    def delay_random_min(self) -> float:
        return self.config.delay_random_min

    @delay_random_min.setter
    def delay_random_min(self, delay: float):
        self.config.delay_random_min = delay

    @property
    def delay_random_max(self) -> float:
        return self.config.delay_random_max

    @delay_random_max.setter
    def delay_random_max(self, delay: float):
        self.config.delay_random_max = delay

    # endregion: properties

    # region: message splitting

    def split_message(self, message: str) -> list[str]:
        if self.splitter_mode == SplitterMode.NONE:
            return [message]
        elif self.splitter_mode == SplitterMode.SIMPLE:
            return message.split("\n\n")
        elif self.splitter_mode == SplitterMode.SIMPLE_IMPROVED:
            return self._split_message_simple_improved(message)

        elif self.splitter_mode == SplitterMode.MARKDOWN:
            raise NotImplementedError("Markdown splitting not implemented")
        elif self.splitter_mode == SplitterMode.STRUCTURED:
            raise NotImplementedError("Structured splitting not implemented")
        else:
            raise ValueError(f"Invalid splitter mode: {self.splitter_mode}")

    def _split_message_simple_improved(self, message: str) -> list[str]:
        logger.debug(
            f"Splitting message of length {len(message)} with min_length={self.config.splitter_min_message_length}"
        )
        # First split by double newlines
        parts = message.split("\n\n")
        logger.debug(f"Initial split produced {len(parts)} parts")

        # Combine parts that are too short
        messages = []
        current_message = ""

        for part in parts:
            if not current_message:
                current_message = part
            elif len(current_message) <= self.config.splitter_min_message_length:
                # Add the part with double newline separator
                current_message += "\n\n" + part
                logger.debug(f"Combined part, new length: {len(current_message)}")
            else:
                # Current message is long enough, save it and start new one
                messages.append(current_message)
                logger.debug(f"Added message of length {len(current_message)}")
                current_message = part

        # Don't forget to add the last message if it exists
        if current_message:
            messages.append(current_message)
            logger.debug(f"Added final message of length {len(current_message)}")

        logger.info(f"Final split produced {len(messages)} messages")
        return messages

    # endregion: message splitting

    async def send_messages(self, messages: list[str], user_message: Message):
        logger.info(
            f"Sending {len(messages)} messages with delay_mode={self.delay_mode}"
        )

        if self.config.convert_to_markdown:
            messages = [markdown_to_html(msg) for msg in messages]

        if self.delay_mode == DelayMode.NONE:
            for i, message in enumerate(messages, 1):
                logger.debug(f"Sending message {i}/{len(messages)}")
                if self.reply_mode == ReplyMode.reply:
                    await reply_safe(user_message, message)
                else:
                    await answer_safe(user_message, message)

        elif self.delay_mode == DelayMode.SIMPLE:
            logger.debug(
                f"Waiting {self.delay_before_first_message}s before first message"
            )
            async with typing_status(user_message.chat.id):
                await asyncio.sleep(self.delay_before_first_message)

            for i, message in enumerate(messages, 1):
                logger.debug(f"Sending message {i}/{len(messages)}")
                if self.reply_mode == ReplyMode.reply:
                    await reply_safe(user_message, message)
                else:
                    await answer_safe(user_message, message)
                logger.debug(
                    f"Waiting {self.delay_between_messages}s before next message"
                )
                async with typing_status(user_message.chat.id):
                    await asyncio.sleep(self.delay_between_messages)

        elif self.delay_mode == DelayMode.RANDOM:
            logger.debug(
                f"Waiting {self.delay_before_first_message}s before first message"
            )
            # set status to typing
            async with typing_status(user_message.chat.id):
                await asyncio.sleep(self.delay_before_first_message)

            for i, message in enumerate(messages, 1):
                logger.debug(f"Sending message {i}/{len(messages)}")
                if self.reply_mode == ReplyMode.reply:
                    await reply_safe(user_message, message)
                else:
                    await answer_safe(user_message, message)
                delay = random.uniform(self.delay_random_min, self.delay_random_max)
                logger.debug(f"Waiting {delay:.2f}s before next message")
                async with typing_status(user_message.chat.id):
                    await asyncio.sleep(delay)
        else:
            logger.error(f"Unsupported delay mode: {self.delay_mode}")
            raise NotImplementedError("Delay mode not implemented")

    async def generate_response(self, input_text: str, user_id: int, attachments: list):
        logger.info(f"Generating response for user {user_id} with model {self.model}")
        logger.debug(
            f"Input text length: {len(input_text)}, attachments: {len(attachments)}"
        )

        return astream_llm(
            prompt=input_text,
            user=user_id,
            attachments=attachments,
            model=self.model,
            system_message=self.system_message,
        )

    # todo: streaming_main_loop
    # def split_message_streaming
