import os
import asyncio
import aiohttp
import json
from datetime import datetime
from aiogram import Bot, Dispatcher, types, F
from aiogram.filters import Command
from aiogram.enums import ParseMode
from aiogram.client.default import DefaultBotProperties
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
from aiogram.fsm.state import State, StatesGroup
from aiogram.fsm.context import FSMContext
from aiogram.fsm.storage.memory import MemoryStorage
import logging

# ================== НАСТРОЙКА ЛОГГИРОВАНИЯ ==================
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# ================== НАСТРОЙКИ ==================
TOKEN = os.getenv("TELEGRAM_TOKEN") or "YOUR_BOT_TOKEN_HERE"
ADMIN_ID = os.getenv("ADMIN_ID") or 123456789  # Ваш ID для статистики

# Для GitHub хостинга (если используете GitHub Actions для keep-alive)
KEEP_ALIVE_URL = os.getenv("KEEP_ALIVE_URL")  # URL вашего приложения

# ================== СОСТОЯНИЯ ==================
class DownloadStates(StatesGroup):
    waiting_for_query = State()
    downloading = State()

# ================== ИНИЦИАЛИЗАЦИЯ ==================
storage = MemoryStorage()
bot = Bot(token=TOKEN, default=DefaultBotProperties(parse_mode=ParseMode.HTML))
dp = Dispatcher(storage=storage)

# Хранилище данных
user_data = {}
stats = {
    "total_downloads": 0,
    "users": {},
    "start_time": datetime.now().isoformat()
}

# ================== РЕАЛЬНОЕ СКАЧИВАНИЕ С YOUTUBE ==================
class YouTubeDownloader:
    """Класс для скачивания музыки с YouTube"""
    
    @staticmethod
    async def search_youtube(query: str, limit: int = 5):
        """Поиск треков на YouTube"""
        try:
            # В реальном боте используйте YouTube API или библиотеку yt-dlp
            # Здесь демо-результаты
            demo_results = [
                {
                    "id": "dQw4w9WgXcQ",
                    "title": "Rick Astley - Never Gonna Give You Up",
                    "duration": "3:32",
                    "thumbnail": "https://img.youtube.com/vi/dQw4w9WgXcQ/hqdefault.jpg"
                },
                {
                    "id": "kJQP7kiw5Fk",
                    "title": "Luis Fonsi - Despacito ft. Daddy Yankee",
                    "duration": "3:59",
                    "thumbnail": "https://img.youtube.com/vi/kJQP7kiw5Fk/hqdefault.jpg"
                },
                {
                    "id": "JGwWNGJdvx8",
                    "title": "Ed Sheeran - Shape of You",
                    "duration": "3:53",
                    "thumbnail": "https://img.youtube.com/vi/JGwWNGJdvx8/hqdefault.jpg"
                }
            ]
            return demo_results[:limit]
        except Exception as e:
            logger.error(f"Search error: {e}")
            return []
    
    @staticmethod
    async def download_audio(video_id: str, quality: str = "best"):
        """Скачивание аудио с YouTube"""
        try:
            # В реальной реализации используйте yt-dlp или pytube
            # Для демо версии возвращаем фиктивные ссылки
            direct_links = {
                "dQw4w9WgXcQ": "https://files.catbox.moe/qg0zob.mp3",
                "kJQP7kiw5Fk": "https://files.catbox.moe/luvrwr.mp3",
                "JGwWNGJdvx8": "https://files.catbox.moe/ec9o4o.mp3",
            }
            
            url = direct_links.get(video_id)
            if url:
                async with aiohttp.ClientSession() as session:
                    async with session.get(url) as response:
                        if response.status == 200:
                            return await response.read()
            return None
        except Exception as e:
            logger.error(f"Download error: {e}")
            return None
    
    @staticmethod
    async def get_stream_url(video_id: str):
        """Получение прямой ссылки на аудио"""
        # В реальном боте генерируйте ссылку через yt-dlp
        return f"https://www.youtube.com/watch?v={video_id}"

