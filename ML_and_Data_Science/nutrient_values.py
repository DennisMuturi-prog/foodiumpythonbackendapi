import pandas as pd
import spacy
import ast
import re
import numpy as np
from textblob import Word
from fractions import Fraction

import os

cwd = os.getcwd()
print('current working directory',cwd)


def singularize(word):
  return Word(word).singularize()
food_densities=pd.read_excel('./datasets/density_DB_v2_0_final-1__1_.xlsx',
                             sheet_name='Density DB')
nlp_ner = spacy.load("./datasets/ML Models/model-best-nlp-ner/model-best")
def calculateStringLength(row):
  if pd.isna(row):
    return 0
  return len(row)
food_densities['stringLength']=food_densities['Food name and description'].apply(calculateStringLength)
food_nutrients=pd.read_csv('./datasets/food_with_nutrients.csv')
myarray=[2,1,23,24,46,61,76,146,151,176,180,150,207,208,201,210,211,215]
wantedColumns=[]
all_colums=food_nutrients.columns
for pos in myarray:
  wantedColumns.append(all_colums[pos-1])
nutrientArray=wantedColumns[2:]
food_nutrients=food_nutrients.copy()[wantedColumns]
food_nutrients = food_nutrients.iloc[10:]
food_nutrients['stringLength']=food_nutrients['description'].apply(calculateStringLength)
def frac2string(s):
    i, f = s.groups(0)
    f = Fraction(f)
    return str(int(i) + float(f))
def getMasses(portion):
  if not '(' in portion:
    return 'nothing found'
  splitWord=portion.split('(')
  number_and_unit_unsplit=splitWord[1].split(')')
  number_and_unit=number_and_unit_unsplit[0].split(' ')
  print(number_and_unit)
  if len(number_and_unit)<2:
    return 'nothing found'
  return {'number':number_and_unit[0],'unit':number_and_unit[1]}
def extract_floats(input_string):
    # Regular expression to match floating-point numbers
    floats = re.findall(r'\d+\.\d+', input_string)

    # Convert the matched strings to floats
    float_list = [float(num) for num in floats]

    return float_list
def getNumbersAndUnits(proportion):
  numbers = [float(i) for i in proportion.split() if i.isdigit()]
  if len(numbers)==0:
    numbers=extract_floats(proportion)
  portions=nlp_ner(proportion)
  unitsList=[]
  ingredientsList=[]
  for ent in portions.ents:
    if ent.label_=='UNIT':
      unitsList.append(ent.text)
    if ent.label_=='INGREDIENT':
      ingredientsList.append(ent.text)
  print('ingredients',ingredientsList)
  if len(ingredientsList)==0:
    proportionSplitted=proportion.split(' ')
    lenOfProportionSplitted=len(proportionSplitted)
    ingredientsList.append(proportionSplitted[lenOfProportionSplitted-1])
  if '(' in ingredientsList[0] and not ')' in ingredientsList[0]:
    ingredientsList[0]=ingredientsList[0]+')'
  return {'numbers':numbers,'units':unitsList,'ingredients':ingredientsList}

def findMatches(ingredient,proportion):
  foodDensityMatch=food_densities[food_densities['Food name and description'].str.contains(ingredient,case=False)]
  foodNutrientMatch=food_nutrients[food_nutrients['description'].str.contains(ingredient,na=False,case=False)]
  if len(foodDensityMatch)>0 and len(foodNutrientMatch)>0:
    return {'densityMatch':foodDensityMatch,'nutrientMatch':foodNutrientMatch}
  singularFormIngredient=singularize(ingredient)
  split_words=proportion.split(' ')
  positionOfLastSplitIndex=len(split_words)-1
  positionOfSecondLastSplitIndex=positionOfLastSplitIndex-1
  if len(foodDensityMatch)==0:
    foodDensityMatch=food_densities[food_densities['Food name and description'].str.contains(singularFormIngredient,case=False)]
    if len(foodDensityMatch)==0 and not ')' in split_words[positionOfLastSplitIndex] and not '(' in split_words[positionOfLastSplitIndex]:
      foodDensityMatch=food_densities[food_densities['Food name and description'].str.contains(split_words[positionOfLastSplitIndex],case=False)]
      if len(foodDensityMatch)==0 and not ')' in split_words[positionOfSecondLastSplitIndex] and not '(' in split_words[positionOfSecondLastSplitIndex]:
        foodDensityMatch=food_densities[food_densities['Food name and description'].str.contains(split_words[positionOfSecondLastSplitIndex],case=False)]

  if len(foodNutrientMatch)==0:
    foodNutrientMatch=food_nutrients[food_nutrients['description'].str.contains(singularFormIngredient,na=False,case=False)]
    if len(foodNutrientMatch)==0 and not ')' in split_words[positionOfLastSplitIndex] and not '(' in split_words[positionOfLastSplitIndex]:
      foodNutrientMatch=food_nutrients[food_nutrients['description'].str.contains(split_words[positionOfLastSplitIndex],na=False,case=False)]
      if len(foodNutrientMatch)==0 and not ')' in split_words[positionOfSecondLastSplitIndex] and not '(' in split_words[positionOfSecondLastSplitIndex]:
        foodNutrientMatch=food_nutrients[food_nutrients['description'].str.contains(split_words[positionOfSecondLastSplitIndex],na=False,case=False)]
  return {'densityMatch':foodDensityMatch,'nutrientMatch':foodNutrientMatch}
