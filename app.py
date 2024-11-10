# Server side code
from flask import Flask, render_template, jsonify, request, redirect, session, flash, url_for
import sqlite3
from flask_cors import CORS
import mysql.connector
import requests
import updateWeather
import json
from datetime import datetime, timedelta
from collections import defaultdict
import os

# creates a Flask object that represents the web application
app = Flask(__name__)

#Local MYSQL details 
database_config = {
    'host': 'localhost',
    'username': 'root',
    'password': '',
    'database': 'wtax'
}

# Route for the home page
@app.route('/')
def home():
    #renders the HTML template and send response to client
    return render_template('home.html') 

#Triggered when user searches for weather
@app.route('/get_weather_info', methods=['POST'])
def get_weather_info():
    # get form data
    location = request.form.get('location')
    forecast_type = request.form.get('forecast_type')
    
    #converted_location is the location in the form city, country
    converted_location = location 
    
    result = 1 #indicates a valid location request from user
    
    # Check if location exists in the location_coords table
    if location_exists(location) == False: #location not in location_coords table
        #either location is a new location entry or badly formatted which can be corrected
        
        #get converted location and coords 
        result = get_converted_loc_and_coords_from_api(location) 
        
        if result != 0: #valid location request by user
            converted_location, latitude, longitude = result
            if location_exists(converted_location) == False:
                #converted_location also not in location_coords
                
                #add converted_location and coords to database
                add_location_and_coords_to_location_coords(converted_location, latitude, longitude)
                
                #add weather info to weather table
                updateWeather.updateSingleWeather(converted_location, latitude, longitude)

    # getting the weather data to the user
    data = []
    if result != 0: #valid location request
        if forecast_type =="five_days":
            data = get_weather_data_from_db_5_days(converted_location)
        else:
            data = get_weather_data_from_db_2_days(converted_location)
            
        #send the requested converted location
        data.append({'converted_location': converted_location})
        
    else: #invalid location request
        data.append({"converted_location": ""}) #used as an error check
    
    # Return as a JSON response back to the client
    return jsonify(data)
    
def get_weather_data_from_db_2_days(location):
    # Get the current datetime in UTC
    current_datetime = datetime.now()
    
    end_datetime = current_datetime + timedelta(hours=48) #2days

    # Connect to the MySQL server
    conn = mysql.connector.connect(**database_config)
    
    # Create a cursor object to execute SQL queries
    cursor = conn.cursor()

    # Execute the SQL query (within 2 days)
    query = "SELECT * FROM weather WHERE location = %s AND (date > %s OR (date = %s AND time >= %s)) AND (date < %s OR (date = %s AND time <= %s)) "
    cursor.execute(query, (location, current_datetime.date(), current_datetime.date(), current_datetime.time(),
                           end_datetime.date(), end_datetime.date(), end_datetime.time()))
    
    # Fetch all rows
    rows = cursor.fetchall()
    
    # Close the cursor and connection
    cursor.close()
    conn.close()

    # Convert rows to a list of dictionaries
    results = []
    for row in rows:
        result = {
            'date': str(row[1]),
            'time': str(row[2]),
            'temp': float(row[3]),
            'precipitation': float(row[4]),
            'humidity': float(row[5]),
            'wind_speed': float(row[6]),
            'description': row[7],
        }
        results.append(result)

    return results

