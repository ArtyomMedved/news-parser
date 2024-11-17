import feedparser
import re

# URL RSS-канала
rss_url = "https://habr.com/ru/rss/news/?fl=ru"

# Получение данных из RSS-канала
feed = feedparser.parse(rss_url)

# Проверка, удалось ли загрузить канал
if feed.bozo == 0:
    print(f"Новости с {feed.feed.title}:\n")
    
    # Вывод первых 5 новостей
    for entry in feed.entries[:5]:
        # Заголовок новости
        title = entry.title
        
        # Ссылка на полную статью
        link = entry.link
        
        # Описание новости (с удалением лишних тегов HTML)
        description = entry.description
        description_clean = re.sub(r'<[^>]*>', '', description)  # Удаляет HTML-теги

        # Дата публикации
        pub_date = entry.published
        
        # Извлечение изображения из тега <img src="...">
        img_url = None
        img_match = re.search(r'<img[^>]*src="([^"]+)"', description)
        if img_match:
            img_url = img_match.group(1)

        # Вывод новости
        print(f"Заголовок: {title}")
        print(f"Ссылка: {link}")
        print(f"Описание: {description_clean}")
        if img_url:
            print(f"Изображение: {img_url}")
        print(f"Дата: {pub_date}\n")
else:
    print("Ошибка при загрузке RSS-канала")
