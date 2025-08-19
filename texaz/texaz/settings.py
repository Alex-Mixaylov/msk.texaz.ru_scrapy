# Scrapy settings for texaz project

BOT_NAME = "texaz"

SPIDER_MODULES = ["texaz.spiders"]
NEWSPIDER_MODULE = "texaz.spiders"

# --- Вежливость и соответствие сайту ---
ROBOTSTXT_OBEY = False           # оставляем True; переключите на False, если robots.txt блокирует раздел
DOWNLOAD_DELAY = 1.0            # базовая задержка между запросами
CONCURRENT_REQUESTS_PER_DOMAIN = 1  # не агрессируем

# Автотюнинг скорости (плавно реагирует на нагрузку/задержки)
AUTOTHROTTLE_ENABLED = True
AUTOTHROTTLE_START_DELAY = 1.0
AUTOTHROTTLE_MAX_DELAY = 5.0
AUTOTHROTTLE_TARGET_CONCURRENCY = 1.0
AUTOTHROTTLE_DEBUG = False

# Заголовки по умолчанию (адекватный UA и локаль)
DEFAULT_REQUEST_HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/124.0 Safari/537.36"
    ),
    "Accept-Language": "ru,en;q=0.9",
}

# Экспорт (корректная кодировка для CSV/JSON/XLSX-пайплайна)
FEED_EXPORT_ENCODING = "utf-8"

# Уровень логов при необходимости:
LOG_LEVEL = "INFO"

# Сохранить в XLSX через pipeline — раскомментируйте и пропишите свой класс:
ITEM_PIPELINES = {
    "texaz.pipelines.ExcelExportPipeline": 300,
}


