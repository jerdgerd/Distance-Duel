import random
import math
from data.countryContinentTuple import countriesToContinents
from data.insults import insults
from data.compliments import compliments
import csv
numTries = 3
complimentValue = 4000
insultValue = 200
difficultyCities = 207
decayValue = .002
maxScore = 5000
# Open the CSV file in read mode
with open("data/worldcities.csv", "r") as file:
  # Create a CSV reader object
  reader = csv.reader(file)

  # Skip the first row (header row)
  next(reader)

  # Create an empty list to store the tuples
  cities = []

  # Create a dictionary to store the names of cities that have already been added
  added_cities = {}

  # Iterate over the rows in the CSV file
  for row in reader:
    # Get the name of the city and the country
    city_name = row[1]
    country = row[4]

    # Check if the city has already been added
    if city_name not in added_cities or added_cities[city_name] != country:
      # Create a tuple with the values for city_ascii, lat, lng, and country
      if (row[9] != ""):
        population = row[9].split(".")
        city = (row[1], float(row[2]), float(row[3]), row[4],
                int(population[0]))
      # Add the tuple to the list
      cities.append(city)

      # Add the city name to the dictionary
      added_cities[city_name] = country

with open("data/worldcities3.csv", "r") as file:
  # Create a CSV reader object
  reader = csv.reader(file)

  # Skip the first row (header row)
  next(reader)

  # Create an empty list to store the tuples
  questionCities = []

  # Create a dictionary to store the names of cities that have already been added
  added_cities = {}

  # Iterate over the rows in the CSV file
  for row in reader:
    # Get the name of the city and the country
    city_name = row[1]
    country = row[4]

    # Check if the city has already been added
    if city_name not in added_cities or added_cities[city_name] != country:
      # Create a tuple with the values for city_ascii, lat, lng, and country
      if (row[9] != ""):
        population = row[9].split(".")
        city = (row[1], float(row[2]), float(row[3]), row[4],
                int(population[0]))
      # Add the tuple to the list
      questionCities.append(city)

      # Add the city name to the dictionary
      added_cities[city_name] = country

def distance(lat1, lon1, lat2, lon2):
  # Function to calculate the distance between two cities in miles
  # using the Haversine formula
  R = 3958.8  # approximate radius of earth in miles

  lat1 = math.radians(lat1)
  lon1 = math.radians(lon1)
  lat2 = math.radians(lat2)
  lon2 = math.radians(lon2)

  dlon = lon2 - lon1
  dlat = lat2 - lat1

  a = math.sin(
    dlat / 2)**2 + math.cos(lat1) * math.cos(lat2) * math.sin(dlon / 2)**2
  c = 2 * math.atan2(math.sqrt(a), math.sqrt(1 - a))

  return R * c


def cityPicker(topCities):
  random_index = random.randint(0, topCities)
  random_index2 = random.randint(0, topCities)
  while random_index == random_index2:
    random_index2 = random.randint(0, topCities)
  return questionCities[random_index], questionCities[random_index2]


def getContinent(country):
  return countriesToContinents.get(country, "ERROR1")


def listSearch(cityName):
  locationMatches = []
  for city in cities:
    if cityName == city[0].lower():
      locationMatches.append(city)
  return locationMatches


def collectCities(cityName):
  cityMatches = listSearch(cityName)
  if len(cityMatches) == 0:
    return None
  if (len(cityMatches) == 1):
    return cityMatches[0]
  for i in range(1, len(cityMatches) + 1):
    print(
      f"{i}: {cityMatches[i- 1][0]}, {cityMatches[i-1][3]}, with a population of {cityMatches[i-1][4]}"
    )
  selection = ""
  while not selection.isdigit() or not int(selection) < len(cityMatches) or not int(selection) > 0:
    selection = input("Please select a match from the list above, using only the number given: ")
  return cityMatches[int(selection) - 1]


def validContinent(continent1, continent2, city):
  continent = countriesToContinents.get(city[3], "ERROR")
  return (continent != continent1 and continent != continent2)

def addToScore(diffDistance):
  return int(maxScore * math.exp(-decayValue * diffDistance))

def main():
  score = 0
  for count in range(0, numTries):
    print("You are on try " + str(count+1) + " of " + str(numTries))
    city1, city2 = cityPicker(difficultyCities)
    continent1 = countriesToContinents.get(city1[3], "ERROR1")
    continent2 = countriesToContinents.get(city2[3], "ERROR2")
    print(
      f"What are two cities that are approximately the same distance apart as {city1[0]}, {city1[3]} and {city2[0]}, {city2[3]}?"
    )
    city3, city4 = None, None
    while (city3 == None or city4 == None):
      cityName = (input("First city: ")).lower()
      city3 = collectCities(cityName)
      cityName = (input("Second city: ")).lower()
      city4 = collectCities(cityName)
      if (city3 == None or city4 == None):
        print("One of your cities is not in our database. This may be because the name of the city is misspelled, or because we are using a different name of the city. Please try again.")
      elif (not validContinent(continent1, continent2, city3) or not validContinent(continent1, continent2, city4)):
        print("One of your cities is on the same continent as a city provided in the question. Please try again.")
        city3 = None
    distance1 = distance(city1[1], city1[2], city2[1], city2[2])
    distance2 = distance(city3[1], city3[2], city4[1], city4[2])
    # Calculate difference between distances
    diff = abs(distance1 - distance2)

    print(
      f"The distance between {city1[0]} and {city2[0]} is {distance1:.2f} miles and the distance between {city3[0]} and {city4[0]} is {distance2:.2f} miles."
      )
    score = score + addToScore(diff)
    print("You scored " + str(score) +" this round!")
    print("Your new total score is "  + str(score))
    if (addToScore(diff) > complimentValue):
      randomIndex = random.randint(0, len(compliments))
      print(compliments[randomIndex])
    elif (addToScore(diff) < insultValue):
      randomIndex = random.randint(0, len(insults))
      print(insults[randomIndex])
    print("\n")
  print("=============================")
  print("Your final score is " + str(score))
if __name__ == "__main__":
  main()
