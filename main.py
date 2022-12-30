import random
import math
import csv
import cherrypy
import json
import os
import logging
import wikipedia

from jinja2 import Environment, FileSystemLoader
from data.countryContinentTuple import countriesToContinents
from data.insults import insults
from data.compliments import compliments

# Set up a logger
logger = logging.getLogger(__name__)
logger.setLevel(logging.DEBUG)

# Create a file handler to write log messages to a file
file_handler = logging.FileHandler('cherrypy.log')
file_handler.setLevel(logging.DEBUG)

# Create a formatter for the log messages
formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')

# Add the formatter to the file handler
file_handler.setFormatter(formatter)

# Add the file handler to the logger
logger.addHandler(file_handler)

#setting up jinja
env = Environment(loader=FileSystemLoader('templates'))

# Variables
numTries = 3
complimentValue = 4000
insultValue = 200
difficultyCities = 206
decayValue = 5
maxScore = 5000
cities = []
questionCities = []
isMiles = True

class DistanceDuelGame(object):
    def __init__(self):
        # Define a variable within the __init__ method
        self.city1 = None
        self.city2 = None
        self.city3 = None
        self.city4 = None
        self.numDuels = 0
        self.score = 0
        self.continent1 = None
        self.continent2 = None
        self.name = ""
        self.cityFound = True
        self.duplicateContinent = False

    @cherrypy.expose
    def index(self):
        self.populateCitiesList()
        self.gatherQuestionCities()
        template = env.get_template('getName.html')
        return template.render(high_scores=self.get_high_scores())

    def get_city_info(self, city_name, city_country):
       try:
           search_list=wikipedia.search(f"{city_name}, {city_country}")
           logger.debug(f"{search_list}")
           search_term=search_list.pop(0)
           logger.debug(f"New search term is: {search_term}")
           page = wikipedia.page(search_term,auto_suggest=False)
           logger.debug(f"Page contents: {page}")
           summary = wikipedia.summary(search_term, sentences=7, auto_suggest=False)
           return {
               'title': page.title,
               'url': page.url,
               'summary': summary
           }
       except wikipedia.DisambiguationError:
           logger.debug(f"Disambiguation error triggered on {search_term}")
           return {
               'title': '',
               'url': '',
               'summary': ''
           }
       except wikipedia.exceptions.PageError:
           return {
               'title': '',
               'url': '',
               'summary': ''
           }

    def format_population(self, num):
        # Convert the number to a string and reverse it
        num = str(num)[::-1]

        # Initialize an empty result string
        result = ""

        # Iterate through the characters in the number
        for i, c in enumerate(num):
            # Add the character to the result string
            result += c

            # If the current character is the third character from the end (i.e. the hundred place)
            # and the number has more than three characters, add a comma
            if i == 2 and len(num) > 3:
                result += ","

            # If the current character is the sixth character from the end (i.e. the thousand place)
            # and the number has more than six characters, add a comma
            if i == 5 and len(num) > 6:
                result += ","

            # If the current character is the ninth character from the end (i.e. the million place)
            # and the number has more than nine characters, add a comma
            if i == 8 and len(num) > 9:
                result += ","

        # Reverse the result string and return it
        return result[::-1]

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
                country_iso3 = row[6]
                city_id=row[10]

                # Check if the city has already been added
                if city_id not in added_cities:
                    # Create a tuple with the values for city_id, city_ascii, lat, lng,
                    # country, country_iso3, population
                    if (row[9] != ""):
                        population = row[9].split(".")
                        city = (row[10], row[1], float(row[2]), float(row[3]), row[4],row[6],int(population[0]))
                    # Add the tuple to the list
                    cities.append(city)

                    # Add the city name to the dictionary
                    added_cities[city_id] = country

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
                country_iso3 = row[6]
                city_id=row[10]

                # Check if the city has already been added
                if city_id not in added_cities:
                    # Create a tuple with the values for city_id, city_ascii, lat, lng,
                    # country, country_iso3, population
                    if (row[9] != ""):
                        population = row[9].split(".")
                        city = (row[10], row[1], float(row[2]), float(row[3]), row[4],row[6],int(population[0]))
                    # Add the tuple to the list
                    questionCities.append(city)

                    # Add the city name to the dictionary
                    added_cities[city_id] = country

    @cherrypy.expose
    def distance(self, lat1, lon1, lat2, lon2):
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
        else:
            1.609344 * (R * c)

    @cherrypy.expose
    def cityPicker(self, topCities):
        random_index = random.randint(0, topCities)
        random_index2 = random.randint(0, topCities)
        while random_index == random_index2:
            random_index2 = random.randint(0, topCities)
        return questionCities[random_index], questionCities[random_index2]

    @cherrypy.expose
    def getContinent(self, country):
        return countriesToContinents.get(country, "ERROR1")

    @cherrypy.expose
    def listSearch(self, cityName):
        locationMatches = []
        for city in cities:
            if (len(cityName) >= 5):
                if (cityName.lower() in city[1].lower()):
                    locationMatches.append(city)
            elif cityName.lower() == city[1].lower():
                locationMatches.append(city)
        return locationMatches

    @cherrypy.expose
    def collectCities(self, cityName):
        logger.debug(f"cityName: {cityName}")
        cityMatches = self.listSearch(cityName.strip())
        logger.debug(f"cityName: {cityName}, cityMatches: {cityMatches}")
        if len(cityMatches) == 0:
         return None
        # if (len(cityMatches) == 1):
        # print(f"------> You selected {cityMatches[0][0]}, {cityMatches[0][3]}")
        return cityMatches[0]
        # for i in range(1, len(cityMatches) + 1):
        #  print(
        #    f"{i}: {cityMatches[i- 1][0]}, {cityMatches[i-1][3]}, with a population of {cityMatches[i-1][4]}"
        #  )
        # selection = ""
        # while not selection.isdigit() or not int(selection) < len(cityMatches) + 1 or not int(selection) > 0:
        #  selection = input("Please select a match from the list above, using only the number given: ")
        # print(f"------> You selected {cityMatches[int(selection) - 1][0]}, {cityMatches[int(selection) - 1][3]}")
        # return cityMatches[int(selection) - 1]

    @cherrypy.expose
    def validContinent(self, continent1, continent2, city):
        continent = countriesToContinents.get(city[4], "ERROR")
        return (continent != continent1 and continent != continent2)

    @cherrypy.expose
    def addToScore(self, originalDistance, diffDistance):
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
    def get_high_scores(self):
        high_scores = []
        with open("data/highScores.csv", "r") as csvfile:
            reader = csv.reader(csvfile)
            for row in reader:
                high_scores.append((row[0], row[1]))
            high_scores.sort(key=lambda x: int(x[1]), reverse=True)
        return high_scores[:5]

    @cherrypy.expose
    def add_score_to_database(self, name, score):
        with open("data/highScores.csv", "a") as csvfile:
            writer = csv.writer(csvfile)
            writer.writerow([name, score])

    @cherrypy.expose
    def gatherName(self, name=None):
        if (name == None or len(name) != 3):
            template = env.get_template('getName.html')
            return template.render()
        else:
            self.name = name.upper()
            return self.nextRound()

    @cherrypy.expose
    def distanceCheck(self, cityName1=None, cityName2=None):
        if (not self.validateSelections(cityName1, cityName2)):
            cities_json = json.dumps(cities)
            template = env.get_template('duelQuestion.html')
            city1_title, city1_url, city1_summary = self.get_city_info(self.city1[1], self.city1[4]).values()
            city2_title, city2_url, city2_summary = self.get_city_info(self.city2[1], self.city2[4]).values()
            return template.render(cities_json=cities_json, city1=self.city1, city1_pop=self.format_population(self.city1[6]), city1_summary=city1_summary, city2=self.city2, city2_pop=self.format_population(self.city2[6]), city2_summary=city2_summary, city1_country_iso3=self.city1[5], city2_country_iso3=self.city2[5], continent1 = self.continent1, continent2 = self.continent2, cherrypy=cherrypy, duplicateContinent = self.duplicateContinent, cityFound = self.cityFound)
        logger.debug(f"city2: {self.city2}")
        logger.debug(f"city3: {self.city3}")
        logger.debug(f"city4: {self.city4}")
        distance1 = self.distance(self.city1[2], self.city1[3], self.city2[2], self.city2[3])
        distance2 = self.distance(self.city3[2], self.city3[3], self.city4[2], self.city4[3])
        # Calculate difference between distances
        diff = abs(distance1 - distance2)
        self.numDuels = self.numDuels + 1
        duelScore = self.addToScore(distance1, diff)
        self.score = self.score + duelScore
        feedback = self.decideOnFeedback(duelScore)
        distanceMeasure = ""
        needToReset = False
        if self.numDuels < numTries:
            template = env.get_template('notFinalDuelResults.html')

        else:
            self.add_score_to_database(self.name,self.score)
            template = env.get_template('finalDuelResults.html')
            needToReset = True

        if (isMiles):
            distanceMeasure = "miles"

        else:
            distanceMeasure = "Kilometers"

        html = template.render(numDuels=self.numDuels, duelScore=duelScore, score=self.score, city1=self.city1, city2=self.city2, distance1=format(distance1, '.2f'),
        distanceMeasure="kilometers", city3=self.city3, city4=self.city4, distance2=format(distance2, '.2f'), duelsLeft= (numTries - self.numDuels), feedback=feedback, high_scores=self.get_high_scores())

        if (needToReset):
            self.name = ""
            self.score = 0
            self.city1 = None
            self.city2 = None
            self.city3 = None
            self.city4 = None
            self.continent1 = None
            self.continent2 = None
            self.numDuels = 0
            needToReset = False
            self.duplicateContinent = False
            self.cityFound = True

        return html

    @cherrypy.expose
    def nextRound(self):
        self.city1, self.city2 = self.cityPicker(difficultyCities)
        logger.debug(f"city1: {self.city1}")
        self.continent1 = countriesToContinents.get(self.city1[4], "ERROR1")
        self.continent2 = countriesToContinents.get(self.city2[4], "ERROR2")

        # Convert the list of cities to a JSON string
        cities_json = json.dumps(cities)

        template = env.get_template('duelQuestion.html')
        city1_title, city1_url, city1_summary = self.get_city_info(self.city1[1], self.city1[4]).values()
        city2_title, city2_url, city2_summary = self.get_city_info(self.city2[1], self.city2[4]).values()
        return template.render(cities_json=cities_json, city1=self.city1, city1_pop=self.format_population(self.city1[6]), city1_summary=city1_summary, city2=self.city2, city2_pop=self.format_population(self.city2[6]), city2_summary=city2_summary, city1_country_iso3=self.city1[5], city2_country_iso3=self.city2[5], continent1 = self.continent1, continent2 = self.continent2, duplicateContinent = False, cherrypy=cherrypy, cityFound = True)

    @cherrypy.expose
    def validateSelections(self, cityName1, cityName2):
        self.city3 = self.collectCities(cityName1)
        self.city4 = self.collectCities(cityName2)
        if (self.city3 == None or self.city4 == None):
            self.cityFound = False
            return False
        elif (not self.validContinent(self.continent1, self.continent2, self.city3) or not self.validContinent(self.continent1, self.continent2, self.city4)):
            self.duplicateContinent = True
            return False
        self.cityFound = True
        self.duplicateContinent = False
        return True

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


conf={
      "/static": {
               'tools.staticdir.on': True,
               'tools.staticdir.dir': os.path.abspath("./static")
               }
	}



# Set up CherryPy to use the logger
cherrypy.log.access_log.propagate = False
cherrypy.log.error_log.propagate = False
cherrypy.log.screen = False
cherrypy.log.access_log.addHandler(file_handler)
cherrypy.log.error_log.addHandler(file_handler)

cherrypy.server.socket_host = '0.0.0.0'
cherrypy.quickstart(DistanceDuelGame(),config=conf)
