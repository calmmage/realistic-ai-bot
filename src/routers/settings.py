from aiogram import Router
from aiogram.filters import Command
from aiogram.fsm.context import FSMContext
from aiogram.types import Message
from botspot import commands_menu
from botspot.utils import send_safe

from src.app import App, supported_models

router = Router()

# TIMEZONE_SETUP_METHODS = [
#     "Enter timezone name (e.g. 'Europe/London')",
#     "Send location",
#     "Select from common timezones",
# ]

# COMMON_TIMEZONES = ["UTC", "Europe/London", "Europe/Paris", "America/New_York", "Asia/Tokyo"]


# @botspot_command("timezone", "Set your timezone", visibility="hidden")
# @router.message(Command("timezone"))
# async def timezone_setup(message: Message, state) -> None:
#     """Interactive timezone setup with multiple input methods"""
#
#     # First, ask user how they want to set their timezone
#     method = await ask_user_choice(
#         message.chat.id, "How would you like to set your timezone?", TIMEZONE_SETUP_METHODS, state
#     )
#
#     if not method:
#         await reply_safe(message, "Timezone setup cancelled.")
#         return
#
#     if method == TIMEZONE_SETUP_METHODS[0]:  # Manual entry
#         timezone = await ask_user(
#             message.chat.id, "Please enter your timezone (e.g. 'Europe/London'):", state
#         )
#         if timezone:
#             # Here you would validate the timezone and save it
#             await reply_safe(message, f"Timezone set to: {timezone}")
#         else:
#             await reply_safe(message, "Timezone setup cancelled.")
#
#     elif method == TIMEZONE_SETUP_METHODS[1]:  # Location
#         await reply_safe(
#             message, "Please send your location. Note: This feature is not implemented yet."
#         )
#         # You would implement location handling here
#
#     elif method == TIMEZONE_SETUP_METHODS[2]:  # Common list
#         timezone = await ask_user_choice(
#             message.chat.id, "Select your timezone:", COMMON_TIMEZONES, state
#         )
#         if timezone:
#             await reply_safe(message, f"Timezone set to: {timezone}")
#         else:
#             await reply_safe(message, "Timezone setup cancelled.")


# @botspot_command("error_test", "Test error handling", visibility="hidden")
# @router.message(Command("error_test"))
# async def error_test(message: Message) -> None:
#     """Demonstrate error handling"""
#     raise ValueError("This is a test error!")


@commands_menu.botspot_command("set_model", "Set the model")
@router.message(Command("set_model"))
async def set_model_handler(message: Message, app: App, state: FSMContext):
    """Basic help command handler"""

    from botspot.user_interactions import ask_user_choice

    choices = supported_models
    response = await ask_user_choice(
        chat_id=message.chat.id,
        question="Select a model",
        choices=choices,
        state=state,
        columns=2,
    )
    if response is None:
        await send_safe(message.chat.id, "No model selected")
        return
    app.model = response
    await send_safe(message.chat.id, f"Model set to {response}")


@commands_menu.botspot_command("set_splitter_mode", "Set the splitter mode")
@router.message(Command("set_splitter_mode"))
async def set_splitter_mode_handler(message: Message, app: App, state: FSMContext):
    """Basic help command handler"""

    from botspot.user_interactions import ask_user_choice

    from src.app import SplitterMode

    choices = [mode.value for mode in SplitterMode]
    response = await ask_user_choice(
        chat_id=message.chat.id,
        question="Select a splitter mode",
        choices=choices,
        state=state,
    )
    if response is None:
        await send_safe(message.chat.id, "No splitter mode selected")
        return
    app.splitter_mode = response
    await send_safe(message.chat.id, f"Splitter mode set to {response}")


@commands_menu.botspot_command("set_delay_mode", "Set the delay mode")
@router.message(Command("set_delay_mode"))
async def set_delay_mode_handler(message: Message, app: App, state: FSMContext):
    """Basic help command handler"""

    from botspot.user_interactions import ask_user_choice

    from src.app import DelayMode

    choices = [mode.value for mode in DelayMode]
    response = await ask_user_choice(
        chat_id=message.chat.id,
        question="Select a delay mode",
        choices=choices,
        state=state,
    )
    if response is None:
        await send_safe(message.chat.id, "No delay mode selected")
        return
    app.delay_mode = response
    await send_safe(message.chat.id, f"Delay mode set to {response}")
