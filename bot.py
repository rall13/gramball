"""
⚽ Пенальти — Telegram-бот с мини-игрой (Mini App / WebApp).

Как запустить:
  1. Создайте бота у @BotFather и получите токен.
  2. Разместите index.html на любом HTTPS-хостинге (GitHub Pages, Vercel, Netlify).
  3. Укажите переменные окружения BOT_TOKEN и GAME_URL.
  4. pip install -r requirements.txt && python bot.py
"""

import asyncio
import json
import logging
import os

from aiogram import Bot, Dispatcher, F
from aiogram.filters import Command
from aiogram.types import (
    InlineKeyboardButton,
    InlineKeyboardMarkup,
    KeyboardButton,
    Message,
    ReplyKeyboardMarkup,
    WebAppInfo,
)

BOT_TOKEN = os.getenv("BOT_TOKEN", "8890399400:AAHjImc1vz98emFFDguQGy2avg7Sn0gHXKE")
GAME_URL = os.getenv("GAME_URL", "https://rall13.github.io/gramball/index.html")

COUNTRY_NAMES = {
    "es": "Испания 🇪🇸",
    "ar": "Аргентина 🇦🇷",
    "br": "Бразилия 🇧🇷",
    "fr": "Франция 🇫🇷",
    "de": "Германия 🇩🇪",
    "en": "Англия En",
    "it": "Италия 🇮🇹",
    "pt": "Португалия 🇵🇹",
    "ru": "Россия 🇷🇺",
    "nl": "Нидерланды 🇳🇱",
    "ma": "Марокко 🇲🇦",
    "jp": "Япония 🇯🇵",
}

logging.basicConfig(level=logging.INFO)

bot = Bot(BOT_TOKEN)
dp = Dispatcher()


@dp.message(Command("start"))
async def cmd_start(message: Message) -> None:
    """Приветствие + кнопка запуска игры.

    Кнопка в reply-клавиатуре нужна, чтобы игра могла
    присылать результат обратно через sendData.
    """
    reply_kb = ReplyKeyboardMarkup(
        keyboard=[[KeyboardButton(text="⚽ Играть в пенальти", web_app=WebAppInfo(url=GAME_URL))]],
        resize_keyboard=True,
    )
    await message.answer(
        "Привет! Это мини-игра «Пенальти» ⚽\n\n"
        "• Выбери свою сборную и соперника\n"
        "• Выбери мяч\n"
        "• Три режима: бей пенальти, стой на воротах или чекань мяч 🎯\n"
        "• Свайпай по мячу, чтобы бить — вратарь будет в форме соперника!\n\n"
        "Жми кнопку ниже 👇",
        reply_markup=reply_kb,
    )


@dp.message(Command("game"))
async def cmd_game(message: Message) -> None:
    """Запуск игры через inline-кнопку (без sendData)."""
    inline_kb = InlineKeyboardMarkup(
        inline_keyboard=[[InlineKeyboardButton(text="⚽ Открыть игру", web_app=WebAppInfo(url=GAME_URL))]]
    )
    await message.answer("Пенальти ждёт! 🧤", reply_markup=inline_kb)


@dp.message(F.web_app_data)
async def on_game_result(message: Message) -> None:
    """Принимаем результат из игры (Telegram.WebApp.sendData)."""
    try:
        data = json.loads(message.web_app_data.data)
    except (json.JSONDecodeError, AttributeError):
        return

    score = data.get("score", 0)
    best = data.get("best", score)
    me = COUNTRY_NAMES.get(data.get("me"), "?")
    op = COUNTRY_NAMES.get(data.get("op"), "?")

    mode = data.get("mode", "striker")
    if mode == "keeper":
        text = (
            f"🧤 Результат: <b>{score}</b> сейв(ов)!\n"
            f"🏆 Рекорд: {best}\n"
            f"🏟 Матч: {me} против {op}"
        )
    elif mode == "juggle":
        text = (
            f"🎯 Чеканка: <b>{score}</b> подряд!\n"
            f"🏆 Рекорд: {best}\n"
            f"⚽ Сборная: {me}"
        )
    else:
        text = (
            f"⚽ Результат: <b>{score}</b> гол(ов)!\n"
            f"🏆 Рекорд: {best}\n"
            f"🏟 Матч: {me} против {op}"
        )
    await message.answer(text, parse_mode="HTML")


async def main() -> None:
    await dp.start_polling(bot)


if __name__ == "__main__":
    asyncio.run(main())
