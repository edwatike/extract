import asyncio
import logging
from playwright.async_api import async_playwright, Browser, Page, Request, Response, BrowserContext, Playwright
import json
import time
from typing import Dict, List, Optional, Set
import random
from urllib.parse import urljoin, urlparse
import re
from dataclasses import dataclass
from enum import Enum
import aiohttp
import hashlib
import os
from datetime import datetime

class ProtectionType(Enum):
    CLOUDFLARE = "cloudflare"
    RECAPTCHA = "recaptcha"
    HCAPTCHA = "hcaptcha"
    JAVASCRIPT = "javascript"
    COOKIE = "cookie"
    IP_BASED = "ip_based"
    USER_AGENT = "user_agent"
    UNKNOWN = "unknown"

@dataclass
class SiteConfig:
    """Конфигурация для конкретного сайта"""
    selectors: List[str]
    wait_time: int
    scroll_required: bool
    protection_types: List[ProtectionType]
    custom_headers: Dict[str, str]
    exclude_patterns: List[str]
    dynamic_load_selectors: List[str]

class EnhancedAntiBotBypass:
    """Расширенный класс для обхода анти-бот защиты"""
    
    def __init__(self):
        self.logger = logging.getLogger(__name__)
        self.user_agents = [
            'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36',
            'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/121.0.0.0 Safari/537.36',
            'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36',
            'Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:123.0) Gecko/20100101 Firefox/123.0'
        ]
        self.proxy_list = []  # Список прокси будет загружаться динамически
        
    async def detect_protection(self, page: Page) -> List[ProtectionType]:
        """Определение типа защиты на сайте"""
        protections = []
        
        # Проверка Cloudflare
        if await page.query_selector("iframe[title*='challenge']"):
            protections.append(ProtectionType.CLOUDFLARE)
            
        # Проверка reCAPTCHA
        if await page.query_selector("iframe[src*='recaptcha']"):
            protections.append(ProtectionType.RECAPTCHA)
            
        # Проверка hCaptcha
        if await page.query_selector("iframe[src*='hcaptcha']"):
            protections.append(ProtectionType.HCAPTCHA)
            
        # Проверка JavaScript защиты
        js_checks = await page.evaluate("""() => {
            return {
                hasBotDetection: !!window._botDetection,
                hasAntiBot: !!window._antiBot,
                hasProtection: !!window._protection
            }
        }""")
        if any(js_checks.values()):
            protections.append(ProtectionType.JAVASCRIPT)
            
        # Проверка cookie защиты
        cookies = await page.context.cookies()
        if any('cf_' in cookie.get('name', '') for cookie in cookies):
            protections.append(ProtectionType.COOKIE)
            
        return protections or [ProtectionType.UNKNOWN]
        
    async def bypass_cloudflare(self, page: Page) -> bool:
        """Обход Cloudflare защиты"""
        try:
            # Ждем появления challenge
            challenge_frame = await page.wait_for_selector("iframe[title*='challenge']", timeout=5000)
            if challenge_frame:
                # Эмулируем человеческое поведение
                await page.mouse.move(random.randint(100, 700), random.randint(100, 700))
                await page.wait_for_timeout(random.randint(2000, 4000))
                
                # Ждем исчезновения challenge
                try:
                    await page.wait_for_selector("iframe[title*='challenge']", state="detached", timeout=30000)
                    return True
                except:
                    return False
            return True
        except Exception as e:
            self.logger.error(f"Error bypassing Cloudflare: {str(e)}")
            return False
            
    async def bypass_recaptcha(self, page: Page) -> bool:
        """Обход reCAPTCHA"""
        try:
            recaptcha_frame = await page.wait_for_selector("iframe[src*='recaptcha']", timeout=5000)
            if recaptcha_frame:
                # Здесь можно добавить логику обхода reCAPTCHA
                # Например, использование сервиса решения капчи
                await page.wait_for_timeout(10000)
                return True
            return True
        except Exception as e:
            self.logger.error(f"Error bypassing reCAPTCHA: {str(e)}")
            return False
            
    async def setup_browser_context(self, context) -> None:
        """Настройка контекста браузера"""
        await context.add_init_script("""
            Object.defineProperty(navigator, 'webdriver', {get: () => undefined});
            Object.defineProperty(navigator, 'plugins', {get: () => [1, 2, 3, 4, 5]});
            
            // Эмуляция WebGL
            const getParameter = WebGLRenderingContext.prototype.getParameter;
            WebGLRenderingContext.prototype.getParameter = function(parameter) {
                if (parameter === 37445) {
                    return 'Intel Open Source Technology Center';
                }
                if (parameter === 37446) {
                    return 'Mesa DRI Intel(R) HD Graphics (SKL GT2)';
                }
                return getParameter.apply(this, arguments);
            };
        """)
        
    async def rotate_user_agent(self, context) -> None:
        """Ротация User-Agent"""
        user_agent = random.choice(self.user_agents)
        await context.set_extra_http_headers({
            'User-Agent': user_agent,
            'Accept-Language': 'ru-RU,ru;q=0.9,en-US;q=0.8,en;q=0.7',
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
            'DNT': '1',
            'Upgrade-Insecure-Requests': '1'
        })

