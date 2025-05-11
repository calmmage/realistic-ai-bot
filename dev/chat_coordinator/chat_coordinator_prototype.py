# # Part 1 - Chat Coordinator
# %%
from datetime import datetime, timedelta
from pydantic import BaseModel
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from enum import Enum
from typing import List, Callable
import asyncio


class ChatCoordinatorBase:
    pass


class EventType(Enum):
    HANDLE_INPUT_MESSAGE = "handle_input_message"
    HANDLE_OUTPUT_MESSAGE = "handle_output_message"


# class Event(BaseModel):
#     event_type: EventType


class InputMessage(BaseModel):
    message: str
    timestamp: datetime


class OutputMessage(BaseModel):
    message: str
    timestamp: datetime


class ChatCoordinator(ChatCoordinatorBase):
    input_buffer = 5  # seconds

    def __init__(self, output_callback: Callable[[str], None]):
        self.input_messages = []  # input, timestamp
        # self.output_messages = []
        self.events_log = []

        self.scheduler = AsyncIOScheduler()

        self.output_callback = output_callback

    def _add_input_message(self, message: InputMessage):
        # todo: add proper multi-user support
        self.input_messages.append(message)

    def _clean_input_messages(self):
        # remove all input messages
        # todo: add proper multi-user support
        self.input_messages = []

    def add_input_message(self, message: str):
        timestamp = datetime.now()
        input_msg = InputMessage(message=message, timestamp=timestamp)
        self._add_input_message(input_msg)

        # schedule event to handle input message
        self.scheduler.add_job(
            self.handle_input_message,
            "date",
            kwargs={"message": input_msg},
            run_date=datetime.now() + timedelta(seconds=self.input_buffer),
            misfire_grace_time=60,  # Allow job to be executed up to 60 seconds late
        )

    # region: event processors
    def _check_new_messages_arrived(self, timestamp: datetime):
        # check if new input messages arrived after the original one.
        for message in self.input_messages:
            if message.timestamp > timestamp:
                return True
        return False

    def _process_messages(self, messages: List[InputMessage]) -> List[OutputMessage]:
        # for now - mock response
        # return [OutputMessage(message="Hello, how can I help you today?", timestamp=datetime.now())]
        responses = []
        target_timestamp = datetime.now() + timedelta(seconds=1)
        responses.append(
            OutputMessage(
                message=f"I see {len(messages)} messages from you",
                timestamp=target_timestamp,
            )
        )

        if len(messages) > 5:
            target_timestamp = datetime.now() + timedelta(seconds=2)
            responses.append(
                OutputMessage(message="That's a lot!", timestamp=target_timestamp)
            )

        return responses

    def handle_input_message(self, message: InputMessage):
        # step 1: check if new input messages arrived after the original one.
        if self._check_new_messages_arrived(message.timestamp):
            return

        to_process = self.input_messages.copy()
        self._clean_input_messages()
        responses = self._process_messages(to_process)
        for response in responses:
            self.scheduler.add_job(
                self.handle_output_message,
                "date",
                kwargs={"message": response.message},
                run_date=response.timestamp,
                misfire_grace_time=60,  # Allow job to be executed up to 60 seconds late
            )

    def handle_output_message(self, message: str):
        # todo: check if new input messages arrived between now and then. If yes - cancel and allow to respond again.
        # todo: behavior 1 - stop responding
        # todo: behavior 2 - still respond, no matter what.
        # decide the behavior
        #  - ask ai what to do
        #  - randomly decide
        #  - depending on the amount of planned response messages. If like 10 messages are queued - worth interrupting for sure..
        #  - activate 'answer' instead of 'respond' aiogram mode.
        self.output_callback(message)

    def run(self):
        self.scheduler.start()


# Part 2 - App
# %%
class AppBase:
    pass


class App(AppBase):
    def __init__(self, output_callback: Callable[[str], None]):
        self.chat_coordinator = ChatCoordinator(output_callback)

    def new_message(self, message: str):
        self.chat_coordinator.add_input_message(message)

    def run(self):
        self.chat_coordinator.run()


# # Part 3 - frontend, chat emulator
# %%
async def async_main():
    def output_callback(message):
        print(f"Bot: {message}")

    app = App(output_callback=output_callback)
    app.run()

    print("Chat started. Type 'exit' to quit.")

    while True:
        try:
            # Use asyncio to get input without blocking
            user_input = await asyncio.get_event_loop().run_in_executor(
                None, input, "You: "
            )
            if user_input.lower() == "exit":
                break
            else:
                # print(">", user_input)
                app.new_message(user_input)
        except (EOFError, KeyboardInterrupt):
            break

    print("Shutting down...")


def main():
    asyncio.run(async_main())


if __name__ == "__main__":
    main()
