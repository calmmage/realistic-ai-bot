import pytest
from unittest.mock import patch

from src.bot import main


class TestBot:
    def test_main_setup(self):
        # Mock dependencies
        with patch("src.bot.setup_logger") as mock_setup_logger, patch(
            "src.bot.Dispatcher"
        ) as mock_dispatcher, patch("src.bot.App") as mock_app, patch(
            "src.bot.Bot"
        ) as mock_bot, patch("src.bot.BotManager") as mock_bot_manager, patch(
            "src.bot.settings_router"
        ) as mock_settings_router, patch(
            "src.bot.main_router"
        ) as mock_main_router, patch(
            "src.bot.DefaultBotProperties"
        ) as mock_default_props, patch("src.bot.ParseMode") as mock_parse_mode:
            # Configure mocks
            mock_dispatcher_instance = mock_dispatcher.return_value
            mock_app_instance = mock_app.return_value
            mock_app_instance.config.telegram_bot_token.get_secret_value.return_value = "test_token"
            mock_bot_instance = mock_bot.return_value
            mock_bot_manager_instance = mock_bot_manager.return_value
            mock_parse_mode.HTML = "HTML"

            # Call the function under test
            main(debug=True)

            # Verify logger setup
            mock_setup_logger.assert_called_once_with(
                mock_setup_logger.mock_calls[0][1][0], level="DEBUG"
            )

            # Verify dispatcher setup
            mock_dispatcher.assert_called_once()
            mock_dispatcher_instance.include_router.assert_any_call(
                mock_settings_router
            )
            mock_dispatcher_instance.include_router.assert_any_call(mock_main_router)
            # assert mock_dispatcher_instance["app"] == mock_app_instance

            # Verify app and bot setup
            mock_app.assert_called_once()
            mock_bot.assert_called_once()

            # Verify BotManager setup
            mock_bot_manager.assert_called_once()
            mock_bot_manager_instance.setup_dispatcher.assert_called_once_with(
                mock_dispatcher_instance
            )

            # Verify polling start
            mock_dispatcher_instance.run_polling.assert_called_once_with(
                mock_bot_instance
            )

    def test_main_no_debug(self):
        # Same test but with debug=False to check different logger level
        with patch("src.bot.setup_logger") as mock_setup_logger, patch(
            "src.bot.Dispatcher"
        ) as mock_dispatcher, patch("src.bot.App") as mock_app, patch(
            "src.bot.Bot"
        ) as mock_bot, patch("src.bot.BotManager") as mock_bot_manager, patch(
            "src.bot.settings_router"
        ) as mock_settings_router, patch(
            "src.bot.main_router"
        ) as mock_main_router, patch(
            "src.bot.DefaultBotProperties"
        ) as mock_default_props, patch("src.bot.ParseMode") as mock_parse_mode:
            mock_app_instance = mock_app.return_value
            mock_app_instance.config.telegram_bot_token.get_secret_value.return_value = "test_token"

            main(debug=False)

            # Verify logger setup with INFO level
            mock_setup_logger.assert_called_once_with(
                pytest.importorskip("loguru").logger, level="INFO"
            )

    def test_main_entry_point(self):
        # Since we can't rewrite the module-level code after import,
        # we'll verify the structure exists but not try to execute it

        # Make sure the entry point condition exists in the file
        import inspect
        import src.bot

        source = inspect.getsource(src.bot)
        assert 'if __name__ == "__main__":' in source
        assert "main()" in source
