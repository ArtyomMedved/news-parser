import feedparser
import re
from telegram import Bot
from telegram.ext import Application, CommandHandler
import logging
import os

# Токен вашего бота
TOKEN = 'TOKEN'
CHAT_ID = '@HackAndTrend'  # Ваш канал (или ID чата)

# URL RSS-канала
rss_url = "https://habr.com/ru/rss/flows/develop/news/?fl=ru"

# Путь к файлу для хранения отправленных ссылок
SENT_POSTS_FILE = "sent_posts.txt"

# Настройка логирования для отслеживания ошибок
logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
                    level=logging.INFO)
logger = logging.getLogger(__name__)

def get_sent_posts():
    """Загружаем список отправленных постов из файла."""
    if os.path.exists(SENT_POSTS_FILE):
        with open(SENT_POSTS_FILE, 'r') as file:
            return set(file.read().splitlines())
    return set()

def mark_as_sent(post_url):
    """Сохраняем ссылку на отправленный пост в файл."""
    with open(SENT_POSTS_FILE, 'a') as file:
        file.write(post_url + '\n')

def get_news():
    """Получаем новости из RSS-канала."""
    feed = feedparser.parse(rss_url)
    news_list = []

    if feed.bozo == 0:
        logger.info(f"RSS успешно загружен с URL: {rss_url}")
        for entry in feed.entries[:8]:  # Пример: последние 5 новостей
            title = entry.title
            link = entry.link
            description = entry.description
            description_clean = re.sub(r'<[^>]*>', '', description)  # Удаляем HTML-теги
            
            # Извлечение изображения из тега <img src="...">
            img_url = None
            img_match = re.search(r'<img[^>]*src="([^"]+)"', description)
            if img_match:
                img_url = img_match.group(1)

            # Собираем информацию о новости
            news_list.append({
                'title': title,
                'link': link,
                'description': description_clean,
                'img_url': img_url
            })
    
    if not news_list:
        logger.warning("Новости не были найдены в RSS.")
    return news_list

async def post_news(context):
    """Отправляем новости в канал Telegram, проверяя на дублирование."""
    sent_posts = get_sent_posts()  # Получаем уже отправленные посты
    news_list = get_news()

    if not news_list:
        logger.info("Нет новостей для отправки.")
        return
    
    logger.info(f"Отправка {len(news_list)} новостей в канал {CHAT_ID}.")
    
    for news in news_list:
        # Проверка, отправлялась ли уже эта новость
        if news['link'] in sent_posts:
            logger.info(f"Новость уже была отправлена: {news['title']}")
            continue

        # Форматируем сообщение
        title = f"<b>{news['title']}</b>"  # Заголовок жирным
        # Описание в цитате
        description = f"<blockquote>{news['description'][:300]}...</blockquote>" if len(news['description']) > 300 else f"<blockquote>{news['description']}</blockquote>"
        read_more = f"<a href=\"{news['link']}\">Подробнее</a>"

        # Формирование окончательного сообщения
        message = f"{title}\n\n{description}\n\n{read_more}"
        logger.info(f"Отправка новости: {news['title']}")

        # Отправляем сообщение
        if news['img_url']:
            caption = message[:1024]  # Обрезаем сообщение до 1024 символов
            await context.bot.send_photo(chat_id=CHAT_ID, photo=news['img_url'], caption=caption, parse_mode="HTML")
        else:
            # Если нет изображения, отправляем только текст
            await context.bot.send_message(chat_id=CHAT_ID, text=message, parse_mode="HTML")

        # Помечаем новость как отправленную
        mark_as_sent(news['link'])

async def start(update, context):
    await update.message.reply_text("Бот запущен!")

def main():
    """Основная функция для запуска бота."""
    # Инициализация приложения
    application = Application.builder().token(TOKEN).build()
    
    # Команда /start
    application.add_handler(CommandHandler("start", start))
    
    # Каждые 10 минут постим новости
    job_queue = application.job_queue
    job_queue.run_repeating(post_news, interval=60, first=1)  # Каждые 60 секунд (1 минута)
    
    # Запуск бота
    application.run_polling()

if __name__ == '__main__':
    main()