class EnhancedSiteAnalyzer:
    """Улучшенный анализатор сайтов"""
    
    def __init__(self, verbose: bool = False):
        """Инициализация анализатора сайтов"""
        self.verbose = verbose
        self.browser: Optional[Browser] = None
        self.context: Optional[BrowserContext] = None
        self.page: Optional[Page] = None
        self.playwright: Optional[Playwright] = None
        self.request_log: List[Dict] = []
        self.anti_bot = EnhancedAntiBotBypass()
        self.site_configs: Dict[str, SiteConfig] = {}
        self.cache_dir = "cache"
        os.makedirs(self.cache_dir, exist_ok=True)
        
        # Настройка логирования
        log_level = logging.DEBUG if verbose else logging.INFO
        logging.basicConfig(
            level=log_level,
            format='%(asctime)s - %(levelname)s - %(message)s'
        )
        self.logger = logging.getLogger(__name__)
        
    async def init_browser(self):
        """Инициализация браузера"""
        try:
            if not self.playwright:
                self.logger.debug("Starting playwright")
                self.playwright = await async_playwright().start()
                
                self.logger.debug("Launching browser")
                self.browser = await self.playwright.chromium.launch(
                    headless=True,
                    args=['--no-sandbox', '--disable-setuid-sandbox']
                )
                
                self.logger.debug("Creating browser context")
                self.context = await self.browser.new_context(
                    viewport={'width': 1920, 'height': 1080},
                    user_agent='Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
                )
                self.logger.debug("Browser initialization completed")
        except Exception as e:
            self.logger.error(f"Error initializing browser: {str(e)}")
            if self.context:
                await self.context.close()
            if self.browser:
                await self.browser.close()
            if self.playwright:
                await self.playwright.stop()
            raise

    async def create_page(self, url: str) -> Optional[Page]:
        """Создание страницы с настройками"""
        try:
            self.logger.debug(f"Creating page for {url}")
            await self.init_browser()
            
            if not self.context:
                raise Exception("Browser context not initialized")
            
            page = await self.context.new_page()
            if not page:
                raise Exception("Failed to create page")
                
            self.logger.debug("Page created successfully")
            
            # Настройка таймаутов
            self.logger.debug("Setting page timeouts")
            page.set_default_navigation_timeout(60000)  # Увеличиваем таймаут навигации до 60 секунд
            page.set_default_timeout(60000)  # Увеличиваем общий таймаут до 60 секунд
            
            # Обработка запросов
            self.logger.debug("Setting up request handling")
            async def handle_request(request):
                self.request_log.append({
                    'url': request.url,
                    'method': request.method,
                    'timestamp': datetime.now().isoformat()
                })
            
            page.on('request', handle_request)
            
            # Настройка перехватчиков JavaScript
            self.logger.debug("Adding JavaScript interceptors")
            await page.add_init_script("""
                // Перехват проверок на бота
                Object.defineProperty(navigator, 'webdriver', {
                    get: () => false,
                });
                
                // Эмуляция событий мыши
                window.addEventListener('load', () => {
                    const event = new MouseEvent('mousemove', {
                        'view': window,
                        'bubbles': true,
                        'cancelable': true,
                        'clientX': Math.random() * window.innerWidth,
                        'clientY': Math.random() * window.innerHeight
                    });
                    document.dispatchEvent(event);
                });
            """)
            
            self.logger.debug("Page setup completed")
            return page
            
        except Exception as e:
            self.logger.error(f"Error creating page: {str(e)}")
            return None

    async def bypass_antibot(self, page: Page) -> bool:
        """Обход защиты от ботов"""
        try:
            self.logger.debug("Attempting to bypass antibot protection")
            
            # Установка дополнительных заголовков
            await page.set_extra_http_headers({
                'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
                'Accept-Language': 'ru-RU,ru;q=0.8,en-US;q=0.5,en;q=0.3',
                'Cache-Control': 'no-cache',
                'Pragma': 'no-cache',
                'Upgrade-Insecure-Requests': '1'
            })
            
            # Эмуляция действий пользователя
            await page.mouse.move(50, 50)
            await page.wait_for_timeout(500)
            await page.mouse.move(100, 100)
            await page.wait_for_timeout(300)
            await page.mouse.wheel(delta_x=0, delta_y=50)
            await page.wait_for_timeout(200)
            await page.mouse.wheel(delta_x=0, delta_y=-30)
            
            # Ожидание загрузки контента
            await page.wait_for_timeout(2000)
            
            # Проверка на наличие защиты
            has_antibot = await page.evaluate("""() => {
                return !!(
                    document.querySelector('[class*="antibot"]') ||
                    document.querySelector('[id*="antibot"]') ||
                    document.querySelector('script[src*="antibot"]')
                );
            }""")
            
            if has_antibot:
                self.logger.warning("Antibot protection detected")
                
                # Дополнительные действия для обхода защиты
                await page.evaluate("""() => {
                    // Удаление скриптов антибота
                    document.querySelectorAll('script[src*="antibot"]').forEach(script => script.remove());
                    
                    // Эмуляция событий клавиатуры
                    document.dispatchEvent(new KeyboardEvent('keydown', { key: 'Tab' }));
                    document.dispatchEvent(new KeyboardEvent('keyup', { key: 'Tab' }));
                    
                    // Эмуляция фокуса
                    document.body.focus();
                    
                    // Очистка localStorage и sessionStorage
                    localStorage.clear();
                    sessionStorage.clear();
                }""")
                
                # Перезагрузка страницы
                await page.reload(wait_until="networkidle")
                await page.wait_for_timeout(3000)
                
                # Повторная проверка
                has_antibot = await page.evaluate("""() => {
                    return !!(
                        document.querySelector('[class*="antibot"]') ||
                        document.querySelector('[id*="antibot"]') ||
                        document.querySelector('script[src*="antibot"]')
                    );
                }""")
                
                if has_antibot:
                    self.logger.error("Failed to bypass antibot protection")
                    return False
                    
            self.logger.debug("Antibot protection bypassed successfully")
            return True
            
        except Exception as e:
            self.logger.error(f"Error bypassing antibot protection: {str(e)}")
            return False

    async def analyze_site(self, url: str) -> Dict:
        """Анализ сайта"""
        page = None
        try:
            self.logger.info(f"Starting analysis of {url}")
            
            # Создание страницы
            page = await self.create_page(url)
            
            if not page:
                raise Exception("Failed to create page")
            
            # Переход на страницу с дополнительным ожиданием
            self.logger.debug(f"Navigating to {url}")
            response = await page.goto(url, wait_until="networkidle", timeout=60000)
            
            if not response:
                raise Exception("Failed to load page")
                
            if response.status != 200:
                raise Exception(f"Page returned status code {response.status}")
            
            # Обход защиты от ботов
            if not await self.bypass_antibot(page):
                raise Exception("Failed to bypass antibot protection")
            
            # Эмуляция действий пользователя
            self.logger.debug("Emulating user actions")
            await page.mouse.move(100, 100)
            await page.mouse.wheel(delta_x=0, delta_y=100)
            
            # Ожидание появления основного контента
            try:
                self.logger.debug("Waiting for main content")
                await page.wait_for_selector('body', timeout=10000)
                
                # Проверяем наличие основного контента
                content_selectors = ['.main-content', '#content', 'main', '.content', '#main']
                for selector in content_selectors:
                    try:
                        await page.wait_for_selector(selector, timeout=5000)
                        self.logger.debug(f"Found content selector: {selector}")
                        break
                    except:
                        continue
                        
            except Exception as e:
                self.logger.warning(f"Content selectors not found: {str(e)}")
            
            # Анализ страницы
            self.logger.debug("Analyzing page structure")
            structure = await self.analyze_site_structure(page)
            
            self.logger.debug("Extracting categories")
            categories = await self.extract_categories(page)
            
            self.logger.debug("Extracting products")
            products = await self.extract_products(page)
            
            self.logger.debug("Extracting links")
            links = await self.extract_links(page)
            
            results = {
                'url': url,
                'title': await page.title(),
                'structure': structure,
                'categories': categories,
                'products': products,
                'links': links,
                'request_log': self.request_log,
                'timestamp': datetime.now().isoformat()
            }
            
            self.logger.debug("Analysis completed successfully")
            return results
            
        except Exception as e:
            self.logger.error(f"Error analyzing site {url}: {str(e)}")
            raise
            
        finally:
            if page:
                self.logger.debug("Closing page")
                await page.close()

    async def analyze_site_structure(self, page: Page) -> Dict:
        """Анализ структуры сайта для определения основных элементов"""
        try:
            structure = await page.evaluate("""() => {
                const structure = {
                    navigation: [],
                    mainContent: null,
                    sidebar: null,
                    footer: null,
                    forms: [],
                    scripts: [],
                    styles: []
                };
                
                // Анализ навигации
                document.querySelectorAll('nav, [role="navigation"], [class*="nav"], [class*="menu"]').forEach(nav => {
                    const links = Array.from(nav.querySelectorAll('a')).map(a => ({
                        text: a.textContent.trim(),
                        href: a.href,
                        isActive: a.classList.contains('active') || a.getAttribute('aria-current') === 'page'
                    }));
                    if (links.length > 0) {
                        structure.navigation.push({
                            type: nav.tagName.toLowerCase(),
                            className: nav.className,
                            links: links
                        });
                    }
                });
                
                // Определение основного контента
                const mainContent = document.querySelector('main, [role="main"], #content, .content, [class*="content"]');
                if (mainContent) {
                    structure.mainContent = {
                        type: mainContent.tagName.toLowerCase(),
                        className: mainContent.className,
                        children: Array.from(mainContent.children).map(child => ({
                            type: child.tagName.toLowerCase(),
                            className: child.className
                        }))
                    };
                }
                
                // Анализ сайдбара
                const sidebar = document.querySelector('aside, [role="complementary"], .sidebar, [class*="sidebar"]');
                if (sidebar) {
                    structure.sidebar = {
                        type: sidebar.tagName.toLowerCase(),
                        className: sidebar.className,
                        children: Array.from(sidebar.children).map(child => ({
                            type: child.tagName.toLowerCase(),
                            className: child.className
                        }))
                    };
                }
                
                // Анализ футера
                const footer = document.querySelector('footer, [role="contentinfo"], .footer, [class*="footer"]');
                if (footer) {
                    structure.footer = {
                        type: footer.tagName.toLowerCase(),
                        className: footer.className,
                        children: Array.from(footer.children).map(child => ({
                            type: child.tagName.toLowerCase(),
                            className: child.className
                        }))
                    };
                }
                
                // Анализ форм
                document.querySelectorAll('form').forEach(form => {
                    structure.forms.push({
                        action: form.action,
                        method: form.method,
                        className: form.className,
                        inputs: Array.from(form.querySelectorAll('input, select, textarea')).map(input => ({
                            type: input.type || input.tagName.toLowerCase(),
                            name: input.name,
                            className: input.className
                        }))
                    });
                });
                
                // Анализ скриптов и стилей
                document.querySelectorAll('script[src]').forEach(script => {
                    structure.scripts.push(script.src);
                });
                
                document.querySelectorAll('link[rel="stylesheet"]').forEach(style => {
                    structure.styles.push(style.href);
                });
                
                return structure;
            }""")
            
            return structure
            
        except Exception as e:
            self.logger.error(f"Error analyzing site structure: {str(e)}")
            return {}
            
    async def cleanup(self):
        """Очистка ресурсов"""
        if self.browser:
            await self.browser.close()
        if self.playwright:
            await self.playwright.stop()

    async def __aenter__(self):
        self.logger.debug("Entering context manager")
        await self.init_browser()
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        self.logger.debug("Exiting context manager")
        if self.context:
            await self.context.close()
        if self.browser:
            await self.browser.close()
        if self.playwright:
            await self.playwright.stop()

    async def extract_categories(self, page: Page) -> List[Dict[str, str]]:
        """Извлечение категорий со страницы"""
        categories = []
        
        # Ждем загрузки элементов меню
        await page.wait_for_timeout(5000)  # Увеличенный таймаут для динамического контента
        
        # Список селекторов для извлечения категорий
        selectors = [
            ".menu-menu1 a",  # Основные пункты меню
            ".menu-menu2 a",  # Подпункты меню
            ".cats-wrap .item a",  # Карточки категорий товаров
            ".big-menu a",  # Большое меню
            "nav[id^='nav'] a",  # Элементы навигации
            ".catalog-menu a",  # Меню каталога
            "#menu a",  # Элементы меню
            ".categories a",  # Общие категории
            ".product-categories a",  # Категории товаров
            ".sidebar a",  # Сайдбар
            ".category-list a",  # Список категорий
            ".catalog a",  # Каталог
            ".menu a",  # Меню
            ".nav a",  # Навигация
            "[class*='category'] a",  # Любые элементы с 'category' в классе
            "[class*='catalog'] a"  # Любые элементы с 'catalog' в классе
        ]
        
        # Пробуем каждый селектор
        for selector in selectors:
            try:
                elements = await page.query_selector_all(selector)
                for element in elements:
                    try:
                        href = await element.get_attribute('href')
                        if href and not href.startswith('#') and not href.startswith('javascript:'):
                            name = await element.text_content()
                            name = name.strip() if name else ''
                            if name and href:
                                # Преобразуем относительные URL в абсолютные
                                if not href.startswith('http'):
                                    base_url = page.url
                                    href = urljoin(base_url, href)
                                
                                # Добавляем в категории, если еще нет
                                category = {'name': name, 'url': href}
                                if category not in categories:
                                    categories.append(category)
                    except Exception as e:
                        self.logger.debug(f"Error extracting category details: {str(e)}")
            except Exception as e:
                self.logger.debug(f"Error with selector {selector}: {str(e)}")
                continue
        
        # Удаляем дубликаты, сохраняя порядок
        seen = set()
        unique_categories = []
        for cat in categories:
            cat_tuple = (cat['name'], cat['url'])
            if cat_tuple not in seen:
                seen.add(cat_tuple)
                unique_categories.append(cat)
        
        # Фильтруем не-категории
        filtered_categories = []
        exclude_patterns = [
            '/about/', '/contacts/', '/feedback/', '/user/',
            'javascript:', '#', 'tel:', 'mailto:',
            '/docs/', '/transportation/', '/service/',
            '/news/', '/blog/', '/articles/',
            '/delivery/', '/payment/', '/warranty/'
        ]
        
        for cat in unique_categories:
            if not any(pattern in cat['url'].lower() for pattern in exclude_patterns):
                if cat['name'].strip() and len(cat['name'].strip()) > 1:  # Проверяем, что имя не пустое и не слишком короткое
                    filtered_categories.append(cat)
        
        return filtered_categories

    async def extract_products(self, page: Page) -> List[Dict]:
        """Извлечение информации о товарах со страницы"""
        products = []
        
        # Ждем загрузки элементов товаров
        await page.wait_for_timeout(5000)
        
        # Список селекторов для извлечения товаров
        selectors = [
            ".product-item",  # Стандартный элемент товара
            ".catalog-item",  # Элемент каталога
            ".item-product",  # Элемент продукта
            "[class*='product']",  # Любые элементы с 'product' в классе
            "[class*='item']"  # Любые элементы с 'item' в классе
        ]
        
        # Пробуем каждый селектор
        for selector in selectors:
            try:
                elements = await page.query_selector_all(selector)
                for element in elements:
                    try:
                        # Извлекаем информацию о товаре
                        product = {}
                        
                        # Название товара
                        name_elem = await element.query_selector('h1, h2, h3, .title, .name, [class*="title"], [class*="name"]')
                        if name_elem:
                            product['name'] = await name_elem.text_content()
                            product['name'] = product['name'].strip() if product['name'] else ''
                        
                        # Цена
                        price_elem = await element.query_selector('.price, .cost, [class*="price"], [class*="cost"]')
                        if price_elem:
                            price_text = await price_elem.text_content()
                            price_text = price_text.strip() if price_text else ''
                            # Извлекаем только цифры из строки цены
                            price = re.findall(r'\d+[\s.,]?\d*', price_text)
                            if price:
                                product['price'] = price[0].replace(' ', '').replace(',', '.')
                        
                        # URL товара
                        link_elem = await element.query_selector('a')
                        if link_elem:
                            href = await link_elem.get_attribute('href')
                            if href:
                                if not href.startswith('http'):
                                    base_url = page.url
                                    href = urljoin(base_url, href)
                                product['url'] = href
                        
                        # Описание
                        desc_elem = await element.query_selector('.description, .desc, [class*="description"], [class*="desc"]')
                        if desc_elem:
                            product['description'] = await desc_elem.text_content()
                            product['description'] = product['description'].strip() if product['description'] else ''
                        
                        # Добавляем товар, если есть хотя бы название или URL
                        if product.get('name') or product.get('url'):
                            products.append(product)
                            
                    except Exception as e:
                        self.logger.debug(f"Error extracting product details: {str(e)}")
            except Exception as e:
                self.logger.debug(f"Error with selector {selector}: {str(e)}")
                continue
        
        return products

    async def extract_links(self, page: Page) -> List[str]:
        """Извлечение всех ссылок со страницы"""
        links = []
        
        # Ждем загрузки всех ссылок
        await page.wait_for_timeout(5000)
        
        # Список селекторов для извлечения ссылок
        selectors = [
            "a",  # Все элементы <a>
            "link[href]",  # Все элементы <link> с атрибутом href
            "img[src]",  # Все элементы <img> с атрибутом src
            "script[src]",  # Все элементы <script> с атрибутом src
            "iframe[src]",  # Все элементы <iframe> с атрибутом src
            "video[src]",  # Все элементы <video> с атрибутом src
            "audio[src]",  # Все элементы <audio> с атрибутом src
            "object[data]",  # Все элементы <object> с атрибутом data
            "embed[src]",  # Все элементы <embed> с атрибутом src
            "area[href]",  # Все элементы <area> с атрибутом href
            "form[action]",  # Все элементы <form> с атрибутом action
            "input[src]"  # Все элементы <input> с атрибутом src
        ]
        
        # Пробуем каждый селектор
        for selector in selectors:
            try:
                elements = await page.query_selector_all(selector)
                for element in elements:
                    try:
                        # Получаем атрибут href или src в зависимости от типа элемента
                        if selector == "form[action]":
                            href = await element.get_attribute('action')
                        elif selector == "input[src]":
                            href = await element.get_attribute('src')
                        else:
                            href = await element.get_attribute('href') or await element.get_attribute('src')
                        
                        if href and not href.startswith('#') and not href.startswith('javascript:'):
                            # Преобразуем относительные URL в абсолютные
                            if not href.startswith('http'):
                                base_url = page.url
                                href = urljoin(base_url, href)
                            
                            # Добавляем в список, если еще нет
                            if href not in links:
                                links.append(href)
                    except Exception as e:
                        self.logger.debug(f"Error extracting link details: {str(e)}")
            except Exception as e:
                self.logger.debug(f"Error with selector {selector}: {str(e)}")
                continue
        
        return links 