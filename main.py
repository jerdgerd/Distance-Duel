import random
import math
import csv
import cherrypy
import json
import os
import logging
import wikipedia
import folium
import requests
import nltk


nltk.download('punkt')
from cherrypy.lib import sessions
from jinja2 import Environment, FileSystemLoader, Template
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
difficultyCities = 369
decayValue = 5
maxScore = 5000
cities = []
showMaps = True
openweatherapikey="02cb929956f5c623f3c7552d88638f8d"
generated_numbers = []

class DistanceDuelGame(object):

    @cherrypy.expose
    def resetValues(self):
        session = cherrypy.session
        session['city1'] = []
        session['city2'] = []
        session['city3'] = []
        session['city4'] = []
        session['numDuels'] = 0
        session['score'] = 0
        session['continent1'] = ""
        session['continent2'] = ""
        session['name'] = ""
        session['cityFound'] = True
        session['duplicateContinent'] = False
        session['city1page'] = ''
        session['city2page'] = ''
        session['difficulty'] = 'easy'
        session['isMiles'] = True
        session['timerLength'] = -1
        session['timedOut']=False
        session['isTimed']=False
        session['continentOfPlay']="global"
        session['questionCityFile']=f"data/{session['continentOfPlay']}/questionCities.csv"
        session['scoreId'] = self.generate_unique_number()
        session['guessesList'] = []
        session['questionCities'] = []

    @cherrypy.expose
    def get_weather(self, lat, lon):
        API_KEY = openweatherapikey
        API_ENDPOINT = 'https://api.openweathermap.org/data/2.5/weather'
        params = {
            'lat': lat,
            'lon': lon,
            'appid': API_KEY,
            'units': 'metric'
        }
        response = requests.get(API_ENDPOINT, params=params)
        data = response.json()
        return data

    @cherrypy.expose
    def index(self):
        self.resetValues()
        self.populateCitiesList()
        template = env.get_template('getName.html')
        return template.render(high_scores=self.get_high_scores("data/global/highScores.csv"))

    def get_wiki_page(self, city_name, city_country):
        if city_name != "Male":
            try:
                page = wikipedia.page(city_name,auto_suggest=False)
            except wikipedia.DisambiguationError:
                search_list=wikipedia.search(f"{city_name}, {city_country}")
                logger.debug(f"{search_list}")
                search_term=list(search_list)[0]
                logger.debug(f"New search term is: {search_term}")
                page = wikipedia.page(search_term,auto_suggest=False)
        else:
           search_list=wikipedia.search(f"{city_name}, {city_country}")
           logger.debug(f"{search_list}")
           search_term=list(search_list)[0]
           logger.debug(f"New search term is: {search_term}")
           page = wikipedia.page(search_term,auto_suggest=False)
        return page


    def get_city_info(self, page):
       try:
           summary = page.summary
           summarySentences = nltk.sent_tokenize(summary)
           #Add first 7 sentences to the summary
           summary = ''
           i = 0
           while len(summarySentences) > i and i < 7:
               summary = summary + " " + summarySentences[i]
               i = i + 1
           response  = requests.get('http://en.wikipedia.org/w/api.php?action=query&prop=pageimages&format=json&piprop=original&titles=' + page.title)
           json_data = json.loads(response.text)
           try:
               picture = list(json_data['query']['pages'].values())[0]['original']['source']
           except Exception as e:
               logger.debug(f"Errored out getting picture for {page.title} at {page.url}")
               return {
                   'title': page.title,
                   'url': page.url,
                   'summary': summary,
                   'picture': ''
               }
           return {
               'title': page.title,
               'url': page.url,
               'summary': summary,
               'picture': picture
           }
       except wikipedia.DisambiguationError:
           logger.debug(f"Disambiguation error triggered on {{ page.title }}")
           return {
               'title': '',
               'url': '',
               'summary': '',
               'picture': ''
           }
       except wikipedia.exceptions.PageError:
           return {
               'title': '',
               'url': '',
               'summary': '',
               'picture': ''
           }


    def generate_map_html(self, city1, city2, city3, city4):
      # create a folium map centered at (0, 0)
      map = folium.Map(location=[0, 0], zoom_start=2, tiles='https://server.arcgisonline.com/ArcGIS/rest/services/World_Imagery/MapServer/tile/{z}/{y}/{x}', attr='Tiles &copy; Esri &mdash; Source: Esri, i-cubed, USDA, USGS, AEX, GeoEye, Getmapping, Aerogrid, IGN, IGP, UPR-EGP, and the GIS User Community', scroll_wheel_zoom=False, dragging=False)

      # loop through the array of cities
      for city in [city1, city2, city3, city4]:
        # add a marker for each city
        folium.Marker(location=[city[2], city[3]], popup=city[1]).add_to(map)

      # create an array of colors for the lines
      colors = ['red', 'white']

      # add a line connecting each pair of cities
      folium.PolyLine([city1[2:4], city2[2:4]], color=colors[0], weight=2, opacity=1).add_to(map)
      folium.PolyLine([city3[2:4], city4[2:4]], color=colors[1], weight=2, opacity=1).add_to(map)

      # set the bounding box for the map
      bounds = [[min(city1[2], city2[2], city3[2], city4[2]), min(city1[3], city2[3], city3[3], city4[3])],
                [max(city1[2], city2[2], city3[2], city4[2]), max(city1[3], city2[3], city3[3], city4[3])]]
      map.fit_bounds(bounds)

      # create a Jinja2 template for the map HTML
      template = Template("""
        <div class="map-container">
        <div id="map" class="map"style="width:900px;height:600px;" >
        {{ map_html }}
        </div>
        </div>
      """)

      # render the template and return the HTML
      return template.render(map_html=map.get_root().render())


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
                admin_region = row[7]
                city_id=row[10]

                # Check if the city has already been added
                if city_id not in added_cities:
                    # Create a tuple with the values for city_id, city_ascii, lat, lng,
                    # country, country_iso3, population
                    if (row[9] != ""):
                        population = row[9].split(".")
                        city = (row[10], row[1], float(row[2]), float(row[3]), row[4],row[6],int(population[0]), row[7])
                    # Add the tuple to the list
                    cities.append(city)

                    # Add the city name to the dictionary
                    added_cities[city_id] = country

    def gatherQuestionCities(self, cityFile):
        session = cherrypy.session
        with open(cityFile, "r") as file:
            # Create a CSV reader object
            reader = csv.reader(file)

            # Skip the first row (header row)
            next(reader)
            # Iterate over the rows in the CSV file
            for row in reader:
                logger.debug(f"row: {row}")
                # Get the name of the city and the country
                city_name = row[1]
                country = row[4]
                country_iso3 = row[6]
                city_id=row[10]

                # Create a tuple with the values for city_id, city_ascii, lat, lng,
                # country, country_iso3, population
                if (row[9] != ""):
                    logger.debug(f"population: {row[9]}")
                    population = row[9].split(".")
                    city = (row[10], row[1], float(row[2]), float(row[3]), row[4],row[6],int(population[0]))
                    session['questionCities'].append(city)

    @cherrypy.expose
    def generate_unique_number(self):
        number = random.randint(10000000000, 99999999999)
        while number in generated_numbers:
            number = random.randint(10000000000, 99999999999)
        generated_numbers.append(number)
        return number


    @cherrypy.expose
    def distance(self, lat1, lon1, lat2, lon2, isMiles):
        session = cherrypy.session
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
            return 1.609344 * (R * c)

    @cherrypy.expose
    def cityPicker(self, topCities):
        session = cherrypy.session
        if (session['continentOfPlay']):
            random_index = random.randint(0, len(session['questionCities']))
            random_index2 = random.randint(0, len(session['questionCities']))
            if session['difficulty']  == 'easy':
                maxDistance = 4000
            elif session['difficulty'] == 'medium':
                maxDistance = 8000
            else:
                maxDistance = 30000
            if not session['isMiles']:
                maxDistance = maxDistance * 1.609344
            while (random_index == random_index2 or (self.distance(session['questionCities'][random_index][2], session['questionCities'][random_index][3],
            session['questionCities'][random_index2][2], session['questionCities'][random_index2][3], session['isMiles']) > maxDistance)):
                random_index2 = random.randint(0, len(session['questionCities']))
        else:
            if session['difficulty'] == 'easy':
                maxCities = 35
            elif session['difficulty'] == 'medium':
                maxCities = 80
            elif session['difficulty'] == 'hard':
                maxCities = 200
            random_index = random.randint(0, maxCities)
            random_index2 = random.randint(0, maxCities)
            while random_index == random_index2:
                random_index2 = random.randint(0, maxCities)
        return session['questionCities'][random_index], session['questionCities'][random_index2]

    @cherrypy.expose
    def getContinent(self, country):
        return countriesToContinents.get(country, "ERROR1")

    @cherrypy.expose
    def listSearch(self, cityId):
        locationMatches = []
        for city in cities:
           if cityId == city[0]:
               locationMatches.append(city)
        return locationMatches

    @cherrypy.expose
    def collectCities(self, cityId):
        logger.debug(f"cityId: {cityId}")
        cityMatches = self.listSearch(cityId.strip())
        logger.debug(f"cityId: {cityId}, cityMatches: {cityMatches}")
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
        session = cherrypy.session
        continent = countriesToContinents.get(city[4], "ERROR")
        if (session['continentOfPlay'] == "global"):
            return (continent != continent1 and continent != continent2)
        else:
            play_continent = session['continentOfPlay'].replace('_', ' ').title()
            return (continent != play_continent)

    @cherrypy.expose
    def addToScore(self, originalDistance, diffDistance):
        session = cherrypy.session
        percentDifferent = (diffDistance + 0.0) / originalDistance
        maxModifier = 0
        decayModifier = 1
        if session['difficulty'] == "easy":
            decayModifier = .7
            maxModifier = -1000
        elif session['difficulty'] == "hard":
            difficultyModifier = 1.3
            maxModifier = 1000
        return int(maxScore * math.exp(-(decayValue * decayModifier) * percentDifferent))

    @cherrypy.expose
    def sortHighScores(self, highScoresFile=None):
        # Read the CSV file
        with open(highScoresFile, 'r') as file:
            reader = csv.reader(file)
            rows = [(row[0], int(row[1])) for row in reader]
        # Sort the rows in place in descending order by the second column
        rows.sort(key=lambda row: row[1], reverse=True)
        # Overwrite the original file with the sorted rows
        with open(highScoresFile, 'w') as file:
            writer = csv.writer(file)
            writer.writerows(rows)

    @cherrypy.expose
    def get_high_scores(self, highScoresFile):
        high_scores = []
        with open(highScoresFile, "r") as csvfile:
            reader = csv.reader(csvfile)
            for row in reader:
                high_scores.append((row[0], row[1]))
            high_scores.sort(key=lambda x: int(x[1]), reverse=True)
        return high_scores[:5]

    @cherrypy.expose
    def add_score_to_database(self, name, score, highScoresFile, id):
        with open(highScoresFile, "a") as csvfile:
            writer = csv.writer(csvfile)
            writer.writerow([name, score, id])

    @cherrypy.expose
    def gatherName(self, name=None, difficulty=None, timerLength=None, isMiles=None, continent=None):
        session = cherrypy.session
        if difficulty == None:
            session['difficulty'] = 'medium'
        else:
            session['difficulty'] = difficulty
        if timerLength == "none":
            logger.debug(f"timerLength: {timerLength}")
            session['timerLength'] = -1
            session['isTimed'] = False
        else:
            logger.debug(f"timerLength: {timerLength}")
            session['isTimed']=True
            session['timerLength'] = timerLength
        if isMiles == None:
            session['isMiles'] = True
        else:
            if isMiles == "True":
                session['isMiles'] = True
            elif isMiles == "False":
                session['isMiles'] = False
        if continent == None:
            continent = "global"
        session['continentOfPlay'] = continent
        if (name == None or len(name) != 3):
            template = env.get_template('getName.html')
            return template.render()
        else:
            if (session['isTimed']):
                session['highScoresFile']=f"data/{session['continentOfPlay']}/highScores{session['timerLength']}s.csv"
            else:
                session['highScoresFile']=f"data/{session['continentOfPlay']}/highScores.csv"
            session['questionCityFile']=f"data/{session['continentOfPlay']}/questionCities.csv"
            self.gatherQuestionCities(session['questionCityFile'])
            session['name'] = name.upper()
            return self.nextRound()

    @cherrypy.expose
    def distanceCheck(self, cityName1=None, cityName2=None, cityId1=None, cityId2=None, time_remaining=None):
        session = cherrypy.session
        if (not self.validateSelections(cityId1, cityId2)):
            cities_json = json.dumps(cities)
            template = env.get_template('duelQuestion.html')
            # Grab data from openweather for both cities
            city1weather=self.get_weather(session['city1'][2],session['city1'][3])
            city2weather=self.get_weather(session['city2'][2],session['city2'][3])

            city1_title, city1_url, city1_summary, city1_picture = self.get_city_info(session['city1page']).values()
            city2_title, city2_url, city2_summary, city2_picture = self.get_city_info(session['city2page']).values()
            return template.render(city1weather=city1weather,city2weather=city2weather,cities_json=cities_json, city1=session['city1'], city1_pop=self.format_population(session['city1'][6]),
                city1_summary=city1_summary, city2=session['city2'], city2_pop=self.format_population(session['city2'][6]),
                city2_summary=city2_summary, city1_country_iso3=session['city1'][5], city2_country_iso3=session['city2'][5],
                city1_picture = city1_picture, city2_picture = city2_picture,
                continent1 = session['continent1'], continent2 = session['continent2'], cherrypy=cherrypy,
                duplicateContinent = session['duplicateContinent'], cityFound = session['cityFound'], timeoutDuration = session['timerLength'], timeRemaining = time_remaining, isTimed = session['isTimed'],
                isGlobal=(session['continentOfPlay'] == "global"), continentOfPlay=session['continentOfPlay'].replace('_', ' ').title())

        city1 = session['city1']
        city2 = session['city2']
        city3 = session['city3']
        city4 = session['city4']
        logger.debug(f"city2: {city2}")
        logger.debug(f"city3: {city3}")
        logger.debug(f"city4: {city4}")
        session['numDuels'] = session['numDuels'] + 1

        if session['timedOut']:
            distance1 = 0
            distance2 = 0
            duelScore = 0
        else:
            distance1 = self.distance(city1[2], city1[3], city2[2], city2[3], session['isMiles'])
            distance2 = self.distance(city3[2], city3[3], city4[2], city4[3], session['isMiles'])
            # Calculate difference between distances
            diff = abs(distance1 - distance2)
            duelScore = self.addToScore(distance1, diff)
        session['score'] = session['score'] + duelScore
        feedback = self.decideOnFeedback(duelScore)
        distanceMeasure = ""
        sessionGuess = [city1, city2, city3, city4, duelScore]
        session['guessesList'].append(sessionGuess)
        guessList = session['guessesList']
        needToReset = False
        if session['numDuels'] < numTries:
            template = env.get_template('notFinalDuelResults.html')

        else:
            self.add_score_to_database(session['name'],session['score'],session['highScoresFile'], session['scoreId'])
            template = env.get_template('finalDuelResults.html')
            needToReset = True

        if (session['isMiles']):
            distanceMeasure = "miles"
        else:
            distanceMeasure = "kilometers"

        if session['timedOut']:
            html = template.render(showMaps=False,map_html="",numDuels=session['numDuels'], duelScore=duelScore, score=session['score'], city1=city1, city2=city2, distance1=format(distance1, '.2f'),
            distanceMeasure=distanceMeasure, city3=city3, city4=city4, distance2=format(distance2, '.2f'), duelsLeft= (numTries - session['numDuels']), feedback=feedback, high_scores=self.get_high_scores(session['highScoresFile']), timedOut=session['timedOut'], guess_list=guessList)
        else:
            html = template.render(showMaps=showMaps,map_html=self.generate_map_html(city1,city2,city3,city4),numDuels=session['numDuels'], duelScore=duelScore, score=session['score'], city1=city1, city2=city2, distance1=format(distance1, '.2f'),
            distanceMeasure=distanceMeasure, city3=city3, city4=city4, distance2=format(distance2, '.2f'), duelsLeft= (numTries - session['numDuels']), feedback=feedback, high_scores=self.get_high_scores(session['highScoresFile']), timedOut=session['timedOut'], guess_list=guessList)

        if (needToReset):
            self.resetValues()
            needToReset = False
        return html

    @cherrypy.expose
    def nextRound(self):
        session = cherrypy.session
        session['city1'], session['city2'] = self.cityPicker(difficultyCities)
        logger.debug(f"city1: {session['city1']}")
        session['continent1'] = countriesToContinents.get(session['city1'][4], "ERROR1")
        session['continent2'] = countriesToContinents.get(session['city2'][4], "ERROR2")

        # Convert the list of cities to a JSON string
        cities_json = json.dumps(cities)

        # Grab data from openweather for both cities
        city1weather=self.get_weather(session['city1'][2],session['city1'][3])
        city2weather=self.get_weather(session['city2'][2],session['city2'][3])

        template = env.get_template('duelQuestion.html')
        session['city1page'] = self.get_wiki_page(session['city1'][1], session['city1'][4])
        session['city2page'] = self.get_wiki_page(session['city2'][1], session['city2'][4])
        city1_title, city1_url, city1_summary, city1_picture = self.get_city_info(session['city1page']).values()
        city2_title, city2_url, city2_summary, city2_picture = self.get_city_info(session['city2page']).values()
        logger.debug(f"next round timerLength: {session['timerLength']}")
        return template.render(city1weather=city1weather, city2weather=city2weather, cities_json=cities_json, city1=session['city1'], city1_pop=self.format_population(session['city1'][6]),
            city1_summary=city1_summary, city2=session['city2'], city2_pop=self.format_population(session['city2'][6]), city2_summary=city2_summary,
            city1_country_iso3=session['city1'][5], city2_country_iso3=session['city2'][5], city1_picture = city1_picture, city2_picture = city2_picture,
            continent1 = session['continent1'], continent2 = session['continent2'], duplicateContinent = False, cherrypy=cherrypy, cityFound = True, timeoutDuration = session['timerLength'],timeRemaining = session['timerLength'], isTimed = session['isTimed'],
            isGlobal=(session['continentOfPlay'] == "global"), continentOfPlay=session['continentOfPlay'].replace('_', ' ').title())

    @cherrypy.expose
    def validateSelections(self, cityId1, cityId2):
        session = cherrypy.session
        session['city3'] = self.collectCities(cityId1)
        session['city4'] = self.collectCities(cityId2)
        if (cityId1 == "00000" or cityId2 == "00000"):
            session['timedOut']=True
            session['cityFound'] = True
            session['duplicateContinent'] = False
            return True
        else:
            session['timedOut']=False
        city3 = session['city3']
        city4 = session['city4']
        continent1 = session['continent1']
        continent2 = session['continent2']
        if (city3 == None or city4 == None):
            session['cityFound'] = False
            return False
        elif (not self.validContinent(continent1, continent2, city3) or not self.validContinent(continent1, continent2, city4)):
            session['duplicateContinent'] = True
            return False
        session['cityFound'] = True
        session['duplicateContinent'] = False
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


conf = {
    '/': {
        'tools.sessions.on': True,
    },
    '/static': {
        'tools.staticdir.on': True,
        'tools.staticdir.dir': os.path.abspath('./static'),
    }
}



# Set up CherryPy to use the logger
cherrypy.log.access_log.propagate = False
cherrypy.log.error_log.propagate = False
cherrypy.log.screen = False
cherrypy.log.access_log.addHandler(file_handler)
cherrypy.log.error_log.addHandler(file_handler)

cherrypy.server.socket_host = '0.0.0.0'
cherrypy.quickstart(DistanceDuelGame(), '/', config=conf)
