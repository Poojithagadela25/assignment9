import os
import matplotlib
matplotlib.use('Agg')  # Use non-GUI backend for generating plots
import matplotlib.pyplot as plt
from flask import Flask, request, render_template
import requests
import datetime

# Initialize Flask application
app = Flask(__name__)  # Corrected __name__ here

@app.route('/', methods=['GET', 'POST'])
def weather():
    weather_data = None
    graph_filenames = {}

    if request.method == 'POST':
        city = request.form.get('city')  # Get city input from the user

        # Fetch geolocation (latitude, longitude) for the city
        geocoding_response = requests.get(f'https://geocoding-api.open-meteo.com/v1/search?name={city}')

        if geocoding_response.status_code == 200:
            geocoding_results = geocoding_response.json().get('results', [])
            if geocoding_results:
                location = geocoding_results[0]
                latitude, longitude = location['latitude'], location['longitude']

                # Fetch weather data for the city
                weather_response = requests.get(
                    f'https://api.open-meteo.com/v1/forecast?latitude={latitude}&longitude={longitude}'
                    f'&hourly=temperature_2m,relative_humidity_2m,windspeed_10m,precipitation&timezone=auto'
                )

                if weather_response.status_code == 200:
                    weather_data = weather_response.json()

                    # Generate graphs for multiple weather attributes
                    graph_filenames['temperature'] = generate_graph(
                        weather_data, 'temperature_2m', 'Temperature (°C)', 'Temperature Forecast')
                    graph_filenames['humidity'] = generate_graph(
                        weather_data, 'relative_humidity_2m', 'Humidity (%)', 'Humidity Forecast')
                    graph_filenames['wind_speed'] = generate_graph(
                        weather_data, 'windspeed_10m', 'Wind Speed (m/s)', 'Wind Speed Forecast')
                    graph_filenames['precipitation'] = generate_graph(
                        weather_data, 'precipitation', 'Precipitation (mm)', 'Precipitation Forecast')
                else:
                    weather_data = {'error': 'Unable to fetch weather data.'}
            else:
                weather_data = {'error': 'City not found. Please try another.'}
        else:
            weather_data = {'error': 'Failed to fetch geolocation data.'}

    return render_template('dashboard.html', weather_data=weather_data, graph_filenames=graph_filenames)


# Function to generate weather graphs
def generate_graph(weather_data, attribute, ylabel, title):
    try:
        # Extract data for the next 24 hours
        times = weather_data['hourly']['time'][:24]
        values = weather_data['hourly'][attribute][:24]
        time_labels = [datetime.datetime.fromisoformat(t).strftime('%H:%M') for t in times]

        # Plot the graph
        plt.figure(figsize=(10, 5))
        plt.plot(time_labels, values, marker='o', linestyle='-', label=attribute)
        plt.xticks(rotation=45)
        plt.xlabel('Time (24 hours)')
        plt.ylabel(ylabel)
        plt.title(title)
        plt.tight_layout()

        # Save the graph to the static folder
        if not os.path.exists('static'):
            os.makedirs('static')
        graph_filename = f'static/{attribute}_plot.png'
        plt.savefig(graph_filename)
        plt.close()
        return graph_filename
    except Exception as e:
        print(f"Error generating graph for {attribute}: {e}")
        return None


# Run the Flask application
if __name__ == '__main__':  # Corrected __name__ here
    try:
        # Ensure necessary directories exist
        if not os.path.exists('static'):
            os.makedirs('static')
        if not os.path.exists('templates'):
            os.makedirs('templates')

        # Start the server
        app.run(debug=True)
    except Exception as e:
        print(f"Failed to start the server: {e}")
