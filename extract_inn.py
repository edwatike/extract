#!/usr/bin/env python3
import asyncio
import logging
import os
import json
import re
from datetime import datetime
from typing import List, Tuple, Optional
from enhanced_site_analyzer import EnhancedSiteAnalyzer
import aiohttp
import backoff
import signal
from contextlib import asynccontextmanager

# Настройка логирования
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('inn_extraction.log'),
        logging.StreamHandler()
    ]
)

# Глобальные переменные для управления состоянием
shutdown_event = asyncio.Event()

def signal_handler():
    """Обработчик сигнала для корректного завершения"""
    logging.info("Received shutdown signal, cleaning up...")
    shutdown_event.set()

@asynccontextmanager
async def get_analyzer():
    """Контекстный менеджер для работы с анализатором"""
    analyzer = None
    try:
        analyzer = EnhancedSiteAnalyzer(verbose=True)
        await analyzer.__aenter__()
        yield analyzer
    finally:
        if analyzer:
            try:
                await analyzer.__aexit__(None, None, None)
            except Exception as e:
                logging.error(f"Error closing analyzer: {str(e)}")

async def check_site_availability(url: str) -> bool:
    """Проверяет доступность сайта"""
    try:
        timeout = aiohttp.ClientTimeout(total=10)
        async with aiohttp.ClientSession(timeout=timeout) as session:
            async with session.get(url) as response:
                return response.status == 200
    except Exception as e:
        logging.warning(f"Site {url} is not available: {str(e)}")
        return False

@backoff.on_exception(backoff.expo, 
                     (Exception,),
                     max_tries=3,
                     giveup=lambda e: isinstance(e, (KeyboardInterrupt, SystemExit)))
async def extract_inn(url: str, analyzer: EnhancedSiteAnalyzer) -> Tuple[str, Optional[str], bool]:
    """
    Извлекает ИНН из указанного URL.
    Возвращает: (url, inn, success)
    """
    if shutdown_event.is_set():
        raise asyncio.CancelledError("Shutdown requested")

    try:
        # Проверяем доступность сайта
        if not await check_site_availability(url):
            return url, None, False

        results = await analyzer.analyze_site(url)
        content = results.get('content', '')
        
        # Поиск ИНН в тексте
        inn_pattern = r'\b\d{10}\b|\b\d{12}\b'
        inns = re.findall(inn_pattern, content)
        
        for inn in inns:
            if len(inn) == 10 and check_inn_organization(inn):
                return url, inn, True
            elif len(inn) == 12 and check_inn_individual(inn):
                return url, inn, True
        
        return url, None, False
    except Exception as e:
        logging.error(f"Error extracting INN from {url}: {str(e)}")
        raise

def check_inn_organization(inn: str) -> bool:
    """Проверка контрольной суммы ИНН организации"""
    if len(inn) != 10:
        return False
    
    weights = [2, 4, 10, 3, 5, 9, 4, 6, 8]
    checksum = sum(int(inn[i]) * weights[i] for i in range(9)) % 11
    if checksum == 10:
        checksum = 0
    return checksum == int(inn[9])

def check_inn_individual(inn: str) -> bool:
    """Проверка контрольных сумм ИНН ИП"""
    if len(inn) != 12:
        return False
    
    # Первая контрольная сумма
    weights1 = [7, 2, 4, 10, 3, 5, 9, 4, 6, 8]
    checksum1 = sum(int(inn[i]) * weights1[i] for i in range(10)) % 11
    if checksum1 == 10:
        checksum1 = 0
    if checksum1 != int(inn[10]):
        return False
    
    # Вторая контрольная сумма
    weights2 = [3, 7, 2, 4, 10, 3, 5, 9, 4, 6, 8]
    checksum2 = sum(int(inn[i]) * weights2[i] for i in range(11)) % 11
    if checksum2 == 10:
        checksum2 = 0
    return checksum2 == int(inn[11])

async def process_sites(urls: List[str], output_dir: str = "data"):
    """Обрабатывает список сайтов и сохраняет результаты"""
    os.makedirs(output_dir, exist_ok=True)
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    
    found_inn = []
    not_found_inn = []
    
    try:
        async with get_analyzer() as analyzer:
            for url in urls:
                if shutdown_event.is_set():
                    break

                try:
                    url, inn, success = await extract_inn(url, analyzer)
                    result = {
                        "url": url,
                        "timestamp": datetime.now().isoformat(),
                        "inn": inn
                    }
                    
                    if success:
                        found_inn.append(result)
                        logging.info(f"Found INN {inn} for {url}")
                    else:
                        not_found_inn.append(result)
                        logging.info(f"No INN found for {url}")
                        
                except Exception as e:
                    logging.error(f"Failed to process {url}: {str(e)}")
                    not_found_inn.append({
                        "url": url,
                        "timestamp": datetime.now().isoformat(),
                        "error": str(e)
                    })
    except Exception as e:
        logging.error(f"Error in process_sites: {str(e)}")
    finally:
        # Сохранение результатов
        try:
            with open(os.path.join(output_dir, f"found_inn_{timestamp}.json"), 'w', encoding='utf-8') as f:
                json.dump(found_inn, f, ensure_ascii=False, indent=2)
            
            with open(os.path.join(output_dir, f"not_found_inn_{timestamp}.json"), 'w', encoding='utf-8') as f:
                json.dump(not_found_inn, f, ensure_ascii=False, indent=2)
            
            logging.info(f"Found INN for {len(found_inn)} sites")
            logging.info(f"No INN found for {len(not_found_inn)} sites")
        except Exception as e:
            logging.error(f"Error saving results: {str(e)}")

def main():
    # Настройка обработчика сигналов
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    
    for sig in (signal.SIGINT, signal.SIGTERM):
        loop.add_signal_handler(sig, signal_handler)
    
    try:
        # Чтение списка сайтов из файла
        with open('brick_sites.txt', 'r', encoding='utf-8') as f:
            urls = [line.strip() for line in f if line.strip()]
        
        loop.run_until_complete(process_sites(urls))
    except KeyboardInterrupt:
        logging.info("Received keyboard interrupt, shutting down...")
    finally:
        loop.close()

if __name__ == "__main__":
    main() 