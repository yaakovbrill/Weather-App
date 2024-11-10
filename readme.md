# Weather App

## Description
The Weather App allows users to check real-time weather information for any city. It utilizes external APIs (Google Maps API & OpenWeatherMap API) to fetch location & weather data and displays it in a user-friendly interface. You can view the website at https://yaakovbrill.pythonanywhere.com/. If you would like to download it locally, then you will need a server environment (Apache) and Python for backend processing. Feel free to continue reading to install the project.

## Prerequisites

Before running the app, ensure the following are installed on your machine:

1. **XAMPP**: 
   - XAMPP provides the necessary server environment, including Apache and optionally MySQL. 
   - [Download XAMPP](https://www.apachefriends.org/index.html)

2. **Python**:
   - Make sure you have Python installed to run the backend of the application. 
   - [Download Python](https://www.python.org/downloads/)

## Setup

### 1. API Keys and Environment Variables
This project requires API keys for external services. You'll need to set up a `config.json` file to store these sensitive credentials securely.

- Create a file named `config.json` in the root directory of the project.
- Add your API keys and other necessary data in the following format:

```json
{
    "google_api_key": "your_api_key_here",
    "weather_api_key": "your_api_key_here"
}
```

Replace "your_api_key_here" with your actual API keys.

### 2. Installation and Running the App

Follow these steps to run the app locally:

1. **Start XAMPP**:
   - Launch the XAMPP Control Panel.
   - Ensure that **Apache** (and **MySQL** if required) are running.

2. **Set up the Python environment**:
   - Open a terminal and navigate to the root directory of the project.

3. **Run the app**:
   - In the terminal, execute the following command to start the app:

     ```bash
     python app.py
     ```

The app should now be accessible locally and ready to fetch weather data.

## Usage
Once the app is running, you can interact with it by entering the desired location (city) to retrieve real-time weather information.
