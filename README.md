# Site Analyzer

Инструмент для анализа веб-сайтов и извлечения информации о компаниях.

## Возможности

- Анализ структуры сайта
- Извлечение категорий и продуктов
- Поиск ИНН компаний
- Параллельная обработка нескольких сайтов
- Подробное логирование процесса
- Сохранение результатов в JSON формате

## Требования

- Python 3.8+
- Playwright
- aiohttp
- backoff

## Установка

1. Клонируйте репозиторий:
```bash
git clone https://github.com/yourusername/site-analyzer.git
cd site-analyzer
```

2. Создайте виртуальное окружение и активируйте его:
```bash
python -m venv venv
source venv/bin/activate  # для Linux/Mac
# или
venv\Scripts\activate  # для Windows
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

### Анализ одного сайта

```bash
python site_analyzer_cli.py https://example.com -v
```

### Анализ нескольких сайтов

```bash
python analyze_multiple_sites.py https://example1.com https://example2.com -v
```

### Извлечение ИНН

```bash
python extract_inn.py
```

## Структура проекта

```
site-analyzer/
├── README.md
├── requirements.txt
├── site_analyzer.py
├── site_analyzer_cli.py
├── enhanced_site_analyzer.py
├── analyze_multiple_sites.py
├── extract_inn.py
└── data/
    └── results/
```

## Лицензия

MIT 