volumes={
    'c.':250.000,
    'Tbsp.':14.7868,
    'tsp.':4.9829,
    'qt.':950.0000

}
masses={
    'oz.':28.3495,
    'lb':453.592
}
def populateNutrientValues(row):
  try:
    ingredientProportions=row
    ingredientProportions=[re.sub(r'(?:(\d+)[-\s])?(\d+/\d+)', frac2string, s) for s in ingredientProportions]
    nutrientValues=np.zeros(16,dtype=float)
    accuracy='results:'
    for idx,proportion in enumerate(ingredientProportions):
      all_parameters=getNumbersAndUnits(proportion)
      matches=findMatches(all_parameters['ingredients'][0],proportion)
      if len(matches['nutrientMatch'])==0:
        foodNutrient=np.zeros(16,dtype=float)
        nutrientValues+=foodNutrient
        accuracy+='nutrient value not found'
        continue
      elif len(matches['densityMatch'])==0 and len(matches['nutrientMatch'])>0:
        indexfoodNutrient=matches['nutrientMatch']['stringLength'].idxmin()
        foodNutrient=food_nutrients.iloc[indexfoodNutrient][food_nutrients.columns.difference(['description','stringLength','fdc_id'],sort=False)].fillna(0).to_numpy(dtype='float32')
        nutrientValues+=foodNutrient
        accuracy+='density value not found'
        continue
      extracted_masses=getMasses(proportion)
      foodDensity=food_densities.iloc[matches['densityMatch']['stringLength'].idxmin()]['Density in g/ml (including mass and bulk density)']
      # print('food density before',foodDensity)
      if(not foodDensity):
        foodDensity=food_densities.iloc[matches['densityMatch']['stringLength'].idxmin()]['Specific Gravity']
      if pd.isna(foodDensity):
        foodDensity=matches['densityMatch'].iloc[0]['Density in g/ml (including mass and bulk density)']
        if pd.isna(foodDensity):
          foodDensity=1
      fdfood=food_nutrients.iloc[matches['nutrientMatch']['stringLength'].idxmin()]
      print('nutrient value',fdfood)
      foodNutrient=food_nutrients.iloc[matches['nutrientMatch']['stringLength'].idxmin()][food_nutrients.columns.difference(['description','stringLength','fdc_id'],sort=False)].fillna(0).to_numpy(dtype='float32')
      if not np.any(foodNutrient):
        newQuery=matches['nutrientMatch'].iloc[0][food_nutrients.columns.difference(['description','stringLength','fdc_id'],sort=False)]
        foodNutrient=newQuery.fillna(0).to_numpy(dtype='float32')
        # print('i was ttriggered',foodNutrient)
      print(foodNutrient)
      if extracted_masses!='nothing found':
        if extracted_masses['unit'] in masses:
          foodNutrient=foodNutrient*(float(extracted_masses['number'])*masses[extracted_masses['unit']])/100
        # print('after calc simple case',foodNutrient)
        nutrientValues+=foodNutrient
        # print('simple case final',nutrientValues)
        continue
      if len(all_parameters['numbers'])>0 and len(all_parameters['units'])>0:
        if all_parameters['units'][0] in volumes:
          if isinstance(foodDensity,str) and '-' in foodDensity:
            foodDensity=foodDensity.split('-')[0]
          foodNutrient=foodNutrient*(float(foodDensity)*volumes[all_parameters['units'][0]]*all_parameters['numbers'][0])/100
          # print('after complex calc  case',foodNutrient)
          nutrientValues+=foodNutrient
          # print('complex case final',nutrientValues)
          continue
      nutrientValues+=foodNutrient
      # print('without calculations',nutrientValues)
    return dict(zip(nutrientArray, nutrientValues))

  except:
    print('error in populate nutrients at:')
    return {column: 0.0 for column in wantedColumns}

# def searchFood(searchQuery:str):
#   return recipe_data[recipe_data['title']==searchQuery]
 
if __name__=='__main__':
  # print(searchFood('No-Bake Nut Cookies'))
  print('main')
  