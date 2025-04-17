import asyncio
from site_analyzer import DeepSiteAnalyzer
import json
from datetime import datetime
import os
import logging
from tqdm import tqdm
from typing import List, Dict, Any
import aiofiles
from concurrent.futures import ThreadPoolExecutor

class ParallelSiteAnalyzer:
    def __init__(self, max_concurrent_browsers: int = 3):
        self.max_concurrent_browsers = max_concurrent_browsers
        self.semaphore = asyncio.Semaphore(max_concurrent_browsers)
        self.results: Dict[str, Any] = {}
        
    async def analyze_site(self, url: str, output_dir: str, verbose: bool) -> dict:
        """
        Анализ одного сайта с использованием семафора для контроля параллельных браузеров
        """
        async with self.semaphore:
            print(f"\n{'='*50}")
            print(f"Начинаем анализ сайта {url}...")
            print(f"{'='*50}\n")
            
            try:
                async with DeepSiteAnalyzer() as analyzer:
                    result = await analyzer.analyze_site(url)
                    
                    if "error" in result:
                        print(f"\nОшибка при анализе {url}: {result['error']}")
                        return {"url": url, "error": result["error"]}
                    
                    # Сохраняем результаты асинхронно
                    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                    filename = os.path.join(output_dir, f"{url.replace('https://', '').replace('http://', '')}_{timestamp}.json")
                    
                    async with aiofiles.open(filename, 'w', encoding='utf-8') as f:
                        await f.write(json.dumps(result, ensure_ascii=False, indent=2))
                    
                    print(f'\nАнализ {url} завершен. Результаты сохранены в {filename}')
                    
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
                    
                    return {
                        "url": url,
                        "success": True,
                        "products_count": len(products),
                        "categories_count": len(categories),
                        "filename": filename
                    }
                    
            except Exception as e:
                print(f"\nКритическая ошибка при анализе {url}: {str(e)}")
                return {"url": url, "error": str(e)}

    async def analyze_multiple_sites(self, urls: List[str], output_dir: str = "data", verbose: bool = True):
        """
        Параллельный анализ нескольких сайтов с контролем ресурсов
        """
        # Настройка логирования
        log_level = logging.INFO if verbose else logging.WARNING
        logging.basicConfig(
            level=log_level,
            format='%(asctime)s - %(levelname)s - %(message)s'
        )
        
        # Создаем директорию для результатов если её нет
        os.makedirs(output_dir, exist_ok=True)
        
        # Создаем прогресс-бар
        pbar = tqdm(total=len(urls), desc="Анализ сайтов")
        
        # Запускаем анализ всех сайтов параллельно с контролем ресурсов
        tasks = []
        for url in urls:
            task = asyncio.create_task(self.analyze_site(url, output_dir, verbose))
            task.add_done_callback(lambda p: pbar.update(1))
            tasks.append(task)
        
        results = await asyncio.gather(*tasks, return_exceptions=True)
        
        # Закрываем прогресс-бар
        pbar.close()
        
        # Обрабатываем результаты
        for result in results:
            if isinstance(result, Exception):
                print(f"\nОшибка при выполнении задачи: {str(result)}")
                continue
                
            self.results[result["url"]] = result
        
        # Выводим общую статистику
        print("\n" + "="*50)
        print("ИТОГОВАЯ СТАТИСТИКА:")
        print("="*50)
        
        total_products = 0
        total_categories = 0
        
        for url, result in self.results.items():
            print(f"\nСайт: {url}")
            if "error" in result:
                print(f"Статус: Ошибка - {result['error']}")
            else:
                print(f"Статус: Успешно")
                print(f"Товаров найдено: {result['products_count']}")
                print(f"Категорий найдено: {result['categories_count']}")
                print(f"Результаты сохранены в: {result['filename']}")
                
                total_products += result['products_count']
                total_categories += result['categories_count']
        
        print("\n" + "="*50)
        print(f"ОБЩАЯ СТАТИСТИКА:")
        print(f"Всего проанализировано сайтов: {len(self.results)}")
        print(f"Всего найдено товаров: {total_products}")
        print(f"Всего найдено категорий: {total_categories}")
        print("="*50)

def main():
    # Список сайтов для анализа
    sites = [
        "https://medexe.ru",
        "https://mc.ru"
    ]
    
    try:
        analyzer = ParallelSiteAnalyzer(max_concurrent_browsers=3)
        asyncio.run(analyzer.analyze_multiple_sites(sites, verbose=True))
    except KeyboardInterrupt:
        print("\nАнализ прерван пользователем")
    except Exception as e:
        print(f"\nНепредвиденная ошибка: {str(e)}")

if __name__ == "__main__":
    main() 