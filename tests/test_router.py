import pytest
from unittest.mock import patch, AsyncMock, MagicMock

from aiogram.types import Message, User, Chat
from src.router import start_handler, help_handler, chat_handler
from src.app import App


# Define a proper async iterator class for mocking streaming responses
class AsyncMockStream:
    def __init__(self, content):
        self.content = content
        self.consumed = False

    def __aiter__(self):
        return self

    async def __anext__(self):
        if self.consumed:
            raise StopAsyncIteration
        self.consumed = True
        return self.content


@pytest.fixture
def mock_message():
    message = MagicMock(spec=Message)
    message.from_user = MagicMock(spec=User)
    message.from_user.id = 12345
    message.from_user.full_name = "Test User"
    message.chat = MagicMock(spec=Chat)
    message.chat.id = 12345
    message.text = "Test message"
    message.caption = None
    return message


@pytest.fixture
def app():
    with patch("src.app.AppConfig"):
        app = App()
        return app


class TestRouter:
    @pytest.mark.asyncio
    async def test_start_handler(self, mock_message, app):
        with patch("src.router.send_safe") as mock_send:
            await start_handler(mock_message, app)

            # Check if send_safe was called
            mock_send.assert_called_once()

            # Check content of the message
            call_args = mock_send.call_args[0]
            assert call_args[0] == mock_message.chat.id
            assert app.name in call_args[1]
            assert mock_message.from_user.full_name in call_args[1]

    @pytest.mark.asyncio
    async def test_help_handler(self, mock_message, app):
        with patch("src.router.send_safe") as mock_send:
            await help_handler(mock_message, app)

            # Check if send_safe was called
            mock_send.assert_called_once()

            # Check content of the message
            call_args = mock_send.call_args[0]
            assert call_args[0] == mock_message.chat.id
            assert "Features:" in call_args[1]

    @pytest.mark.asyncio
    async def test_chat_handler_with_text(self, mock_message, app):
        # Mock app.generate_response and app.send_messages
        app.split_message = MagicMock(
            return_value=["Response part 1", "Response part 2"]
        )
        app.send_messages = AsyncMock()

        # Define a proper async iterator class
        class AsyncMockStream:
            def __init__(self, content):
                self.content = content
                self.consumed = False

            def __aiter__(self):
                return self

            async def __anext__(self):
                if self.consumed:
                    raise StopAsyncIteration
                self.consumed = True
                return self.content

        # Create a fake response
        response_content = "Response part 1Response part 2"
        stream = AsyncMockStream(response_content)

        # Mock the response function
        app.generate_response = AsyncMock(return_value=stream)

        with patch("botspot.utils.unsorted.get_message_attachments", return_value=[]):
            await chat_handler(mock_message, app)

            # Verify generate_response was called with correct params
            app.generate_response.assert_called_once_with(
                mock_message.text, mock_message.from_user.id, []
            )

            # Verify split_message was called
            app.split_message.assert_called_once()

            # Verify send_messages was called with the split messages
            app.send_messages.assert_called_once()
            args = app.send_messages.call_args[0]
            assert args[0] == ["Response part 1", "Response part 2"]
            assert args[1] == mock_message

    @pytest.mark.asyncio
    async def test_chat_handler_with_caption(self, mock_message, app):
        # Modify message to have caption instead of text
        mock_message.text = None
        mock_message.caption = "Test caption"

        # Mock app.generate_response and app.send_messages
        app.split_message = MagicMock(return_value=["Response"])
        app.send_messages = AsyncMock()

        # Define a proper async iterator class
        class AsyncMockStream:
            def __init__(self, content):
                self.content = content
                self.consumed = False

            def __aiter__(self):
                return self

            async def __anext__(self):
                if self.consumed:
                    raise StopAsyncIteration
                self.consumed = True
                return self.content

        # Create a fake response
        response_content = "Response"
        stream = AsyncMockStream(response_content)

        # Mock the response function
        app.generate_response = AsyncMock(return_value=stream)

        with patch("botspot.utils.unsorted.get_message_attachments", return_value=[]):
            await chat_handler(mock_message, app)

            # Verify generate_response was called with correct params
            app.generate_response.assert_called_once_with(
                mock_message.caption, mock_message.from_user.id, []
            )

    @pytest.mark.asyncio
    async def test_chat_handler_with_attachments(self, mock_message, app):
        # Mock app methods
        app.split_message = MagicMock(return_value=["Response"])
        app.send_messages = AsyncMock()

        # Define a proper async iterator class
        class AsyncMockStream:
            def __init__(self, content):
                self.content = content
                self.consumed = False

            def __aiter__(self):
                return self

            async def __anext__(self):
                if self.consumed:
                    raise StopAsyncIteration
                self.consumed = True
                return self.content

        # Create a fake response
        response_content = "Response"
        stream = AsyncMockStream(response_content)

        # Mock the response function
        app.generate_response = AsyncMock(return_value=stream)

        # Mock attachments
        mock_attachments = [{"type": "image", "url": "http://example.com/image.jpg"}]

        with patch(
            "botspot.utils.unsorted.get_message_attachments",
            return_value=mock_attachments,
        ):
            await chat_handler(mock_message, app)

            # Verify generate_response was called with attachments
            app.generate_response.assert_called_once_with(
                mock_message.text, mock_message.from_user.id, mock_attachments
            )
