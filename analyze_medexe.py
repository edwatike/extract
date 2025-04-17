import asyncio
from site_analyzer import DeepSiteAnalyzer, SecurityProfile
import json
from datetime import datetime
import os
import pickle

# Инициализация файла профилей, если он не существует
if not os.path.exists('security_profiles.pkl'):
    with open('security_profiles.pkl', 'wb') as f:
        pickle.dump({}, f)

async def analyze_medexe():
    print("Начинаем анализ сайта medexe.ru...")
    
    async with DeepSiteAnalyzer() as analyzer:
        # Устанавливаем увеличенное время ожидания для обхода защиты
        result = await analyzer.analyze_site('https://medexe.ru')
        
        # Сохраняем результаты
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"medexe_{timestamp}.json"
        
        with open(filename, 'w', encoding='utf-8') as f:
            json.dump(result, f, ensure_ascii=False, indent=2)
            
        print(f'Анализ завершен. Результаты сохранены в {filename}')
        print('Найдено товаров:', len(result.get('products', [])))
        print('Найдено категорий:', len(result.get('categories', [])))
        
        if result.get('categories'):
            print('\nНайденные категории:')
            for category in result.get('categories', [])[:5]:
                print(f"- {category.get('name', 'Без имени')}")

if __name__ == "__main__":
    asyncio.run(analyze_medexe()) 