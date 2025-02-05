from enum import Enum
from fastapi import FastAPI
from .ML_and_Data_Science.glovo_pricing import getAllPricesInfo
from .ML_and_Data_Science.food_recommendation import makePrediction
from .ML_and_Data_Science.nutrient_values import populateNutrientValues
# from ML_and_Data_Science.nutrient_values import testing
from fastapi import HTTPException
from pydantic import BaseModel

class StoreName(str,Enum):
    naivas="naivas"
    quickmart="quickmart"
class RegionName(str,Enum):
    worldwide="Worldwide"
    kenyan="Kenyan"
class PriceRequest(BaseModel):
    names:list[str]
    store:StoreName
class RecommendationRequest(BaseModel):
    ingredientsList:list[str]
    region:RegionName

app=FastAPI()

# @app.get("/")
# def getItems():
#     testingo=testing()
#     print(testingo)
#     return list(testingo)
@app.get("/")
def testing():
    return ['hello','people']
@app.post("/checkAccuracy")
def checkAccuracyValues(ingredients:list[str]):
    nutrientValues=populateNutrientValues(ingredients)
    return nutrientValues
@app.post("/pricing")
async def getPricesInfo(ingredients:PriceRequest):
    try:
        # asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())
        # response= asyncio.run(main(ingredients))
        response= await getAllPricesInfo(ingredients)
        return response
    except Exception as e:
        print('ERROR in getting prices:',e)
        raise HTTPException(status_code=404, detail="Items not found")

    
    
@app.post("/recommendation")
async def getRecommendations(recommendation:RecommendationRequest):
    try:
        response=makePrediction(recommendation.ingredientsList,recommendation.region)
        return response
    except Exception as e:
        print('error in recommendation',e)
        raise HTTPException(status_code=404, detail="predictions for recommendations failed")
        
        
        
        
    
