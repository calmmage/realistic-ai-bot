import pytest
from unittest.mock import patch, AsyncMock, MagicMock

from aiogram.types import Message
from aiogram.fsm.context import FSMContext
from src.routers.settings import (
    set_model_handler,
    set_splitter_mode_handler,
    set_delay_mode_handler,
)
from src.app import App, SplitterMode, DelayMode, supported_models


@pytest.fixture
def mock_message():
    message = MagicMock(spec=Message)
    message.chat = MagicMock()
    message.chat.id = 12345
    return message


@pytest.fixture
def mock_state():
    state = MagicMock(spec=FSMContext)
    state.get_data = AsyncMock(return_value={})
    state.update_data = AsyncMock()
    return state


@pytest.fixture
def app():
    with patch("src.app.AppConfig"):
        app = App()
        return app


class TestSettingsRouter:
    @pytest.mark.asyncio
    async def test_set_model_handler_with_selection(
        self, mock_message, mock_state, app
    ):
        # Mock the ask_user_choice function to return a model
        selected_model = "claude-3.5-haiku"

        with patch(
            "botspot.user_interactions.ask_user_choice", new_callable=AsyncMock
        ) as mock_ask_user_choice, patch(
            "src.routers.settings.send_safe"
        ) as mock_send_safe, patch("src.routers.settings.get_bot") as mock_get_bot:
            # Configure mocks
            mock_ask_user_choice.return_value = selected_model
            mock_sent_msg = MagicMock()
            mock_sent_msg.pin = AsyncMock()
            mock_send_safe.return_value = mock_sent_msg

            # Call the handler
            await set_model_handler(mock_message, app, mock_state)

            # Verify ask_user_choice was called correctly
            mock_ask_user_choice.assert_called_once_with(
                chat_id=mock_message.chat.id,
                question="Select a model",
                choices=supported_models,
                state=mock_state,
                columns=2,
                cleanup=True,
            )

            # Verify model was set in app
            assert app.model == selected_model

            # Verify message was sent and pinned
            mock_send_safe.assert_called_once_with(
                mock_message.chat.id, f"🤖 Active model: {selected_model}"
            )
            mock_sent_msg.pin.assert_called_once_with(disable_notification=True)

            # Verify state was updated
            mock_state.update_data.assert_called_once_with(
                pinned_model_msg_id=mock_sent_msg.message_id
            )

    @pytest.mark.asyncio
    async def test_set_model_handler_no_selection(self, mock_message, mock_state, app):
        # Mock the ask_user_choice function to return None (no selection)
        with patch(
            "botspot.user_interactions.ask_user_choice", new_callable=AsyncMock
        ) as mock_ask_user_choice, patch(
            "src.routers.settings.send_safe"
        ) as mock_send_safe:
            # Configure mocks
            mock_ask_user_choice.return_value = None

            # Call the handler
            await set_model_handler(mock_message, app, mock_state)

            # Verify ask_user_choice was called
            mock_ask_user_choice.assert_called_once()

            # Verify appropriate message was sent
            mock_send_safe.assert_called_once_with(
                mock_message.chat.id, "No model selected"
            )

            # Verify model was NOT changed in app
            assert app.model != None  # The model should still have its default value

    @pytest.mark.asyncio
    async def test_set_model_handler_with_existing_pin(
        self, mock_message, mock_state, app
    ):
        # Test the case where there's an existing pinned message
        selected_model = "gpt-4o"
        existing_msg_id = 54321

        # Set up the state to return an existing pinned message
        mock_state.get_data = AsyncMock(
            return_value={"pinned_model_msg_id": existing_msg_id}
        )

        with patch(
            "botspot.user_interactions.ask_user_choice", new_callable=AsyncMock
        ) as mock_ask_user_choice, patch(
            "src.routers.settings.send_safe"
        ) as mock_send_safe, patch("src.routers.settings.get_bot") as mock_get_bot:
            # Configure mocks
            mock_ask_user_choice.return_value = selected_model
            mock_bot = MagicMock()
            mock_get_bot.return_value = mock_bot
            mock_sent_msg = MagicMock()
            mock_sent_msg.pin = AsyncMock()
            mock_send_safe.return_value = mock_sent_msg

            # Call the handler
            await set_model_handler(mock_message, app, mock_state)

            # Verify the old message was unpinned
            mock_bot.unpin_chat_message.assert_called_once_with(
                chat_id=mock_message.chat.id, message_id=existing_msg_id
            )

            # Verify new message was pinned
            mock_sent_msg.pin.assert_called_once()

    @pytest.mark.asyncio
    async def test_set_model_handler_unpin_failure(self, mock_message, mock_state, app):
        # Test handling of exception when trying to unpin a message
        selected_model = "gpt-4o-mini"
        existing_msg_id = 54321

        # Set up the state to return an existing pinned message
        mock_state.get_data = AsyncMock(
            return_value={"pinned_model_msg_id": existing_msg_id}
        )

        with patch(
            "botspot.user_interactions.ask_user_choice", new_callable=AsyncMock
        ) as mock_ask_user_choice, patch(
            "src.routers.settings.send_safe"
        ) as mock_send_safe, patch("src.routers.settings.get_bot") as mock_get_bot:
            # Configure mocks
            mock_ask_user_choice.return_value = selected_model
            mock_bot = MagicMock()
            mock_bot.unpin_chat_message = AsyncMock(side_effect=Exception("Test error"))
            mock_get_bot.return_value = mock_bot
            mock_sent_msg = MagicMock()
            mock_sent_msg.pin = AsyncMock()
            mock_send_safe.return_value = mock_sent_msg

            # Call the handler - should not raise exception
            await set_model_handler(mock_message, app, mock_state)

            # Verify we still proceed with setting the model and pinning new message
            assert app.model == selected_model
            mock_sent_msg.pin.assert_called_once()

    @pytest.mark.asyncio
    async def test_set_splitter_mode_handler(self, mock_message, mock_state, app):
        # Test the splitter mode handler
        selected_mode = "simple"

        with patch(
            "botspot.user_interactions.ask_user_choice", new_callable=AsyncMock
        ) as mock_ask_user_choice, patch(
            "src.routers.settings.send_safe"
        ) as mock_send_safe:
            # Configure mocks
            mock_ask_user_choice.return_value = selected_mode

            # Call the handler
            await set_splitter_mode_handler(mock_message, app, mock_state)

            # Verify ask_user_choice was called with all splitter modes
            expected_choices = [mode.value for mode in SplitterMode]
            mock_ask_user_choice.assert_called_once_with(
                chat_id=mock_message.chat.id,
                question="Select a splitter mode",
                choices=expected_choices,
                state=mock_state,
            )

            # Verify splitter mode was set in app
            assert app.splitter_mode == SplitterMode.SIMPLE

            # Verify confirmation message was sent
            mock_send_safe.assert_called_once_with(
                mock_message.chat.id, f"Splitter mode set to {selected_mode}"
            )

    @pytest.mark.asyncio
    async def test_set_splitter_mode_handler_no_selection(
        self, mock_message, mock_state, app
    ):
        # Test when no splitter mode is selected
        with patch(
            "botspot.user_interactions.ask_user_choice", new_callable=AsyncMock
        ) as mock_ask_user_choice, patch(
            "src.routers.settings.send_safe"
        ) as mock_send_safe:
            # Configure mocks
            mock_ask_user_choice.return_value = None
            original_mode = app.splitter_mode

            # Call the handler
            await set_splitter_mode_handler(mock_message, app, mock_state)

            # Verify ask_user_choice was called
            mock_ask_user_choice.assert_called_once()

            # Verify appropriate message was sent
            mock_send_safe.assert_called_once_with(
                mock_message.chat.id, "No splitter mode selected"
            )

            # Verify splitter mode was NOT changed
            assert app.splitter_mode == original_mode

    @pytest.mark.asyncio
    async def test_set_delay_mode_handler(self, mock_message, mock_state, app):
        # Test the delay mode handler
        selected_mode = "simple"

        with patch(
            "botspot.user_interactions.ask_user_choice", new_callable=AsyncMock
        ) as mock_ask_user_choice, patch(
            "src.routers.settings.send_safe"
        ) as mock_send_safe:
            # Configure mocks
            mock_ask_user_choice.return_value = selected_mode

            # Call the handler
            await set_delay_mode_handler(mock_message, app, mock_state)

            # Verify ask_user_choice was called with all delay modes
            expected_choices = [mode.value for mode in DelayMode]
            mock_ask_user_choice.assert_called_once_with(
                chat_id=mock_message.chat.id,
                question="Select a delay mode",
                choices=expected_choices,
                state=mock_state,
            )

            # Verify delay mode was set in app
            assert app.delay_mode == DelayMode.SIMPLE

            # Verify confirmation message was sent
            mock_send_safe.assert_called_once_with(
                mock_message.chat.id, f"Delay mode set to {selected_mode}"
            )

    @pytest.mark.asyncio
    async def test_set_delay_mode_handler_no_selection(
        self, mock_message, mock_state, app
    ):
        # Test when no delay mode is selected
        with patch(
            "botspot.user_interactions.ask_user_choice", new_callable=AsyncMock
        ) as mock_ask_user_choice, patch(
            "src.routers.settings.send_safe"
        ) as mock_send_safe:
            # Configure mocks
            mock_ask_user_choice.return_value = None
            original_mode = app.delay_mode

            # Call the handler
            await set_delay_mode_handler(mock_message, app, mock_state)

            # Verify ask_user_choice was called
            mock_ask_user_choice.assert_called_once()

            # Verify appropriate message was sent
            mock_send_safe.assert_called_once_with(
                mock_message.chat.id, "No delay mode selected"
            )

            # Verify delay mode was NOT changed
            assert app.delay_mode == original_mode
