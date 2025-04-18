#!/usr/bin/env python3
import asyncio
import logging
import os
import json
from datetime import datetime
from enhanced_site_analyzer import EnhancedSiteAnalyzer
from typing import List, Dict
import aiohttp
import sys

async def analyze_brick_sites(urls: List[str], output_dir: str = "brick_data", verbose: bool = True):
    """Анализ списка сайтов о кирпиче"""
    os.makedirs(output_dir, exist_ok=True)
    
    # Настройка логирования
    log_level = logging.DEBUG if verbose else logging.INFO
    logging.basicConfig(
        level=log_level,
        format='%(asctime)s - %(levelname)s - %(message)s',
        handlers=[
            logging.FileHandler(os.path.join(output_dir, 'analysis.log')),
            logging.StreamHandler()
        ]
    )
    
    # Статистика анализа
    stats = {
        'total_sites': len(urls),
        'successful': 0,
        'failed': 0,
        'products_found': 0,
        'categories_found': 0,
        'start_time': datetime.now().isoformat()
    }
    
    async with EnhancedSiteAnalyzer(verbose=verbose) as analyzer:
        for url in urls:
            try:
                logging.info(f"Analyzing {url}")
                results = await analyzer.analyze_site(url)
                
                # Сохранение результатов
                domain = url.split('//')[1].split('/')[0]
                timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                filename = f"{domain}_{timestamp}.json"
                filepath = os.path.join(output_dir, filename)
                
                with open(filepath, 'w', encoding='utf-8') as f:
                    json.dump(results, f, ensure_ascii=False, indent=2)
                
                # Обновление статистики
                stats['successful'] += 1
                stats['products_found'] += len(results.get('products', []))
                stats['categories_found'] += len(results.get('categories', []))
                
                logging.info(f"Analysis completed for {url}")
                logging.info(f"Found {len(results['categories'])} categories")
                logging.info(f"Found {len(results['products'])} products")
                logging.info(f"Results saved to {filepath}")
                
            except Exception as e:
                stats['failed'] += 1
                logging.error(f"Error analyzing {url}: {str(e)}")
                continue
    
    # Сохранение общей статистики
    stats['end_time'] = datetime.now().isoformat()
    stats_file = os.path.join(output_dir, 'analysis_stats.json')
    with open(stats_file, 'w', encoding='utf-8') as f:
        json.dump(stats, f, ensure_ascii=False, indent=2)
    
    # Вывод итоговой статистики
    logging.info("\nAnalysis completed!")
    logging.info(f"Total sites processed: {stats['total_sites']}")
    logging.info(f"Successful: {stats['successful']}")
    logging.info(f"Failed: {stats['failed']}")
    logging.info(f"Total products found: {stats['products_found']}")
    logging.info(f"Total categories found: {stats['categories_found']}")

def main():
    # Чтение списка URL из файла
    with open('brick_sites.txt', 'r', encoding='utf-8') as f:
        urls = [line.strip() for line in f if line.strip()]
    
    # Запуск анализа
    asyncio.run(analyze_brick_sites(urls, verbose=True))

if __name__ == '__main__':
    main() 