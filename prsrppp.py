import asyncio
import aiohttp
from bs4 import BeautifulSoup
from datetime import datetime

async def getHTML(session, url, headers):
    while True:
        try:
            async with session.get(url, headers=headers) as response:
                return await response.text()
        except Exception as er:
            print(f'Ошибка: {er} Время: {datetime.now()}')
            await asyncio.sleep(1)  # Добавляем задержку перед повторной попыткой

async def validationCode(url, headers):
    async with aiohttp.ClientSession() as session:
        i = 0
        run = True
        while run:
            i += 1
            html = await getHTML(session, url, headers)
            soup = BeautifulSoup(html, 'lxml')
            data = soup.find_all('meta')
            print(f'Поиск контента {i}')
            for content in data:
                if '🔴' in str(content) or '🟢' in str(content):
                    run = False
                    return content
    
def prsrpp(url, headers):
    loop = asyncio.get_event_loop()
    content = loop.run_until_complete(validationCode(url, headers))
    return content
        