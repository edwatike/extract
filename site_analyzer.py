import asyncio
import logging
from playwright.async_api import async_playwright, Browser, Page, Request, Response, Playwright
import json
import time
from typing import Dict, List, Optional
import random
from urllib.parse import urljoin, urlparse

class AntiBotBypassStrategy:
    """Стратегии обхода анти-бот защиты"""
    
    @staticmethod
    async def handle_cloudflare(page: Page) -> bool:
        """Обработка Cloudflare защиты"""
        try:
            # Ждем появления потенциального Cloudflare challenge
            challenge_frame = await page.query_selector("iframe[title*='challenge']")
            if challenge_frame:
                # Даем время на решение капчи и проверки
                await page.wait_for_timeout(random.randint(5000, 8000))
                
                # Проверяем, исчез ли iframe с капчей
                challenge_frame = await page.query_selector("iframe[title*='challenge']")
                return challenge_frame is None
            
            return True
            
        except Exception as e:
            logging.error(f"Error in Cloudflare handling: {str(e)}")
            return True  # Если не нашли Cloudflare challenge, считаем что защиты нет
    
    @staticmethod
    async def handle_general_protection(page: Page) -> bool:
        """Общие методы обхода защиты"""
        try:
            # Эмуляция человеческого поведения
            await page.mouse.move(random.randint(100, 700), random.randint(100, 700))
            await page.wait_for_timeout(random.randint(500, 1500))
            
            # Проверяем типичные элементы капчи
            selectors = [
                "iframe[src*='captcha']",
                "iframe[src*='challenge']",
                "div[class*='captcha']",
                "div[class*='challenge']",
                "div[class*='robot']",
                "div[class*='security']"
            ]
            
            for selector in selectors:
                try:
                    element = await page.wait_for_selector(selector, timeout=3000)
                    if element:
                        await page.wait_for_timeout(random.randint(4000, 7000))
                except Exception:
                    continue
            
            return True
            
        except Exception as e:
            logging.error(f"Error in general protection handling: {str(e)}")
            return False

