from aiogram import Router, html, F
from aiogram.filters import Command, CommandStart
from aiogram.types import Message
from botspot import commands_menu
from botspot.utils import send_safe
from textwrap import dedent

from src.app import App

router = Router()


@commands_menu.botspot_command("start", "Start the bot")
@router.message(CommandStart())
async def start_handler(message: Message, app: App):
    await send_safe(
        message.chat.id,
        dedent(
            f"""
        Hey, {html.bold(message.from_user.full_name)}!
        
        This is {app.name}. An experimental project to make chatting with AI to feel like chatting with a real human.
        Just send a message and see how it goes
        
        Price, tokens. For now, bot is free (I added some credits). Use /set_model if the current model is out of budget
        Use /help to for more information or /list_commands to list all commands
        """
        ),
    )


@commands_menu.botspot_command("help", "Show this help message")
@router.message(Command("help"))
async def help_handler(message: Message, app: App):
    """Basic help command handler"""
    await send_safe(
        message.chat.id,
        """
        This is {app.name}!
        
        This is an experimental project to make chatting with AI to feel like chatting with a real human.
        
        Features:
        - Split longer responses in separate messages
        - Realistic pauses and typing between messages
        - planned: Allow AI to contact you randomly throughout the day
        - planned: Down-time, when AI is 'offline' - with responses later.
        
        Todo:
        - message history (for now, only responds to last message)
        
        Price, tokens. For now, bot is free. 
        - I've added small budgets for all vendors - OpenAI, Gemini, Claude and XAI
        - the most budget is available for XAI
        - be warned: that is because they explicitly use all prompts for model training
        
        You can select a model /set_model
        
        Some models support file attachment (notably, claude-3.7), so you can send images
        
        Use /list_commands to see all available commands
        """,
    )


@router.message((F.text | F.caption) & F.chat.type == "private")
async def chat_handler(message: Message, app: App):
    """Basic help command handler"""
    # await send_safe(message.chat.id, f"This is {app.name}. Use /start to begin.")

    input_text = message.text or message.caption
    assert input_text is not None
    assert message.from_user is not None

    # todo: support captions and media
    from botspot.utils.unsorted import get_message_attachments

    attachments = get_message_attachments(message)

    response = await app.generate_response(
        input_text, message.from_user.id, attachments
    )
    result = ""
    async for chunk in response:
        result += chunk
        # messages = app.split_message(result)
        # await app.send_messages(messages, message)

    messages = app.split_message(result)
    await app.send_messages(messages, message)
