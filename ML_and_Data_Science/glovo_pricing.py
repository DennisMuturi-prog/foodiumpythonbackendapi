import aiohttp
import asyncio
from bs4 import BeautifulSoup
from concurrent.futures import ThreadPoolExecutor
import re
import json
import redis
redis_client=redis.StrictRedis(host='rediscache.internal.gentledune-9460edf8.southafricanorth.azurecontainerapps.io:6379',port=6379,decode_responses=True)



async def fetch(session,store,itemName):
    """
    Asynchronously fetches the content from a given URL using the provided session.
    """
    url=f"https://glovoapp.com/ke/en/nairobi/{store}-nbo?search={itemName}"
    async with session.get(url) as response:
        content = await response.text()
        # print(f"Fetched URL: {url}")
        return {
            "htmlContent":content,
            "itemName":itemName,
            "store":store,
        }

def parse(fetchResponse):
    soup = BeautifulSoup(fetchResponse['htmlContent'], "lxml")
    ingredientsPart=soup.find_all('script')[9].text
    ingredientsInfo = re.search(r'data:\{title:".*?",.*?elements:\[(.*?)\]\}', ingredientsPart, flags=re.S).group(1)
    ingredientsInfo = re.sub(r'(\d+)n', r'\1', ingredientsInfo)
    ingredientsInfo = ingredientsInfo.replace('https:', 'PLACEHOLDER_HTTPS')
    ingredientsInfo = ingredientsInfo.replace('dh:', 'PLACEHOLDER_DH')
    ingredientsInfo = re.sub(r'(\w+):', r'"\1":', ingredientsInfo)
    ingredientsInfo = f"[{ingredientsInfo}]"
    ingredientsInfo = ingredientsInfo.replace('PLACEHOLDER_HTTPS', 'https:')
    ingredientsInfo = ingredientsInfo.replace('PLACEHOLDER_DH', 'dh:')
    ingredientsInfo = json.loads(ingredientsInfo)
    allPriceInfo={
        "itemName":fetchResponse['itemName'],
        "foundItems":[]
    }
    for item in ingredientsInfo:
        try:
            info={
                "name":item['data']['name'],
                "imageUrl":item['data']['imageUrl'],
                "price":item['data']['price']
            }
            allPriceInfo['foundItems'].append(info)
        except Exception as e:
            print(f"error in parser:{e} {item['data']['name']}")
            continue
    
    allPriceInfo['foundItems'] = allPriceInfo['foundItems'][:5]
    redis_client.setex(f"{fetchResponse['itemName']}:{fetchResponse['store']}",3600*6,json.dumps(allPriceInfo))
    return allPriceInfo

async def getPriceInfo(items):
    """
    Main function to fetch URLs concurrently and parse their HTML content.
    """
    results=[]
    async with aiohttp.ClientSession() as session:
        # Create a list of tasks for fetching URLs
        tasks = [fetch(session,items["store"], url) for url in items["names"]]
        # Gather all responses concurrently
        fetchResponses = await asyncio.gather(*tasks)

        # Use ThreadPoolExecutor to parse HTML content in parallel
        with ThreadPoolExecutor(max_workers=4) as executor:
            results=list(executor.map(parse, fetchResponses))
    return results

async def getAllPricesInfo(items):
    cacheMissItems=[]
    all_goods_prices_info=[]
    for itemName in items.names:
        cacheHit=redis_client.get(f"{itemName}:{items.store}")
        if cacheHit is None:
            cacheMissItems.append(itemName)
            continue
        else:
            print('cache hit')
        all_goods_prices_info.append(json.loads(cacheHit))
    if len(cacheMissItems)==0:
        return all_goods_prices_info
    results_from_slower_path=await getPriceInfo({"store":items.store,"names":cacheMissItems})
    for goodPriceInfo in results_from_slower_path:
        all_goods_prices_info.append(goodPriceInfo)
    return all_goods_prices_info
    

if __name__ == "__main__":
    asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())
    items = [
    {
        "name":'potato',
        "store":'naivas'
    },
    {
        "name":'beans',
        "store":'naivas'
    },
    {
        "name":'flour',
        "store":'naivas'
    },
    
    
    ] 
    final=asyncio.run(getPriceInfo(items))
    print('result:',final)