def get_weather_data_from_db_5_days(location):
    # Get the current datetime in UTC
    current_datetime = datetime.now()
    
    end_datetime = current_datetime + timedelta(hours=120) #5days
    
    # Connect to the MySQL server
    conn = mysql.connector.connect(**database_config)
    
    # Create a cursor object to execute SQL queries
    cursor = conn.cursor()
    
    # Execute the SQL query (within 5 days)
    query = "SELECT * FROM weather WHERE location = %s AND (date > %s OR (date = %s AND time >= %s)) AND (date < %s OR (date = %s AND time <= %s)) "
    cursor.execute(query, (location, current_datetime.date(), current_datetime.date(), current_datetime.time(),
                           end_datetime.date(), end_datetime.date(), end_datetime.time()))

    # Fetch all rows
    rows = cursor.fetchall()
    
    # Close the cursor and connection
    cursor.close()
    conn.close()

    #get only the temp and date variables
    results = []
    for row in rows:
        result = {
            'date': str(row[1]),
            'temp': float(row[3])
        }
        results.append(result)

    # dictionary to store the minimum and maximum temperature for each date
    temp_data = defaultdict(lambda: {'minTemp': float('inf'), 'maxTemp': float('-inf')})

    # Iterate over the result list to find the minimum and maximum temperature for each date
    for item in results:
        date = item['date']
        temperature = item['temp']
        temp_data[date]['minTemp'] = min(temp_data[date]['minTemp'], temperature)
        temp_data[date]['maxTemp'] = max(temp_data[date]['maxTemp'], temperature)

    # Convert the dictionary to the desired list format
    final_result = [{'date': date, 'minTemp': data['minTemp'], 'maxTemp': data['maxTemp']} for date, data in temp_data.items()]
    return final_result

def add_location_and_coords_to_location_coords(location, latitude, longitude):
    # Connect to the MySQL server
    conn = mysql.connector.connect(**database_config)
    
    # Create a cursor object to execute SQL queries
    cursor = conn.cursor()
    
    # Prepare the SQL query
    query = "INSERT INTO location_coords (location, lat, lon) VALUES (%s, %s, %s)"
    
    # Execute the query with the location, latitude, and longitude values as parameters
    cursor.execute(query, (location, latitude, longitude))
    
    # Commit the changes to the database
    conn.commit()
    
    # Close the cursor and connection
    cursor.close()
    conn.close()

# Returns the converted_location, latitude and longitude
def get_converted_loc_and_coords_from_api(location):
    # get latitude and longitude using geocoding 
    
    #access api key
    with open('config.json', 'r') as file:
        api_keys = json.load(file)

    google_api_key = api_keys["google_api_key"]
    
    # Google geocoding API with the api key
    api_url = "https://maps.googleapis.com/maps/api/geocode/json?address={}&key={}".format(location, google_api_key)

    # Fetch data from the API
    response = requests.get(api_url)
    
    data = response.json()

    # Check if data retrieval was successful
    if data["status"] == "OK":

        #break down the main json data
        res = data["results"][0]
        
        #latitude and longitude
        coords = res["geometry"]["location"]
        lat = coords["lat"]
        lon = coords["lng"]
        
        #get the actual city and country and get the converted location
        city, country = "", ""
        for address in res["address_components"]:
            if address["types"] == ["locality", "political"]:
                city = address["long_name"]
            if address["types"] == [ "country", "political" ]:
                country = ", " + address["long_name"]
                
        if city != "": #valid city
            location = city+country
            return [location, lat, lon]
        else:
            #no city was requested
            print("Enter a city")
            return 0
    
    else: #error- bad search
        print("Error:", data["status"])
        return 0

# check if this location is in the database (location_coords table)
def location_exists(location):
    # Connect to the MySQL server
    conn = mysql.connector.connect(**database_config)
    
    # Create a cursor object to execute SQL queries
    cursor = conn.cursor()
    
    # Prepare the SQL query
    # the queury returns the number of rows
    query = "SELECT COUNT(*) FROM location_coords WHERE location = %s"
    
    # Execute the query with the location value as parameter
    cursor.execute(query, (location,))
    
    # Fetch the result
    result = cursor.fetchone()
    
    # Close the cursor and connection
    cursor.close()
    conn.close()
    
    # Check if the count is greater than 0
    if result[0] > 0:
        return True
    else:
        return False

if __name__ == '__main__':
    app.run(debug=True) #call the flask app and use with debugger