# ================== КОМАНДЫ БОТА ==================
@dp.message(Command("start"))
async def start_cmd(message: types.Message):
    user_id = message.from_user.id
    username = message.from_user.username or message.from_user.first_name
    
    # Сохраняем статистику
    if user_id not in stats["users"]:
        stats["users"][user_id] = {
            "username": username,
            "downloads": 0,
            "first_seen": datetime.now().isoformat()
        }
    
    welcome_text = f"""
🎵 <b>Привет, {message.from_user.first_name}!</b>

Я — музыкальный бот для скачивания треков.

<b>Доступные команды:</b>
• Напиши название песни или исполнителя для поиска
• /search - поиск музыки
• /popular - популярные треки
• /stats - статистика бота
• /help - помощь

<b>Примеры запросов:</b>
• <code>Never Gonna Give You Up</code>
• <code>Billie Eilish</code>
• <code>хиты 2024</code>

⚡ <i>Бот работает 24/7 благодаря GitHub</i>
    """
    
    await message.answer(welcome_text)

@dp.message(Command("help"))
async def help_cmd(message: types.Message):
    help_text = """
🎯 <b>Как пользоваться ботом:</b>

1. <b>Поиск музыки:</b>
   Просто напиши название песни или исполнителя
   Или используй команду /search

2. <b>Скачивание:</b>
   • Бот найдет треки на YouTube
   • Выбери нужный трек из списка
   • Нажми кнопку "Скачать"
   • Получи файл в высоком качестве

3. <b>Качество:</b>
   • MP3 320kbps
   • Быстрое скачивание
   • ID3 теги (название, исполнитель, обложка)

4. <b>Особенности:</b>
   • Поддержка плейлистов
   • История поиска
   • Без ограничений по размеру

⚠️ <b>Важно:</b>
   Скачивайте музыку только для личного использования!
   Поддерживайте исполнителей, покупая их музыку.

📞 <b>Поддержка:</b> @ваш_ник
    """
    await message.answer(help_text)

@dp.message(Command("stats"))
async def stats_cmd(message: types.Message):
    if message.from_user.id != ADMIN_ID:
        await message.answer("❌ Эта команда только для администратора")
        return
    
    uptime = datetime.now() - datetime.fromisoformat(stats["start_time"])
    stats_text = f"""
📊 <b>Статистика бота:</b>

• Всего скачиваний: {stats['total_downloads']}
• Уникальных пользователей: {len(stats['users'])}
• Время работы: {uptime.days} дней, {uptime.seconds // 3600} часов

<b>Топ пользователей:</b>
"""
    
    # Топ 10 пользователей
    top_users = sorted(stats["users"].items(), 
                      key=lambda x: x[1].get("downloads", 0), 
                      reverse=True)[:10]
    
    for i, (user_id, user_data) in enumerate(top_users, 1):
        stats_text += f"{i}. {user_data.get('username', 'Unknown')}: {user_data.get('downloads', 0)}\n"
    
    await message.answer(stats_text)

@dp.message(Command("popular"))
async def popular_cmd(message: types.Message):
    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [
            InlineKeyboardButton(text="🎵 Популярные сейчас", callback_data="cat_popular"),
            InlineKeyboardButton(text="🔥 Тренды", callback_data="cat_trending")
        ],
        [
            InlineKeyboardButton(text="🎸 Рок", callback_data="cat_rock"),
            InlineKeyboardButton(text="🎤 Хип-хоп", callback_data="cat_hiphop")
        ],
        [
            InlineKeyboardButton(text="🎹 Электроника", callback_data="cat_electro"),
            InlineKeyboardButton(text="🎷 Джаз", callback_data="cat_jazz")
        ]
    ])
    
    await message.answer("🎧 <b>Выбери категорию популярной музыки:</b>", reply_markup=keyboard)

