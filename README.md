# Enhanced Site Analyzer

Мощный инструмент для анализа структуры веб-сайтов, извлечения категорий, продуктов и ссылок с использованием Playwright.

## Возможности

- Анализ структуры сайта
- Извлечение категорий и продуктов
- Обход защиты от ботов
- Сохранение результатов в JSON формате
- Поддержка прокси
- Подробное логирование
- Параллельный анализ нескольких сайтов

## Установка

1. Клонируйте репозиторий:
```bash
git clone https://github.com/yourusername/enhanced-site-analyzer.git
cd enhanced-site-analyzer
```

2. Создайте виртуальное окружение и активируйте его:
```bash
python -m venv venv
source venv/bin/activate  # Linux/Mac
# или
venv\Scripts\activate  # Windows
```

3. Установите зависимости:
```bash
pip install -r requirements.txt
```

4. Установите браузеры для Playwright:
```bash
playwright install
```

## Использование

### Базовый анализ сайта:
```bash
python enhanced_analyzer_cli.py https://example.com
```

### Анализ с подробным выводом:
```bash
python enhanced_analyzer_cli.py https://example.com -v
```

### Анализ нескольких сайтов:
```bash
python enhanced_analyzer_cli.py https://site1.com https://site2.com -v
```

### Сохранение результатов в определенную директорию:
```bash
python enhanced_analyzer_cli.py https://example.com -o results -v
```

## Структура проекта

- `enhanced_site_analyzer.py` - основной класс анализатора
- `enhanced_analyzer_cli.py` - CLI интерфейс
- `requirements.txt` - зависимости проекта
- `data/` - директория для сохранения результатов (создается автоматически)

## Результаты анализа

Результаты сохраняются в JSON файлы в формате:
```json
{
    "url": "https://example.com",
    "title": "Site Title",
    "structure": {
        "navigation": [...],
        "mainContent": {...},
        "sidebar": {...},
        "footer": {...}
    },
    "categories": [
        {"name": "Category 1", "url": "https://example.com/cat1"},
        ...
    ],
    "products": [
        {"name": "Product 1", "url": "https://example.com/prod1", "price": "100.00"},
        ...
    ],
    "links": [...],
    "request_log": [...],
    "timestamp": "2024-04-18T01:13:15.894"
}
```

## Лицензия

MIT License 