class DeepSiteAnalyzer:
    def __init__(self):
        self.browser: Optional[Browser] = None
        self.page: Optional[Page] = None
        self.playwright: Optional[Playwright] = None
        self.request_log: List[Dict] = []
        self.logger = logging.getLogger(__name__)
        self.anti_bot = AntiBotBypassStrategy()
        
        # Настройка эмуляции браузера
        self.browser_options = {
            'viewport': {'width': 1920, 'height': 1080},
            'user_agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36',
            'locale': 'ru-RU',
            'timezone_id': 'Europe/Moscow',
            'geolocation': {'latitude': 55.7558, 'longitude': 37.6173},
            'permissions': ['geolocation']
        }

    async def init_browser(self):
        """Инициализация браузера"""
        try:
            self.logger.info("Initializing browser...")
            if not self.playwright:
                self.playwright = await async_playwright().start()
                self.logger.info("Playwright started")
                
            if not self.browser:
                self.logger.info("Launching browser...")
                self.browser = await self.playwright.chromium.launch(
                    headless=False,  # Запускаем в видимом режиме для отладки
                    args=[
                        '--no-sandbox',
                        '--disable-setuid-sandbox',
                        '--disable-dev-shm-usage',
                        '--disable-accelerated-2d-canvas',
                        '--window-size=1920,1080'
                    ]
                )
                self.logger.info("Browser launched successfully")
        except Exception as e:
            self.logger.error(f"Error initializing browser: {str(e)}")
            raise

    async def cleanup(self):
        """Очистка ресурсов"""
        if self.page:
            try:
                await self.page.close()
            except Exception:
                pass
            self.page = None
            
        if self.browser:
            try:
                await self.browser.close()
            except Exception:
                pass
            self.browser = None
            
        if self.playwright:
            try:
                await self.playwright.stop()
            except Exception:
                pass
            self.playwright = None

    async def __aenter__(self):
        await self.init_browser()
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        await self.cleanup()

    def handle_request(self, request: Request):
        """Синхронная обработка запроса"""
        try:
            post_data = None
            if request.method == 'POST':
                try:
                    post_data = request.post_data
                except:
                    post_data = None
                    
            self.logger.info(f"Network request: {request.method} {request.url}")
            self.request_log.append({
                'method': request.method,
                'url': request.url,
                'headers': dict(request.headers),
                'post_data': post_data
            })
        except Exception as e:
            self.logger.error(f"Error handling request: {str(e)}")

    async def handle_cookies(self, page: Page):
        """Управление cookies для обхода защиты"""
        try:
            # Получаем все cookies
            cookies = await page.context.cookies()
            
            # Анализируем и модифицируем при необходимости
            modified_cookies = []
            for cookie in cookies:
                if 'security' in cookie.get('name', '').lower() or 'cf_' in cookie.get('name', '').lower():
                    # Сохраняем важные security cookies
                    modified_cookies.append(cookie)
                    
            # Устанавливаем обработанные cookies
            if modified_cookies:
                await page.context.add_cookies(modified_cookies)
                
        except Exception as e:
            self.logger.warning(f"Error handling cookies: {str(e)}")

    async def setup_local_storage(self, page: Page):
        """Настройка localStorage для обхода защиты"""
        try:
            # Устанавливаем фиктивные значения localStorage
            await page.evaluate("""() => {
                try {
                    const fakeStorage = {
                        'device_id': Math.random().toString(36).substring(7),
                        'session_started': Date.now(),
                        'browser_type': 'Chrome',
                        'platform': 'Win32',
                        'user_agent': navigator.userAgent
                    };
                    
                    for (let key in fakeStorage) {
                        try {
                            localStorage.setItem(key, fakeStorage[key]);
                        } catch (e) {
                            console.warn('localStorage not available:', e);
                        }
                    }
                } catch (e) {
                    console.warn('Error in localStorage setup:', e);
                }
            }""")
            
        except Exception as e:
            self.logger.warning(f"Error setting up localStorage: {str(e)}")

    async def create_page(self) -> Page:
        """Создание страницы с продвинутыми настройками против обнаружения"""
        try:
            self.logger.info("Creating new page...")
            if not self.browser:
                await self.init_browser()
                
            context = await self.browser.new_context(
                viewport=self.browser_options['viewport'],
                user_agent=self.browser_options['user_agent'],
                locale=self.browser_options['locale'],
                timezone_id=self.browser_options['timezone_id'],
                geolocation=self.browser_options['geolocation'],
                permissions=self.browser_options['permissions'],
                ignore_https_errors=True,  # Игнорируем ошибки SSL
                java_script_enabled=True  # Включаем JavaScript
            )
            self.logger.info("Browser context created")
            
            # Добавляем случайные заголовки и скрипты
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
            self.logger.info("Init scripts added")
            
            page = await context.new_page()
            self.logger.info("New page created")
            
            # Устанавливаем таймауты
            page.set_default_navigation_timeout(60000)
            page.set_default_timeout(30000)
            self.logger.info("Timeouts set")
            
            await page.set_extra_http_headers({
                'Accept-Language': 'ru-RU,ru;q=0.9,en-US;q=0.8,en;q=0.7',
                'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
                'DNT': '1',
                'Upgrade-Insecure-Requests': '1',
                'Sec-Fetch-Dest': 'document',
                'Sec-Fetch-Mode': 'navigate',
                'Sec-Fetch-Site': 'none',
                'Sec-Fetch-User': '?1',
                'Cache-Control': 'no-cache',
                'Pragma': 'no-cache'
            })
            self.logger.info("Headers set")
            
            # Устанавливаем размер окна
            await page.set_viewport_size({"width": 1920, "height": 1080})
            
            return page
            
        except Exception as e:
            self.logger.error(f"Error creating page: {str(e)}")
            raise

    async def bypass_protection(self, page: Page) -> bool:
        """Комплексный обход защиты"""
        try:
            # Проверяем наличие Cloudflare
            if not await self.anti_bot.handle_cloudflare(page):
                # Если не удалось обойти Cloudflare, пробуем альтернативный метод
                await self.handle_alternative_protection(page)
            
            # Проверяем наличие reCAPTCHA
            recaptcha_frame = await page.query_selector("iframe[src*='recaptcha']")
            if recaptcha_frame:
                self.logger.warning("Detected reCAPTCHA, waiting for timeout...")
                await page.wait_for_timeout(random.randint(10000, 15000))
            
            # Проверяем наличие hCaptcha
            hcaptcha_frame = await page.query_selector("iframe[src*='hcaptcha']")
            if hcaptcha_frame:
                self.logger.warning("Detected hCaptcha, waiting for timeout...")
                await page.wait_for_timeout(random.randint(10000, 15000))
            
            # Пробуем обойти общую защиту
            if not await self.anti_bot.handle_general_protection(page):
                return False
            
            return True
            
        except Exception as e:
            self.logger.error(f"Error in protection bypass: {str(e)}")
            return False

    async def handle_alternative_protection(self, page: Page):
        """Альтернативные методы обхода защиты"""
        try:
            # Эмуляция событий мыши
            await page.mouse.move(random.randint(100, 700), random.randint(100, 700))
            await page.mouse.down()
            await page.wait_for_timeout(random.randint(50, 150))
            await page.mouse.up()
            
            # Эмуляция клавиатуры
            await page.keyboard.press('Tab')
            await page.wait_for_timeout(random.randint(100, 300))
            
            # Проверка на наличие cookie-consent
            cookie_buttons = await page.query_selector_all([
                'button:has-text("Accept")', 
                'button:has-text("Принять")',
                'button:has-text("Agree")',
                '[id*="cookie"] button',
                '[class*="cookie"] button'
            ].join(','))
            
            for button in cookie_buttons:
                try:
                    await button.click()
                except Exception:
                    continue
            
            # Установка дополнительных cookies
            await page.context.add_cookies([{
                'name': 'cf_clearance',
                'value': ''.join(random.choices('0123456789abcdef', k=32)),
                'domain': urlparse(page.url).netloc
            }])
            
            # Добавление случайных задержек
            await page.wait_for_timeout(random.randint(2000, 5000))
            
        except Exception as e:
            self.logger.warning(f"Error in alternative protection handling: {str(e)}")

    async def wait_for_dynamic_content(self, page: Page):
        """Ожидание загрузки динамического контента"""
        try:
            # Ждем загрузки AJAX-запросов
            await page.wait_for_load_state("networkidle")
            
            # Проверяем наличие динамических элементов
            await page.evaluate("""
                new Promise((resolve) => {
                    let lastHeight = document.body.scrollHeight;
                    let retries = 0;
                    
                    const checkHeight = () => {
                        const newHeight = document.body.scrollHeight;
                        if (newHeight === lastHeight || retries > 5) {
                            resolve();
                        } else {
                            lastHeight = newHeight;
                            retries++;
                            setTimeout(checkHeight, 1000);
                        }
                    };
                    
                    setTimeout(checkHeight, 1000);
                });
            """)
            
        except Exception as e:
            self.logger.warning(f"Error waiting for dynamic content: {str(e)}")

    async def simulate_human_behavior(self, page: Page):
        """Эмуляция человеческого поведения"""
        try:
            # Случайные движения мыши
            for _ in range(random.randint(2, 5)):
                await page.mouse.move(
                    random.randint(100, 800),
                    random.randint(100, 600)
                )
                await page.wait_for_timeout(random.randint(200, 500))

            # Случайный скролл
            await page.evaluate("""
                window.scrollTo({
                    top: Math.random() * document.body.scrollHeight * 0.8,
                    behavior: 'smooth'
                });
            """)
            
            await page.wait_for_timeout(random.randint(500, 1500))
            
        except Exception as e:
            self.logger.warning(f"Error in human behavior simulation: {str(e)}")

    async def analyze_site(self, url: str) -> Dict:
        """Анализ сайта с обходом защиты"""
        try:
            self.logger.info("Starting site analysis...")
            
            # Создаем новую страницу
            self.page = await self.create_page()
            if not self.page:
                raise Exception("Failed to create page")
            self.logger.info("Page created successfully")
                
            # Подписываемся на события запросов
            self.page.on("request", self.handle_request)
            self.logger.info("Request handler attached")
            
            # Переход на страницу с обработкой защиты
            self.logger.info(f"Navigating to {url}")
            try:
                response = await self.page.goto(url, wait_until="networkidle", timeout=60000)
                self.logger.info("Navigation completed")
                
                if not response:
                    raise Exception("Failed to load the page")
                    
                status = response.status
                self.logger.info(f"Page loaded with status code: {status}")
                
                if status != 200:
                    raise Exception(f"Page returned status code {status}")
                
                # Даем время на загрузку страницы
                await self.page.wait_for_timeout(5000)
                self.logger.info("Initial wait completed")
                
                # Обработка cookies после загрузки страницы
                await self.handle_cookies(self.page)
                self.logger.info("Cookies handled")
                
                # Пытаемся обойти защиту
                self.logger.info("Attempting to bypass protection...")
                if not await self.bypass_protection(self.page):
                    # Если не удалось обойти защиту, пробуем альтернативный метод
                    self.logger.info("Using alternative protection bypass...")
                    await self.handle_alternative_protection(self.page)
                
                # Эмуляция человеческого поведения
                self.logger.info("Simulating human behavior...")
                await self.simulate_human_behavior(self.page)
                
                # Ждем загрузки динамического контента
                self.logger.info("Waiting for dynamic content...")
                await self.wait_for_dynamic_content(self.page)
                
                # Проверяем, что страница загружена корректно
                self.logger.info("Checking page content...")
                content = await self.page.content()
                if not content or len(content) < 1000:
                    raise Exception("Page content is too short, possible protection")
                
                # Собираем информацию
                self.logger.info("Collecting page information...")
                result = {
                    "title": await self.page.title(),
                    "url": url,
                    "html": content,
                    "text": await self.page.evaluate('document.body.innerText'),
                    "links": await self.extract_links(),
                    "products": await self.extract_products(),
                    "categories": await self.extract_categories(self.page),
                    "request_log": self.request_log,
                    "status_code": status
                }
                
                self.logger.info("Analysis completed successfully")
                return result
                
            except Exception as e:
                self.logger.error(f"Error during page navigation: {str(e)}")
                self.logger.error(f"Page state: {self.page}")
                raise
            
        except Exception as e:
            self.logger.error(f"Error during site analysis: {str(e)}")
            self.logger.error(f"Current page state: {self.page}")
            return {"error": str(e)}
            
        finally:
            # Очищаем ресурсы страницы
            if self.page:
                try:
                    await self.page.close()
                    self.logger.info("Page closed")
                except Exception as e:
                    self.logger.error(f"Error closing page: {str(e)}")
                self.page = None

    async def extract_links(self) -> List[Dict]:
        """Извлечение ссылок со страницы"""
        try:
            links = await self.page.evaluate("""() => {
                return Array.from(document.querySelectorAll('a')).map(a => ({
                    text: a.innerText.trim(),
                    url: a.href,
                    title: a.title
                })).filter(link => link.url && link.url.startsWith('http'));
            }""")
            return links
        except Exception as e:
            self.logger.error(f"Error extracting links: {str(e)}")
            return []

    async def extract_products(self) -> List[Dict]:
        """Извлечение информации о продуктах"""
        try:
            products = await self.page.evaluate("""() => {
                return Array.from(document.querySelectorAll([
                    '[itemtype*="Product"]',
                    '.product',
                    '.product-item',
                    '.product-card',
                    '[class*="product"]',
                    '[id*="product"]'
                ].join(','))).map(product => {
                    const priceEl = product.querySelector('[itemprop="price"], .price, [class*="price"]');
                    const nameEl = product.querySelector('[itemprop="name"], .name, .title, h1, h2, h3');
                    const imgEl = product.querySelector('img');
                    
                    return {
                        name: nameEl ? nameEl.innerText.trim() : null,
                        price: priceEl ? priceEl.innerText.trim() : null,
                        url: product.tagName === 'A' ? product.href : 
                             product.querySelector('a') ? product.querySelector('a').href : null,
                        image: imgEl ? imgEl.src : null
                    };
                }).filter(p => p.name || p.url);
            }""")
            return products
        except Exception as e:
            self.logger.error(f"Error extracting products: {str(e)}")
            return []

    async def extract_categories(self, page) -> List[Dict[str, str]]:
        """Extract category links from the page."""
        categories = []
        
        # Wait for the menu elements to load
        await page.wait_for_timeout(5000)  # Increased timeout for dynamic content
        
        # List of selectors to try for category extraction
        selectors = [
            ".menu-menu1 a",  # Main menu items
            ".menu-menu2 a",  # Submenu items
            ".cats-wrap .item a",  # Product category cards
            ".big-menu a",  # Big menu items
            "nav[id^='nav'] a",  # Navigation menu items
            ".catalog-menu a",  # Catalog menu items
            "#menu a",  # Menu items
            ".categories a",  # Generic categories
            ".product-categories a"  # Product categories
        ]
        
        # Try each selector
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
                                # Convert relative URLs to absolute
                                if not href.startswith('http'):
                                    base_url = page.url
                                    href = urljoin(base_url, href)
                                
                                # Add to categories if not already present
                                category = {'name': name, 'url': href}
                                if category not in categories:
                                    categories.append(category)
                    except Exception as e:
                        self.logger.debug(f"Error extracting category details: {str(e)}")
            except Exception as e:
                self.logger.debug(f"Error with selector {selector}: {str(e)}")
                continue
        
        # Remove duplicates while preserving order
        seen = set()
        unique_categories = []
        for cat in categories:
            cat_tuple = (cat['name'], cat['url'])
            if cat_tuple not in seen:
                seen.add(cat_tuple)
                unique_categories.append(cat)
        
        # Filter out non-category links
        filtered_categories = []
        exclude_patterns = [
            '/about/', '/contacts/', '/feedback/', '/user/',
            'javascript:', '#', 'tel:', 'mailto:',
            '/docs/', '/transportation/', '/service/'
        ]
        
        for cat in unique_categories:
            if not any(pattern in cat['url'].lower() for pattern in exclude_patterns):
                if cat['name'].strip() and len(cat['name'].strip()) > 1:  # Ensure name is not empty or too short
                    filtered_categories.append(cat)
        
        return filtered_categories