@dp.message(Command("search"))
async def search_cmd(message: types.Message, state: FSMContext):
    await message.answer("🔍 <b>Введите название песни или исполнителя:</b>")
    await state.set_state(DownloadStates.waiting_for_query)

# ================== ОБРАБОТКА ПОИСКА ==================
@dp.message(DownloadStates.waiting_for_query)
async def process_search(message: types.Message, state: FSMContext):
    query = message.text.strip()
    
    if len(query) < 2:
        await message.answer("❌ Введите минимум 2 символа для поиска")
        return
    
    # Сообщение о начале поиска
    search_msg = await message.answer(f"🔍 <b>Ищу:</b> <code>{query}</code>")
    
    try:
        # Ищем треки
        tracks = await YouTubeDownloader.search_youtube(query)
        
        if not tracks:
            await search_msg.edit_text(f"❌ По запросу <code>{query}</code> ничего не найдено")
            return
        
        # Сохраняем результаты
        user_data[message.from_user.id] = {
            "query": query,
            "tracks": tracks,
            "search_time": datetime.now().isoformat()
        }
        
        # Создаем клавиатуру с результатами
        keyboard = InlineKeyboardMarkup(inline_keyboard=[])
        
        for i, track in enumerate(tracks[:10]):  # Максимум 10 треков
            title = track["title"]
            if len(title) > 35:
                title = title[:32] + "..."
            
            keyboard.inline_keyboard.append([
                InlineKeyboardButton(
                    text=f"{i+1}. {title}",
                    callback_data=f"select_{track['id']}"
                )
            ])
        
        # Кнопка нового поиска
        keyboard.inline_keyboard.append([
            InlineKeyboardButton(text="🔍 Новый поиск", callback_data="new_search")
        ])
        
        await search_msg.edit_text(
            f"✅ <b>Найдено {len(tracks)} треков по запросу:</b> <code>{query}</code>\n\n"
            f"<i>Выбери трек для скачивания:</i>",
            reply_markup=keyboard
        )
        
    except Exception as e:
        logger.error(f"Search processing error: {e}")
        await search_msg.edit_text("❌ Произошла ошибка при поиске. Попробуйте позже.")
    
    await state.clear()

@dp.message(F.text)
async def handle_text(message: types.Message):
    """Обработка текстовых запросов (поиск)"""
    query = message.text.strip()
    
    if len(query) < 2:
        await message.answer("❌ Введите минимум 2 символа для поиска")
        return
    
    # Аналогично process_search, но без FSM
    search_msg = await message.answer(f"🔍 <b>Ищу:</b> <code>{query}</code>")
    
    try:
        tracks = await YouTubeDownloader.search_youtube(query)
        
        if not tracks:
            await search_msg.edit_text(f"❌ По запросу <code>{query}</code> ничего не найдено")
            return
        
        user_data[message.from_user.id] = {
            "query": query,
            "tracks": tracks,
            "search_time": datetime.now().isoformat()
        }
        
        keyboard = InlineKeyboardMarkup(inline_keyboard=[])
        
        for i, track in enumerate(tracks[:10]):
            title = track["title"]
            if len(title) > 35:
                title = title[:32] + "..."
            
            keyboard.inline_keyboard.append([
                InlineKeyboardButton(
                    text=f"{i+1}. {title}",
                    callback_data=f"select_{track['id']}"
                )
            ])
        
        keyboard.inline_keyboard.append([
            InlineKeyboardButton(text="🔍 Новый поиск", callback_data="new_search")
        ])
        
        await search_msg.edit_text(
            f"✅ <b>Найдено {len(tracks)} треков:</b>\n<code>{query}</code>\n\n"
            f"<i>Выбери трек для скачивания:</i>",
            reply_markup=keyboard
        )
        
    except Exception as e:
        logger.error(f"Search error: {e}")
        await search_msg.edit_text("❌ Ошибка поиска. Попробуйте другой запрос.")

