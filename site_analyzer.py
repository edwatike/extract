import asyncio
import json
import os
from urllib.parse import urlparse
from bs4 import BeautifulSoup
from playwright.async_api import async_playwright
from loguru import logger
from dotenv import load_dotenv
from datetime import datetime

# Загрузка переменных окружения
load_dotenv()

# Настройка путей для сохранения данных
DATA_DIR = "data"
HTML_DIR = os.path.join(DATA_DIR, "html")
TXT_DIR = os.path.join(DATA_DIR, "txt")
JSON_DIR = os.path.join(DATA_DIR, "json")
LOGS_DIR = os.path.join(DATA_DIR, "logs")

# JavaScript для обхода защиты от ботов
STEALTH_JS = """
Object.defineProperty(navigator, 'webdriver', {
    get: () => undefined
});
"""

class DeepSiteAnalyzer:
    def __init__(self, proxy=None):
        self.proxy = proxy or os.getenv('PROXY')
        self.browser = None
        self.context = None
        self._ensure_directories()
        self._setup_logger()
        
    def _ensure_directories(self):
        """Создает необходимые директории, если они не существуют"""
        for directory in [HTML_DIR, TXT_DIR, JSON_DIR, LOGS_DIR]:
            os.makedirs(directory, exist_ok=True)
            
    def _setup_logger(self):
        """Настраивает логирование"""
        log_file = os.path.join(LOGS_DIR, f"analyzer_{datetime.now().strftime('%Y%m%d_%H%M%S')}.log")
        logger.add(log_file, rotation="100 MB", retention="30 days")
        
    async def __aenter__(self):
        playwright = await async_playwright().start()
        self.browser = await playwright.chromium.launch(
            headless=True,
            args=[
                '--disable-blink-features=AutomationControlled',
                '--disable-dev-shm-usage',
                '--no-sandbox',
                '--disable-setuid-sandbox',
                '--disable-gpu',
                '--disable-web-security',
                '--disable-features=IsolateOrigins,site-per-process'
            ]
        )
        
        # Настройка контекста браузера
        self.context = await self.browser.new_context(
            locale='ru-RU',
            timezone_id='Europe/Moscow',
            geolocation={'latitude': 55.7558, 'longitude': 37.6173},
            proxy=self.proxy if self.proxy else None,
            viewport={'width': 1920, 'height': 1080},
            user_agent='Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/123.0.0.0 Safari/537.36'
        )
        
        # Добавление скрипта для обхода защиты
        await self.context.add_init_script(STEALTH_JS)
        
        return self
        
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        if self.browser:
            await self.browser.close()
            
    def _get_domain(self, url: str) -> str:
        """Извлекает домен из URL"""
        return urlparse(url).netloc
        
    def _get_timestamp(self) -> str:
        """Возвращает текущую метку времени"""
        return datetime.now().strftime("%Y%m%d_%H%M%S")
        
    def _get_file_path(self, domain: str, ext: str, timestamp: str = None) -> str:
        """Генерирует путь к файлу на основе домена и расширения"""
        filename = f"{domain}_{timestamp}.{ext}" if timestamp else f"{domain}.{ext}"
        if ext == 'html':
            return os.path.join(HTML_DIR, filename)
        elif ext == 'txt':
            return os.path.join(TXT_DIR, filename)
        elif ext == 'json':
            return os.path.join(JSON_DIR, filename)
        raise ValueError(f"Неподдерживаемое расширение файла: {ext}")
        
    async def analyze_site(self, url: str) -> dict:
        """
        Анализирует сайт и извлекает необходимую информацию
        """
        try:
            page = await self.context.new_page()
            
            # Увеличенное время ожидания и дополнительные настройки
            await page.goto(url, 
                          wait_until='networkidle', 
                          timeout=60000)  # Увеличиваем таймаут до 60 секунд
            
            # Ждем, пока страница действительно загрузится
            await page.wait_for_load_state('networkidle', timeout=60000)
            await page.wait_for_load_state('domcontentloaded', timeout=60000)
            
            # Прокручиваем страницу, чтобы загрузить динамический контент
            await page.evaluate('window.scrollTo(0, document.body.scrollHeight)')
            await asyncio.sleep(2)  # Даем время на загрузку динамического контента
            
            # Получение HTML
            html = await page.content()
            
            # Парсинг с помощью BeautifulSoup
            soup = BeautifulSoup(html, 'html.parser')
            
            # Извлечение заголовка
            title = soup.title.string if soup.title else ''
            
            # Извлечение текста
            clean_text = soup.get_text(separator=' ', strip=True)
            
            # Извлечение ссылок
            links = [a.get('href') for a in soup.find_all('a', href=True)]
            
            # Формирование результата
            result = {
                'url': url,
                'title': title,
                'html': html,
                'clean_text': clean_text,
                'links': links,
                'timestamp': self._get_timestamp()
            }
            
            # Сохранение результатов
            domain = self._get_domain(url)
            await self._save_results(domain, result)
            
            logger.info(f"Успешно проанализирован сайт: {url}")
            return result
            
        except Exception as e:
            error_msg = f"Ошибка при анализе {url}: {str(e)}"
            logger.error(error_msg)
            error_file = os.path.join(LOGS_DIR, "errors.log")
            with open(error_file, 'a', encoding='utf-8') as f:
                f.write(f"{self._get_timestamp()} - {error_msg}\n")
            return None
            
    async def _save_results(self, domain: str, data: dict):
        """Сохраняет результаты анализа в файлы"""
        timestamp = data['timestamp']
        
        # Сохранение HTML
        html_path = self._get_file_path(domain, 'html', timestamp)
        with open(html_path, 'w', encoding='utf-8') as f:
            f.write(data['html'])
            
        # Сохранение очищенного текста
        txt_path = self._get_file_path(domain, 'txt', timestamp)
        with open(txt_path, 'w', encoding='utf-8') as f:
            f.write(data['clean_text'])
            
        # Сохранение метаданных
        metadata = {
            'url': data['url'],
            'title': data['title'],
            'links': data['links'],
            'timestamp': timestamp,
            'files': {
                'html': html_path,
                'txt': txt_path
            }
        }
        json_path = self._get_file_path(domain, 'json', timestamp)
        with open(json_path, 'w', encoding='utf-8') as f:
            json.dump(metadata, f, ensure_ascii=False, indent=2)

async def main():
    # Чтение списка URL из файла
    with open('sites.txt', 'r', encoding='utf-8') as f:
        urls = [line.strip() for line in f if line.strip()]
    
    async with DeepSiteAnalyzer() as analyzer:
        tasks = [analyzer.analyze_site(url) for url in urls]
        await asyncio.gather(*tasks)

if __name__ == "__main__":
    asyncio.run(main()) 