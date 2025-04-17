import asyncio
import argparse
from site_analyzer import DeepSiteAnalyzer
import json
from datetime import datetime
import os
import logging
from urllib.parse import urlparse

async def analyze_site(url: str, output_dir: str = "data", verbose: bool = False):
    """
    Анализ сайта с сохранением результатов
    
    Args:
        url: URL сайта для анализа
        output_dir: Директория для сохранения результатов
        verbose: Подробный вывод логов
    """
    # Настройка логирования
    log_level = logging.INFO if verbose else logging.WARNING
    logging.basicConfig(
        level=log_level,
        format='%(asctime)s - %(levelname)s - %(message)s'
    )
    
    # Создаем директорию для результатов если её нет
    os.makedirs(output_dir, exist_ok=True)
    
    print(f"Начинаем анализ сайта {url}...")
    
    try:
        async with DeepSiteAnalyzer() as analyzer:
            result = await analyzer.analyze_site(url)
            
            if "error" in result:
                print(f"\nОшибка при анализе: {result['error']}")
                return
            
            # Получаем домен для имени файла
            domain = urlparse(url).netloc
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = os.path.join(output_dir, f"{domain}_{timestamp}.json")
            
            # Сохраняем результаты
            with open(filename, 'w', encoding='utf-8') as f:
                json.dump(result, f, ensure_ascii=False, indent=2)
                
            print(f'\nАнализ завершен. Результаты сохранены в {filename}')
            
            # Выводим статистику
            products = result.get("products", [])
            categories = result.get("categories", [])
            
            print(f'Найдено товаров: {len(products)}')
            print(f'Найдено категорий: {len(categories)}')
            
            if categories:
                print('\nНайденные категории:')
                for category in categories[:10]:
                    print(f"- {category.get('name', 'Без имени')}")
                    if verbose and category.get('url'):
                        print(f"  URL: {category['url']}")
            
            if products:
                print('\nПримеры товаров:')
                for product in products[:5]:
                    print(f"- {product.get('name', 'Без имени')}")
                    if verbose:
                        if product.get('price'):
                            print(f"  Цена: {product['price']}")
                        if product.get('url'):
                            print(f"  URL: {product['url']}")
                        print()
                        
    except Exception as e:
        print(f"\nКритическая ошибка: {str(e)}")

def main():
    parser = argparse.ArgumentParser(description='Анализатор структуры сайтов')
    parser.add_argument('url', help='URL сайта для анализа')
    parser.add_argument('-o', '--output', default='data', help='Директория для сохранения результатов')
    parser.add_argument('-v', '--verbose', action='store_true', help='Подробный вывод')
    
    args = parser.parse_args()
    
    try:
        asyncio.run(analyze_site(args.url, args.output, args.verbose))
    except KeyboardInterrupt:
        print("\nАнализ прерван пользователем")
    except Exception as e:
        print(f"\nНепредвиденная ошибка: {str(e)}")

if __name__ == "__main__":
    main() 