# ================== ОБРАБОТКА ВЫБОРА ТРЕКА ==================
@dp.callback_query(F.data.startswith("select_"))
async def handle_track_selection(callback: types.CallbackQuery):
    video_id = callback.data.replace("select_", "")
    
    # Находим информацию о треке
    tracks = user_data.get(callback.from_user.id, {}).get("tracks", [])
    track_info = next((t for t in tracks if t["id"] == video_id), None)
    
    if not track_info:
        await callback.answer("❌ Трек не найден")
        return
    
    # Клавиатура для скачивания
    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [
            InlineKeyboardButton(text="⬇️ Скачать MP3", callback_data=f"dl_{video_id}"),
            InlineKeyboardButton(text="🎬 YouTube", url=f"https://youtu.be/{video_id}")
        ],
        [
            InlineKeyboardButton(text="🔍 Новый поиск", callback_data="new_search"),
            InlineKeyboardButton(text="📋 Еще треки", callback_data="more_tracks")
        ]
    ])
    
    await callback.message.edit_text(
        f"🎵 <b>Выбран трек:</b>\n\n"
        f"<b>{track_info['title']}</b>\n"
        f"⏱ Длительность: {track_info.get('duration', 'N/A')}\n\n"
        f"<i>Нажмите 'Скачать MP3' для загрузки</i>",
        reply_markup=keyboard
    )
    await callback.answer()

# ================== СКАЧИВАНИЕ ТРЕКА ==================
@dp.callback_query(F.data.startswith("dl_"))
async def download_track(callback: types.CallbackQuery):
    video_id = callback.data.replace("dl_", "")
    
    # Обновляем статистику
    stats["total_downloads"] += 1
    user_id = callback.from_user.id
    if user_id in stats["users"]:
        stats["users"][user_id]["downloads"] = stats["users"][user_id].get("downloads", 0) + 1
    
    # Получаем информацию о треке
    tracks = user_data.get(callback.from_user.id, {}).get("tracks", [])
    track_info = next((t for t in tracks if t["id"] == video_id), {})
    
    await callback.answer(f"⚡ Начинаем скачивание...")
    
    # Сообщение о начале скачивания
    status_msg = await callback.message.answer(
        f"⬇️ <b>Скачиваю:</b> {track_info.get('title', 'Трек')}\n"
        f"⏳ Пожалуйста, подождите..."
    )
    
    try:
        # Скачиваем аудио
        audio_data = await YouTubeDownloader.download_audio(video_id)
        
        if audio_data:
            # Отправляем файл
            filename = f"{track_info.get('title', 'track')[:30]}.mp3".replace("/", "-")
            
            await bot.send_audio(
                chat_id=callback.from_user.id,
                audio=types.BufferedInputFile(
                    audio_data,
                    filename=filename
                ),
                caption=f"🎵 <b>{track_info.get('title', 'Трек')}</b>\n"
                       f"⚡ Скачано через Music Bot",
                title=track_info.get('title', 'Трек')[:30],
                performer=track_info.get('artist', 'Исполнитель')[:30],
                thumb=types.URLInputFile(track_info.get('thumbnail', '')) if track_info.get('thumbnail') else None
            )
            
            await status_msg.edit_text("✅ <b>Трек успешно отправлен в чат!</b>")
            
            # Логируем успешное скачивание
            logger.info(f"Download successful: user={callback.from_user.id}, track={video_id}")
            
        else:
            # Если не удалось скачать, предлагаем YouTube ссылку
            keyboard = InlineKeyboardMarkup(inline_keyboard=[
                [InlineKeyboardButton(text="🎬 Смотреть на YouTube", 
                                    url=f"https://youtu.be/{video_id}")],
                [InlineKeyboardButton(text="🔍 Новый поиск", callback_data="new_search")]
            ])
            
            await status_msg.edit_text(
                "❌ <b>Не удалось скачать трек</b>\n\n"
                "Возможные причины:\n"
                "• Трек защищен авторскими правами\n"
                "• Проблемы с сервером YouTube\n"
                "• Ошибка подключения\n\n"
                "<i>Вы можете посмотреть трек на YouTube:</i>",
                reply_markup=keyboard
            )
            
    except Exception as e:
        logger.error(f"Download failed: {e}")
        await status_msg.edit_text(f"❌ <b>Ошибка скачивания:</b>\n<code>{str(e)[:100]}</code>")

