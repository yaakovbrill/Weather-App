#To create a python executable file, run:
# python -m PyInstaller updateWeatherDaily.py --onefile

import requests
import json
import mysql.connector
from datetime import datetime

#Local MYSQL details 
database_config = {
    'host': 'localhost',
    'username': 'root',
    'password': '',
    'database': 'wtax'
}

# Weather data to be inserted or updated
def updateWeatherData(weather_data):

    # Connect to the MySQL server
    connection = mysql.connector.connect(**database_config)
    cursor = connection.cursor()

    # SQL query to insert or update weather data
    insert_query = """
        INSERT INTO weather (location, date, time, temp, precipitation, humidity, wind_speed, description)
        VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
        ON DUPLICATE KEY UPDATE 
        temp = VALUES(temp),
        precipitation = VALUES(precipitation),
        humidity = VALUES(humidity),
        wind_speed = VALUES(wind_speed),
        description = VALUES(description)
    """

    # Insert or update weather data for each entry
    for entry in weather_data:
        data = (
            entry['location'],
            entry['date'],
            entry['time'],
            entry['temp'],
            entry['precipitation'],
            entry['humidity'],
            entry['wind_speed'],
            entry['description']
        )
        cursor.execute(insert_query, data)

    # Commit the changes to the database
    connection.commit()

    # Close the cursor and connection
    cursor.close()
    connection.close()

def updateSingleWeather(location, lat, lon):
    
    #access api key
    with open('config.json', 'r') as file:
        api_keys = json.load(file)

    weather_api_key = api_keys["weather_api"]
    
    # weather API URL
    api_url = 'https://api.openweathermap.org/data/2.5/forecast?lat={}&lon={}&units=metric&appid={}'.format(lat, lon, weather_api_key)

    # Fetch data from the API
    response = requests.get(api_url)

    # Check if data retrieval was successful
    if response.status_code == 200:
        data = response.json()

        #break down the json data
        data_list = data["list"]
        
        weather_data = []
        # loop over the entire 5 day and 3 hour weather data
        for i in data_list:
            #main data
            main_data = i["main"]
            
            #weather variables
            humidity = main_data["humidity"]
            temp = main_data["temp"]
            description = i["weather"][0]["description"]
            wind_speed = i["wind"]["speed"]
            precipitation = i["pop"]*100 #convert to %
            datetime = i["dt_txt"].split()
            date = datetime[0]
            time = datetime[1]
            
            #weather object
            weather_data.append({'location': location,
            'date': date,
            'time': time,
            'temp': temp,
            'precipitation': precipitation,
            'humidity': humidity,
            'wind_speed': wind_speed,
            'description': description})
            
        # Weather data to be inserted or updated
        updateWeatherData(weather_data)  
    else:
        print('Failed to retrieve data from the API.')
        
# Weather data to be inserted or updated
def getLocationCoords():

    # Connect to the MySQL server
    connection = mysql.connector.connect(**database_config)
    cursor = connection.cursor()

    # Execute the SQL query to fetch all rows from the table
    query = "SELECT * FROM location_coords"
    cursor.execute(query)

    # Fetch all rows
    rows = cursor.fetchall()

    # Close the database connection
    cursor.close()
    connection.close()
    
    return rows

def deleteOldWeather():
    # Connect to the MySQL server
    conn = mysql.connector.connect(**database_config)
    cursor = conn.cursor()

    # Get the current datetime
    current_datetime = datetime.now()

    # Construct the delete query
    query = "DELETE FROM weather WHERE (date < %s) OR (date = %s AND time < %s)"

    # Execute the delete query
    cursor.execute(query, (current_datetime.date(), current_datetime.date(), current_datetime.time().strftime("%H:%M:%S")))

    # Commit the changes to the database
    conn.commit()

    # Close the database connection
    cursor.close()
    conn.close()
    
#delete old weather
deleteOldWeather()
    
#get all locations and coords in the location_coords table
location_coords = getLocationCoords()

#update a single weather location at a time
for row in location_coords:
    location, lat, lon = row  
    updateSingleWeather(location, lat, lon)