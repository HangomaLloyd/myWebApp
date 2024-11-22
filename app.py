import pytesseract
from PIL import Image
import re
from flask import Flask, render_template, request
import folium

# Flask app setup
app = Flask(__name__)

# Helper function to extract GPS coordinates
def extract_coordinates(extracted_text):
    print(f"Original Extracted Text: '{extracted_text}'")
    
    # Normalize text to handle multiple spaces
    extracted_text = " ".join(extracted_text.split())
    print(f"Normalized Extracted Text: '{extracted_text}'")

    # Updated regex pattern
    pattern = r"\$?S?(-?\d+(?:[-]?\d*)\.\d+)\sE\s?(\d+\.\d+)"
    match = re.search(pattern, extracted_text)

    if match:
        lat = match.group(1)  # Latitude
        lon = match.group(2)  # Longitude

        print(f"Matched Latitude: {lat}, Longitude: {lon}")

        # Ensure latitude is always negative if $ or S is present
        if extracted_text.startswith("$") or extracted_text.startswith("S"):
            lat = f"-{lat}"

        # Return the final coordinates as a list
        return [lat, lon]
    else:
        print("Regex did not match. Could not extract valid GPS coordinates.")
        return None


# Route to the main page
@app.route('/')
def index():
    return render_template('index.html')

# Route to handle image upload and processing
@app.route('/upload', methods=['POST'])
def upload_image():
    try:
        # Get the uploaded image from the form
        file = request.files['image']
        img = Image.open(file.stream)
        
        # Extract text from the image using Tesseract
        extracted_text = pytesseract.image_to_string(img)
        print(f"Extracted Text from Image: {extracted_text}")
        
        # Extract GPS coordinates from the text
        result = extract_coordinates(extracted_text)
        
        if result:
            gps_coordinates = result
            print(f"Extracted GPS Coordinates: {gps_coordinates}")
            
            # Save the extracted coordinates to a text file
            coordinates_file_path = 'extracted_coordinates.txt'
            with open(coordinates_file_path, 'a') as file:
                file.write(f"Coordinates: {gps_coordinates[0]}, {gps_coordinates[1]}\n\n")

            # Create a map centered on the extracted coordinates
            latitude, longitude = float(gps_coordinates[0]), float(gps_coordinates[1])
            m = folium.Map(location=[latitude, longitude], zoom_start=12)

            # Add a marker with a popup showing the coordinates
            popup_message = f"Here are the coordinates: {latitude}, {longitude}"
            folium.Marker([latitude, longitude], popup=popup_message).add_to(m)

            # Render the map HTML into a string
            map_html = m._repr_html_()

            # Return the map and extracted coordinates
            return render_template('index.html', map_html=map_html, coordinates=gps_coordinates)
        else:
            # Handle cases where no valid GPS data is found
            return render_template('index.html', error="Could not extract valid GPS coordinates.")
    
    except Exception as e:
        # Print and display any errors during processing
        print(f"Error processing the image: {str(e)}")
        return render_template('index.html', error="Error processing the image. Please try again.")

if __name__ == '__main__':
    app.run(port=4000, debug=True)
