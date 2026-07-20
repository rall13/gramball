"""
⚽ Пенальти — Telegram-бот с мини-игрой (Mini App / WebApp).

Как запустить:
  1. Создайте бота у @BotFather и получите токен.
  2. Разместите index.html на любом HTTPS-хостинге (GitHub Pages, Vercel, Netlify).
  3. Укажите переменные окружения BOT_TOKEN, GAME_URL и SERVER_URL.
     SERVER_URL — публичный адрес вашего бота (напр. https://penalty-bot.onrender.com).
     GAME_URL будет автоматически дополнен параметром ?server=SERVER_URL.
  4. pip install -r requirements.txt && python bot.py
"""

import asyncio
import hashlib
import hmac
import json
import logging
import os
from urllib.parse import parse_qsl, urlencode, urlparse, urlunparse, ParseResult

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

BOT_TOKEN    = os.getenv("BOT_TOKEN",    "8890399400:AAHjImc1vz98emFFDguQGy2avg7Sn0gHXKE")
GAME_URL     = os.getenv("GAME_URL",     "https://rall13.github.io/gramball/index.html")
SERVER_URL   = os.getenv("SERVER_URL",   "").rstrip("/gramsoccer_bot")
BOT_USERNAME = os.getenv("BOT_USERNAME", "").lstrip("@gramsoccer_bot")  # например: mypenaltybot

COUNTRY_NAMES = {
    "es": "Испания 🇪🇸",
    "ar": "Аргентина 🇦🇷",
    "br": "Бразилия 🇧🇷",
    "fr": "Франция 🇫🇷",
    "de": "Германия 🇩🇪",
    "en": "Англия 🏴",
    "it": "Италия 🇮🇹",
    "pt": "Португалия 🇵🇹",
    "ru": "Россия 🇷🇺",
    "nl": "Нидерланды 🇳🇱",
    "ma": "Марокко 🇲🇦",
    "jp": "Япония 🇯🇵",
}

logging.basicConfig(level=logging.INFO)
bot = Bot(BOT_TOKEN)
dp  = Dispatcher()


def _game_url_with_server() -> str:
    """Добавляет ?server=, ?bot= к GAME_URL по наличию переменных."""
    parsed = urlparse(GAME_URL)
    qs = dict(parse_qsl(parsed.query))
    if SERVER_URL:
        qs["server"] = SERVER_URL
    if BOT_USERNAME:
        qs["bot"] = BOT_USERNAME
    new = ParseResult(
        parsed.scheme, parsed.netloc, parsed.path,
        parsed.params, urlencode(qs), parsed.fragment,
    )
    return urlunparse(new)


def _validate_init_data(init_data: str) -> dict | None:
    """Проверяет подпись initData от Telegram WebApp. Возвращает объект user или None."""
    try:
        vals = dict(parse_qsl(init_data, strict_parsing=True))
        hash_ = vals.pop("hash", None)
        if not hash_:
            return None
        data_check = "\n".join(f"{k}={v}" for k, v in sorted(vals.items()))
        secret = hmac.new(b"WebAppData", BOT_TOKEN.encode(), hashlib.sha256).digest()
        expected = hmac.new(secret, data_check.encode(), hashlib.sha256).hexdigest()
        if not hmac.compare_digest(expected, hash_):
            return None
        return json.loads(vals.get("user", "{}"))
    except Exception:
        return None


@dp.message(Command("start"))
async def cmd_start(message: Message) -> None:
    url = _game_url_with_server()
    reply_kb = ReplyKeyboardMarkup(
        keyboard=[[KeyboardButton(text="⚽ Играть в пенальти", web_app=WebAppInfo(url=url))]],
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
    url = _game_url_with_server()
    inline_kb = InlineKeyboardMarkup(
        inline_keyboard=[[InlineKeyboardButton(text="⚽ Открыть игру", web_app=WebAppInfo(url=url))]]
    )
    await message.answer("Пенальти ждёт! 🧤", reply_markup=inline_kb)


@dp.message(F.web_app_data)
async def on_game_result_legacy(message: Message) -> None:
    """Fallback: старый sendData (на случай если игра открыта без ?server=)."""
    try:
        data = json.loads(message.web_app_data.data)
    except (json.JSONDecodeError, AttributeError):
        return
    await _send_result(message.from_user.id, data)


async def _send_result(user_id: int, data: dict) -> None:
    score = data.get("score", 0)
    best  = data.get("best", score)
    me    = COUNTRY_NAMES.get(data.get("me"), "?")
    op    = COUNTRY_NAMES.get(data.get("op"), "?")
    mode  = data.get("mode", "striker")
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
    await bot.send_message(user_id, text, parse_mode="HTML")


async def _run_web_server() -> None:
    """
    Мини-вебсервер:
      GET  /        — health-check (для Render / UptimeRobot)
      POST /result  — приём результата из игры без закрытия WebApp
    """
    from aiohttp import web
    from aiohttp.web import middleware

    @middleware
    async def cors(request, handler):
        if request.method == "OPTIONS":
            return web.Response(headers={
                "Access-Control-Allow-Origin": "*",
                "Access-Control-Allow-Headers": "Content-Type",
                "Access-Control-Allow-Methods": "POST, OPTIONS",
            })
        resp = await handler(request)
        resp.headers["Access-Control-Allow-Origin"] = "*"
        return resp

    async def health(_request: web.Request) -> web.Response:
        return web.Response(text="OK")

    async def result(request: web.Request) -> web.Response:
        try:
            body = await request.json()
            init_data = body.get("init_data", "")
            user = _validate_init_data(init_data)
            if not user:
                return web.Response(status=403, text="Forbidden")
            await _send_result(user["id"], body)
            return web.Response(text="ok")
        except Exception as e:
            logging.exception("Error in /result")
            return web.Response(status=500, text=str(e))

    app = web.Application(middlewares=[cors])
    app.router.add_get("/", health)
    app.router.add_options("/result", health)
    app.router.add_post("/result", result)
    runner = web.AppRunner(app)
    await runner.setup()
    port = int(os.getenv("PORT", "10000"))
    site = web.TCPSite(runner, "0.0.0.0", port)
    await site.start()
    logging.info("Web server listening on port %d", port)


async def main() -> None:
    await _run_web_server()
    await dp.start_polling(bot)


if __name__ == "__main__":
    asyncio.run(main())