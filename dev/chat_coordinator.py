import asyncio
from enum import Enum
from typing import Any, Dict, Optional, Union

from botspot.utils import get_scheduler
from pydantic import BaseModel


class ActivationType(Enum):
    generate_message = "generate_message"
    send_message = "send_message"


class Activation(BaseModel):
    timestamp: float
    activation_type: ActivationType
    user_id: int
    data: Optional[Dict[str, Any]] = None
    job_id: Optional[str] = None


class ChatCoordinator:
    def __init__(self):
        self.scheduler = get_scheduler()

        self.incoming_message_queue = asyncio.Queue()
        self.outgoing_message_queue = asyncio.Queue()

    def _schedule_activation(
        self,
        activation_time: float,
        activation_type: Union[str, ActivationType],
        user_id: int,
        data: Optional[Dict[str, Any]] = None,
    ):
        if isinstance(activation_type, str):
            activation_type = ActivationType(activation_type)
        activation = Activation(
            timestamp=activation_time,
            activation_type=activation_type,
            user_id=user_id,
            data=data,
        )
        self.scheduler.add_job(
            self._handle_activation, "date", run_date=activation_time, args=[activation]
        )

    def _handle_activation(self, activation: Activation):
        if activation.activation_type == ActivationType.generate_message:
            self._handle_generate_message(activation)
        elif activation.activation_type == ActivationType.send_message:
            self._handle_send_message(activation)

    def _handle_generate_message(self, activation: Activation):
        # todo: check if there are new messages from the user and there is a future
        # todo: check if the messages from user are already being processed by another activation

        pass

    def _handle_send_message(self, activation: Activation):
        pass
