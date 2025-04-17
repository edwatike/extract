from typing import Dict, Any, List
from dataclasses import dataclass
from urllib.parse import urlparse

@dataclass
class SiteSelectors:
    """Селекторы для извлечения данных с сайта"""
    product_list: List[str]  # Селекторы для списка товаров
    product_name: List[str]  # Селекторы для названия товара
    product_price: List[str]  # Селекторы для цены
    product_description: List[str]  # Селекторы для описания
    product_characteristics: List[str]  # Селекторы для характеристик
    product_category: List[str]  # Селекторы для категории
    product_stock: List[str]  # Селекторы для наличия
    product_image: List[str]  # Селекторы для изображений
    pagination: List[str]  # Селекторы для пагинации
    wait_for: List[str]  # Селекторы для ожидания загрузки контента

@dataclass
class SiteRules:
    """Правила парсинга для конкретного сайта"""
    selectors: SiteSelectors
    api_endpoints: List[str]  # API эндпоинты для проверки
    dynamic_loading: bool  # Требуется ли ожидание динамической загрузки
    js_scroll: bool  # Требуется ли прокрутка для загрузки контента
    ajax_pagination: bool  # Используется ли AJAX пагинация
    requires_js: bool  # Требуется ли JavaScript для работы сайта
    wait_time: int  # Время ожидания загрузки в миллисекундах
    custom_headers: Dict[str, str]  # Дополнительные заголовки

class SiteRulesRegistry:
    """Реестр правил парсинга для разных сайтов"""
    
    def __init__(self):
        self.rules = {}
        self._init_rules()
    
    def _init_rules(self):
        """Инициализация правил для известных сайтов"""
        
        # Правила для mc.ru
        self.rules['mc.ru'] = SiteRules(
            selectors=SiteSelectors(
                product_list=[
                    '.table-row',
                    'tr[data-id]',
                    '.product-row',
                    '.catalog-item'
                ],
                product_name=[
                    'a[href*="metalloprokat"]',
                    '.name',
                    '.title',
                    '[data-name]'
                ],
                product_price=[
                    '[data-price]',
                    '.price',
                    'td:nth-child(5)'
                ],
                product_description=[
                    '.description',
                    '.product-description',
                    '[data-description]'
                ],
                product_characteristics=[
                    '.characteristics',
                    '.specifications',
                    '.params'
                ],
                product_category=[
                    '.breadcrumbs',
                    '.category-name',
                    '[data-category]'
                ],
                product_stock=[
                    '[data-stock]',
                    '.stock',
                    'td:last-child'
                ],
                product_image=[
                    '.product-image',
                    '.gallery-image',
                    '[data-image]'
                ],
                pagination=[
                    '.pagination',
                    '.pages',
                    '[data-pagination]'
                ],
                wait_for=[
                    'table.products-table',
                    'table.price-table',
                    '.catalog-item',
                    '.product-item'
                ]
            ),
            api_endpoints=[
                '/api/products',
                '/api/catalog',
                '/data/products'
            ],
            dynamic_loading=True,
            js_scroll=True,
            ajax_pagination=True,
            requires_js=True,
            wait_time=5000,
            custom_headers={
                'X-Requested-With': 'XMLHttpRequest',
                'Accept': 'application/json'
            }
        )
        
        # Правила для medexe.ru
        self.rules['medexe.ru'] = SiteRules(
            selectors=SiteSelectors(
                product_list=[
                    '.product-item',
                    '.catalog-item',
                    '.goods-item'
                ],
                product_name=[
                    '.product-name',
                    '.item-name',
                    'h3.title'
                ],
                product_price=[
                    '.product-price',
                    '.price',
                    '[data-price]'
                ],
                product_description=[
                    '.product-description',
                    '.description',
                    '[data-description]'
                ],
                product_characteristics=[
                    '.product-params',
                    '.characteristics',
                    '.specs'
                ],
                product_category=[
                    '.breadcrumbs',
                    '.category-path',
                    '[data-category]'
                ],
                product_stock=[
                    '.stock-status',
                    '.availability',
                    '[data-stock]'
                ],
                product_image=[
                    '.product-image',
                    '.item-image',
                    '[data-image]'
                ],
                pagination=[
                    '.pagination',
                    '.pages',
                    '.load-more'
                ],
                wait_for=[
                    '.product-list',
                    '.catalog-items',
                    '.goods-container'
                ]
            ),
            api_endpoints=[
                '/api/catalog',
                '/api/products',
                '/ajax/items'
            ],
            dynamic_loading=True,
            js_scroll=False,
            ajax_pagination=True,
            requires_js=True,
            wait_time=3000,
            custom_headers={
                'X-Requested-With': 'XMLHttpRequest'
            }
        )
    
    def get_rules(self, url: str) -> SiteRules:
        """Получение правил для конкретного сайта"""
        domain = urlparse(url).netloc.replace('www.', '')
        return self.rules.get(domain, self._get_default_rules())
    
    def _get_default_rules(self) -> SiteRules:
        """Получение правил по умолчанию"""
        return SiteRules(
            selectors=SiteSelectors(
                product_list=[
                    '.product',
                    '.item',
                    '[itemtype="http://schema.org/Product"]'
                ],
                product_name=[
                    '.name',
                    '.title',
                    'h1, h2, h3'
                ],
                product_price=[
                    '.price',
                    '[itemprop="price"]'
                ],
                product_description=[
                    '.description',
                    '[itemprop="description"]'
                ],
                product_characteristics=[
                    '.characteristics',
                    '.specs',
                    '.params'
                ],
                product_category=[
                    '.category',
                    '.breadcrumbs'
                ],
                product_stock=[
                    '.stock',
                    '.availability'
                ],
                product_image=[
                    '.image',
                    '[itemprop="image"]'
                ],
                pagination=[
                    '.pagination',
                    '.pages'
                ],
                wait_for=[
                    '.products',
                    '.items'
                ]
            ),
            api_endpoints=[],
            dynamic_loading=False,
            js_scroll=False,
            ajax_pagination=False,
            requires_js=False,
            wait_time=1000,
            custom_headers={}
        )

    def add_rules(self, domain: str, rules: SiteRules):
        """Добавление новых правил для сайта"""
        self.rules[domain] = rules

    def remove_rules(self, domain: str):
        """Удаление правил для сайта"""
        if domain in self.rules:
            del self.rules[domain] 