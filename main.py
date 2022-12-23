import random
import math
import csv
import cherrypy
import json

from data.countryContinentTuple import countriesToContinents
from data.insults import insults
from data.compliments import compliments

numTries = 3
complimentValue = 4000
insultValue = 200
difficultyCities = 206
decayValue = 5
maxScore = 5000
name = ""
cities = []
questionCities = []
score = 0
city1 = None
city2 = None
city3 = None
city4 = None
continent1 = None
continent2 = None
numDuels = 0
isMiles = True

class DistanceDuelGame(object):
  
  @cherrypy.expose
  def index(self):
    self.populateCitiesList()
    self.gatherQuestionCities()
    return """
        <html>
            <body>
                <form method="get" action="gatherName">
                    <input type="text" name="name"/>
                    <button type="submit">Submit 3 Letter Name</button>
                </form>
            </body>
        </html>
    """
  


  def populateCitiesList(self):
    # Open the CSV file in read mode
    with open("data/worldcities.csv", "r") as file:
      # Create a CSV reader object
      reader = csv.reader(file)
    
      # Skip the first row (header row)
      next(reader)
    
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
 
  def gatherQuestionCities(self):
    with open("data/worldcities3.csv", "r") as file:
      # Create a CSV reader object
      reader = csv.reader(file)
    
      # Skip the first row (header row)
      next(reader)
    
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
 
  @cherrypy.expose
  def distance(self,lat1, lon1, lat2, lon2):
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
    if isMiles:
      return R * c
    else: 1.609344 * (R * c)
  
  @cherrypy.expose  
  def cityPicker(self,topCities):
    random_index = random.randint(0, topCities)
    random_index2 = random.randint(0, topCities)
    while random_index == random_index2:
      random_index2 = random.randint(0, topCities)
    return questionCities[random_index], questionCities[random_index2]
  
  @cherrypy.expose  
  def getContinent(self,country):
    return countriesToContinents.get(country, "ERROR1")
  
  @cherrypy.expose  
  def listSearch(self,cityName):
    locationMatches = []
    for city in cities:
      if (len(cityName) >= 5):
        if (cityName in city[0].lower()):
          locationMatches.append(city)
      elif cityName == city[0].lower():
        locationMatches.append(city)
    return locationMatches
  
  @cherrypy.expose  
  def collectCities(self,cityName):
    cityMatches = self.listSearch(cityName.strip())
    #if len(cityMatches) == 0:
    #  return None
    #if (len(cityMatches) == 1):
      #print(f"------> You selected {cityMatches[0][0]}, {cityMatches[0][3]}")
    return cityMatches[0]
    #for i in range(1, len(cityMatches) + 1):
    #  print(
    #    f"{i}: {cityMatches[i- 1][0]}, {cityMatches[i-1][3]}, with a population of {cityMatches[i-1][4]}"
    #  )
    #selection = ""
    #while not selection.isdigit() or not int(selection) < len(cityMatches) + 1 or not int(selection) > 0:
    #  selection = input("Please select a match from the list above, using only the number given: ")
    #print(f"------> You selected {cityMatches[int(selection) - 1][0]}, {cityMatches[int(selection) - 1][3]}")
    #return cityMatches[int(selection) - 1]
  
  
  @cherrypy.expose
  def validContinent(self,continent1, continent2, city):
    continent = countriesToContinents.get(city[3], "ERROR")
    return (continent != continent1 and continent != continent2)
  
  @cherrypy.expose
  def addToScore(self,originalDistance, diffDistance):
    percentDifferent = (diffDistance + 0.0) / originalDistance
    return int(maxScore * math.exp(-decayValue * percentDifferent))

  @cherrypy.expose  
  def sortHighScores(self):  
    # Read the CSV file
    with open('data/highScores.csv', 'r') as file:
      reader = csv.reader(file)
      rows = [(row[0], int(row[1])) for row in reader]
    # Sort the rows in place in descending order by the second column
    rows.sort(key=lambda row: row[1], reverse=True)
    # Overwrite the original file with the sorted rows
    with open('data/highScores.csv', 'w') as file:
      writer = csv.writer(file)
      writer.writerows(rows)

  @cherrypy.expose
  def printHighScores(self):
    print("The top scores are:")
    print("================================")
    with open('data/highScores.csv', 'r') as file:
      # Read all the lines of the file
      lines = file.readlines()
      # Print the first six lines
      for line in lines[:6]:
        print(line.strip())

  @cherrypy.expose
  def gatherName(self, name=None):
    if (name == None or len(name) != 3):
      return """
        <html>
            <body>
                <form method="get" action="gatherName">
                    <input type="text" name="name"/>
                    <button type="submit"> You submitted a non-3 letter name. Please submit a 3 Letter Name</button>
                </form>
            </body>
        </html>
      """
    else:
      city1, city2 = self.cityPicker(difficultyCities)
      continent1 = countriesToContinents.get(city1[3], "ERROR1")
      continent2 = countriesToContinents.get(city2[3], "ERROR2")
      suggestions_json = json.dumps(cities)
      return f"""
        <html>
        <head>
            <script src="https://code.jquery.com/jquery-3.6.0.min.js"></script>
            <script>
                $(document).ready(function() {{
                    $("#city1").autocomplete({{
                        source: {suggestions_json}
                    }});
                    $("#city2").autocomplete({{
                        source: {suggestions_json}
                    }});
                }});
            </script>
        </head>
        <body>
          <p>
             What are two cities that are approximately the same distance apart as {city1[0]}, {city1[3]} and {city2[0]}, {city2[3]}?"
          </p>
          <form method="get" action="distanceCheck">
             City 1: <input type="text" name="cityName1" />
             <br />
             City 2: <input type="text" name="cityName2" />
             <br />
             <input type="submit" value="Submit" />
             </form>
        </body>
        </html>
      """

  @cherrypy.expose
  def distanceCheck(self, cityName1=None, cityName2=None):
    self.validateSelections(cityName1, cityName2)
    distance1 = self.distance(city1[1], city1[2], city2[1], city2[2])
    distance2 = self.distance(city3[1], city3[2], city4[1], city4[2])
    # Calculate difference between distances
    diff = abs(distance1 - distance2)
    numDuels = numDuels + 1
    duelScore = self.addToScore(distance1, diff)
    score = score + duelScore
    feedback = self.decideOnFeedback(duelScore)
    if numDuels < numTries:
      if isMiles:
        return f"""
            <html>
            <body>
                <h1>Duel {numDuels} Score: {score}</h1>
                <h1>Overall Score: {score}</h1>
                <p>  {city1[0]}, {city1[3]} and {city2[0]}, {city2[3]} were approximately {distance1:.2f} miles apart, while {city3[0]}, {city3[3]} and {city4[0]}, {city4[3]}
                  were approximately {distance2:.2f} miles apart. You have {numTries - numDuels} duels left. </p>
                <form method="post" action="next_round">
                    <input type="submit" value="Next Round">
                </form>
                <p>{feedback}</p>
            </body>
        </html>
        """
      else:
        return f"""
            <html>
            <body>
                <h1>Duel {numDuels} Score: {score}</h1>
                <h1>Overall Score: {score}</h1>
                <p>  {city1[0]}, {city1[3]} and {city2[0]}, {city2[3]} were approximately {distance1:.2f} kilometers apart, while {city3[0]}, {city3[3]} and {city4[0]}, {city4[3]}
                  were approximately {distance2:.2f} kilometers apart. You have {numTries - numDuels} duels left. </p>
                <form method="post" action="gatherName">
                    <input type="submit" value="Next Round">
                </form>
                <p>{feedback}</p>
            </body>
        </html>
        """
    else:
      name = ""
      cities = []
      questionCities = []
      score = 0
      city1 = None
      city2 = None
      city3 = None
      city4 = None
      continent1 = None
      continent2 = None
      numDuels = 0

      return f"""
          <html>
          <body>
              <h1>Duel {numDuels} Score: {score}</h1>
              <h1>Overall Score: {score}</h1>
              <p>  {city1[0]}, {city1[3]} and {city2[0]}, {city2[3]} were approximately {distance1:.2f} kilometers apart, while {city3[0]}, {city3[3]} and {city4[0]}, {city4[3]}
                were approximately {distance2:.2f} kilometers apart. You have no duels left. </p>
                <form method="post" action="index">
                <input type="submit" value="Start Over">
              </form>
          </body>
      </html>
      """


  @cherrypy.expose
  def validateSelections(self, cityName1, cityName2):
    city3 = None
    city4 = None
    while (city3 == None or city4 == None):
      city3 = self.collectCities(cityName1)
      city4 = self.collectCities(cityName2)
      if (city4 == None or city4 == None):
        print("------> ERROR: One of your cities is not in our database. This may be because the name of the city is misspelled, or because we are using a different name of the city. Please try again.")
      elif (not self.validContinent(continent1, continent2, city3) or not self.validContinent(continent1, continent2, city4)):
        print("------> ERROR: One of your cities is on the same continent as a city provided in the question. Please try again.")

  @cherrypy.expose
  def decideOnFeedback(self, addedScore):
    if (addedScore > complimentValue):
      randomIndex = random.randint(0, len(compliments) - 1)
      return (compliments[randomIndex])
    elif (addedScore < insultValue):
      randomIndex = random.randint(0, len(insults) - 1)
      return (insults[randomIndex])
    else:
      return ""


cherrypy.server.socket_host = '0.0.0.0' 
cherrypy.quickstart(DistanceDuelGame())