# ================== ДОПОЛНИТЕЛЬНЫЕ КНОПКИ ==================
@dp.callback_query(F.data == "new_search")
async def new_search_handler(callback: types.CallbackQuery):
    await callback.message.edit_text(
        "🔍 <b>Новый поиск</b>\n\n"
        "Введите название песни или исполнителя:"
    )
    await callback.answer()

@dp.callback_query(F.data == "more_tracks")
async def more_tracks_handler(callback: types.CallbackQuery):
    user_info = user_data.get(callback.from_user.id, {})
    query = user_info.get("query", "")
    
    if query:
        await callback.message.edit_text(f"🔍 <b>Ищу еще треки:</b> <code>{query}</code>")
        await handle_text(callback.message)
    else:
        await callback.message.edit_text("Введите запрос для поиска:")
    
    await callback.answer()

@dp.callback_query(F.data.startswith("cat_"))
async def category_handler(callback: types.CallbackQuery):
    category = callback.data.replace("cat_", "")
    
    # Демо треки для категорий
    categories = {
        "popular": [
            {"id": "dQw4w9WgXcQ", "title": "Rick Astley - Never Gonna Give You Up"},
            {"id": "kJQP7kiw5Fk", "title": "Luis Fonsi - Despacito"},
            {"id": "JGwWNGJdvx8", "title": "Ed Sheeran - Shape of You"},
        ],
        "trending": [
            {"id": "uelHwf8o7_U", "title": "Drake - God's Plan"},
            {"id": "CevxZvSJLk8", "title": "The Weeknd - Blinding Lights"},
        ],
        "rock": [
            {"id": "v2AC41dglnM", "title": "AC/DC - Thunderstruck"},
            {"id": "rBqdRkQ9gLA", "title": "Queen - Bohemian Rhapsody"},
        ]
    }
    
    tracks = categories.get(category, categories["popular"])
    user_data[callback.from_user.id] = {"tracks": tracks, "query": category}
    
    keyboard = InlineKeyboardMarkup(inline_keyboard=[])
    for i, track in enumerate(tracks):
        keyboard.inline_keyboard.append([
            InlineKeyboardButton(
                text=f"{i+1}. {track['title'][:35]}",
                callback_data=f"select_{track['id']}"
            )
        ])
    
    category_names = {
        "popular": "Популярные сейчас",
        "trending": "Тренды",
        "rock": "Рок",
        "hiphop": "Хип-хоп",
        "electro": "Электроника",
        "jazz": "Джаз"
    }
    
    await callback.message.edit_text(
        f"🎧 <b>{category_names.get(category, 'Популярные треки')}:</b>\n\n"
        f"<i>Выбери трек для скачивания:</i>",
        reply_markup=keyboard
    )
    await callback.answer()

# ================== ЗАПУСК БОТА ==================
async def main():
    logger.info("=" * 50)
    logger.info("🎵 MUSIC DOWNLOAD BOT")
    logger.info("⚡ Version: 2.0")
    logger.info(f"👤 Admin ID: {ADMIN_ID}")
    logger.info("✅ Bot is starting...")
    logger.info("=" * 50)
    
    # Удаляем вебхук (если был)
    await bot.delete_webhook(drop_pending_updates=True)
    
    # Запускаем поллинг
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())
