#!/usr/bin/env python3
import asyncio
import argparse
import logging
import os
import json
from datetime import datetime
from enhanced_site_analyzer import EnhancedSiteAnalyzer

async def analyze_sites(urls: list, output_dir: str = "data", verbose: bool = True):
    """Анализ списка сайтов"""
    os.makedirs(output_dir, exist_ok=True)
    
    async with EnhancedSiteAnalyzer(verbose=verbose) as analyzer:
        for url in urls:
            try:
                results = await analyzer.analyze_site(url)
                
                # Сохранение результатов
                domain = url.split('//')[1].split('/')[0]
                timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                filename = f"{domain}_{timestamp}.json"
                filepath = os.path.join(output_dir, filename)
                
                with open(filepath, 'w', encoding='utf-8') as f:
                    json.dump(results, f, ensure_ascii=False, indent=2)
                
                logging.info(f"Analysis completed for {url}")
                logging.info(f"Found {len(results['categories'])} categories")
                logging.info(f"Found {len(results['products'])} products")
                logging.info(f"Results saved to {filepath}")
                
            except Exception as e:
                logging.error(f"Error analyzing {url}: {str(e)}")

def main():
    parser = argparse.ArgumentParser(description='Enhanced Site Analyzer CLI')
    parser.add_argument('urls', nargs='+', help='URLs to analyze')
    parser.add_argument('-o', '--output', default='data', help='Output directory')
    parser.add_argument('-v', '--verbose', action='store_true', help='Enable verbose output')
    
    args = parser.parse_args()
    asyncio.run(analyze_sites(args.urls, args.output, args.verbose))

if __name__ == '__main__':
    main() 