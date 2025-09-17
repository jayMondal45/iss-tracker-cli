import requests
from datetime import datetime, timezone, timedelta
import smtplib
import time
import math
import logging
from typing import Tuple, Optional
import os
from dotenv import load_dotenv
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart

# Load environment variables
load_dotenv()

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler("iss_tracker.log"),
        logging.StreamHandler()
    ]
)

# Configuration from environment variables
MY_EMAIL = os.getenv("MY_EMAIL", "your_email@gmail.com")
EMAIL_PASSWORD = os.getenv("EMAIL_PASSWORD", "your_app_password")
MY_LAT = float(os.getenv("MY_LAT", "22.470493"))
MY_LNG = float(os.getenv("MY_LNG", "88.307407"))
TIMEZONE_OFFSET = float(os.getenv("TIMEZONE_OFFSET", "5.5"))  # Default to IST

# Visual elements for console output
BANNER = r"""
  _____ _____ ____    ____  _   _ ____  _     _____ 
 |_   _|  ___/ ___|  / ___|| | | |  _ \| |   | ____|
   | | | |_  \___ \  \___ \| | | | |_) | |   |  _|  
   | | |  _|  ___) |  ___) | |_| |  __/| |___| |___ 
   |_| |_|   |____/  |____/ \___/|_|   |_____|_____|
   
✨ ISS TRACKER ACTIVATED ✨
Monitoring your position: {}, {}
Notification email: {}
""".format(MY_LAT, MY_LNG, MY_EMAIL)

SUCCESS_ART = r"""
    🌌
   ✨   ISS SPOTTED!
    🌠
   / \
  /   \
 /     \
"""

def calculate_distance(lat1: float, lon1: float, lat2: float, lon2: float) -> float:
    """Calculate distance between two coordinates using Haversine formula."""
    R = 6371  # Earth radius in kilometers
    
    lat1_rad = math.radians(lat1)
    lat2_rad = math.radians(lat2)
    delta_lat = math.radians(lat2 - lat1)
    delta_lon = math.radians(lon2 - lon1)
    
    a = (math.sin(delta_lat/2) * math.sin(delta_lat/2) + 
         math.cos(lat1_rad) * math.cos(lat2_rad) * 
         math.sin(delta_lon/2) * math.sin(delta_lon/2))
    c = 2 * math.atan2(math.sqrt(a), math.sqrt(1-a))
    
    return R * c

def get_iss_location() -> Tuple[Optional[float], Optional[float]]:
    """Get current ISS coordinates."""
    try:
        response = requests.get(url="http://api.open-notify.org/iss-now.json", timeout=10)
        response.raise_for_status()
        data = response.json()
        
        iss_latitude = float(data["iss_position"]["latitude"])
        iss_longitude = float(data["iss_position"]["longitude"])
        
        return iss_latitude, iss_longitude
            
    except requests.exceptions.RequestException as e:
        logging.error(f"Error fetching ISS data: {e}")
        return None, None
    except (KeyError, ValueError) as e:
        logging.error(f"Error parsing ISS data: {e}")
        return None, None

def is_iss_overhead() -> Tuple[bool, Optional[float]]:
    """Check if ISS is overhead and return status with distance."""
    iss_lat, iss_lng = get_iss_location()
    
    if iss_lat is None or iss_lng is None:
        return False, None
        
    # Calculate distance from your position
    distance = calculate_distance(MY_LAT, MY_LNG, iss_lat, iss_lng)
    
    # Check if ISS is within 500km (more precise than 5 degrees)
    if distance <= 500:
        logging.info(f"ISS is {distance:.2f} km away")
        return True, distance
    else:
        logging.info(f"ISS is {distance:.2f} km away (too far)")
        return False, distance

def is_night() -> bool:
    """Check if it's currently night time at your location."""
    try:
        parameters = {
            "lat": MY_LAT,
            "lng": MY_LNG,
            "formatted": 0
        }
        
        response = requests.get(url="https://api.sunrise-sunset.org/json", 
                               params=parameters, timeout=10)
        response.raise_for_status()
        data = response.json()
        
        if data["status"] != "OK":
            logging.error(f"Sunrise-sunset API error: {data}")
            return False
            
        sunrise_str = data["results"]["sunrise"]
        sunset_str = data["results"]["sunset"]
        
        # Parse sunrise and sunset times (they come in UTC)
        sunrise_utc = datetime.fromisoformat(sunrise_str.replace('Z', '+00:00'))
        sunset_utc = datetime.fromisoformat(sunset_str.replace('Z', '+00:00'))
        
        # Convert to local timezone - remove timezone info to make them naive
        utc_offset = timedelta(hours=TIMEZONE_OFFSET)
        sunrise_local = (sunrise_utc + utc_offset).replace(tzinfo=None)
        sunset_local = (sunset_utc + utc_offset).replace(tzinfo=None)
        current_time = datetime.now()  # This is timezone-naive
        
        # For night detection, handle day crossing correctly
        if sunrise_local.date() != sunset_local.date():
            # Handle case where sunset is on different day (shouldn't happen normally)
            is_dark = current_time.time() > sunset_local.time() or current_time.time() < sunrise_local.time()
        else:
            # Normal case: sunrise and sunset on same day
            if sunrise_local < sunset_local:
                # Normal day: sunrise before sunset
                is_dark = current_time.time() < sunrise_local.time() or current_time.time() > sunset_local.time()
            else:
                # Edge case: might cross midnight
                is_dark = current_time.time() > sunset_local.time() or current_time.time() < sunrise_local.time()
        
        logging.info(f"Sunset: {sunset_local.strftime('%H:%M')}, Sunrise: {sunrise_local.strftime('%H:%M')}, "
                    f"Current: {current_time.strftime('%H:%M')}, Is night: {is_dark}")
        return is_dark
        
    except requests.exceptions.RequestException as e:
        logging.error(f"Error fetching sunrise/sunset data: {e}")
        return False
    except (KeyError, ValueError) as e:
        logging.error(f"Error parsing sunrise/sunset data: {e}")
        return False
    except Exception as e:
        logging.error(f"Error in night detection: {e}")
        return False

def send_email_notification(distance: float):
    """Send email notification about ISS sighting."""
    try:
        # Create message with proper MIME structure
        msg = MIMEMultipart()
        msg['From'] = MY_EMAIL
        msg['To'] = MY_EMAIL
        msg['Subject'] = "🌌 ISS Overhead! Look Up! 🌌"
        
        body = (
            f"The International Space Station is {distance:.2f} km above you!\n"
            f"Go outside and look up! You might see it passing by!\n\n"
            f"Time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n"
            f"Position: {MY_LAT}, {MY_LNG}"
        )
        
        msg.attach(MIMEText(body, 'plain'))
        
        # Send email
        with smtplib.SMTP("smtp.gmail.com", 587) as server:
            server.starttls()
            server.login(MY_EMAIL, EMAIL_PASSWORD)
            server.send_message(msg)
            
        logging.info(f"Email sent successfully to {MY_EMAIL}")
        print(SUCCESS_ART)
        
    except smtplib.SMTPAuthenticationError:
        logging.error("SMTP Authentication failed. Check your email credentials.")
    except smtplib.SMTPException as e:
        logging.error(f"SMTP error occurred: {e}")
    except Exception as e:
        logging.error(f"Failed to send email: {e}")

def display_iss_position(iss_lat: float, iss_lng: float, distance: float):
    """Display a visual representation of ISS position relative to user."""
    # Simple text-based visualization
    map_width = 60
    map_height = 15
    
    # Calculate relative position (normalized)
    lat_ratio = (iss_lat + 90) / 180  # Convert from [-90,90] to [0,1]
    lng_ratio = (iss_lng + 180) / 360  # Convert from [-180,180] to [0,1]
    
    # Scale to map size
    x_pos = int(lng_ratio * (map_width - 1))  # Prevent index out of bounds
    y_pos = int((1 - lat_ratio) * (map_height - 1))  # Invert y-axis for display
    
    # Calculate your position on the map
    my_lat_ratio = (MY_LAT + 90) / 180
    my_lng_ratio = (MY_LNG + 180) / 360
    my_x_pos = int(my_lng_ratio * (map_width - 1))
    my_y_pos = int((1 - my_lat_ratio) * (map_height - 1))
    
    print("🌎 Your Position vs ISS Position:")
    for y in range(map_height):
        row = ""
        for x in range(map_width):
            if x == my_x_pos and y == my_y_pos:
                row += "🏠"  # Your position
            elif x == x_pos and y == y_pos:
                row += "🛰️"  # ISS position
            elif x == my_x_pos and y == my_y_pos and x == x_pos and y == y_pos:
                row += "🎯"  # Both at same position (unlikely but possible)
            else:
                row += "・"
        print(row)
    
    print(f"\n📍 Your position: {MY_LAT}, {MY_LNG}")
    print(f"🛰️  ISS position: {iss_lat:.2f}, {iss_lng:.2f}")
    print(f"📏 Distance: {distance:.2f} km")
    
    # Add direction information
    direction = ""
    lat_diff = iss_lat - MY_LAT
    lng_diff = iss_lng - MY_LNG
    
    if abs(lat_diff) > 0.1:  # Small threshold to avoid noise
        if lat_diff > 0:
            direction += "North"
        else:
            direction += "South"
        
    if abs(lng_diff) > 0.1:  # Small threshold to avoid noise
        if direction:  # Add separator if we already have north/south
            direction += "-"
        if lng_diff > 0:
            direction += "East"
        else:
            direction += "West"
    
    if not direction:
        direction = "Directly overhead"
        
    print(f"🧭 Direction: {direction}")

def validate_config():
    """Validate configuration settings."""
    errors = []
    
    if MY_EMAIL == "your_email@gmail.com":
        errors.append("Please set your email address in the .env file")
    
    if EMAIL_PASSWORD == "your_app_password":
        errors.append("Please set your email app password in the .env file")
    
    if not (-90 <= MY_LAT <= 90):
        errors.append(f"Invalid latitude: {MY_LAT}. Must be between -90 and 90")
    
    if not (-180 <= MY_LNG <= 180):
        errors.append(f"Invalid longitude: {MY_LNG}. Must be between -180 and 180")
    
    if errors:
        for error in errors:
            logging.error(error)
            print(f"❌ {error}")
        return False
    
    return True

def main():
    """Main monitoring function."""
    print(BANNER)
    
    # Validate configuration
    if not validate_config():
        print("\n❌ Configuration errors found. Please fix them before running.")
        return
    
    logging.info("ISS Tracker started successfully")
    
    # Track if we've already notified to avoid spamming
    already_notified = False
    consecutive_errors = 0
    max_consecutive_errors = 5
    
    while True:
        try:
            iss_lat, iss_lng = get_iss_location()
            if iss_lat is None or iss_lng is None:
                consecutive_errors += 1
                print(f"❌ Failed to get ISS location (attempt {consecutive_errors}/{max_consecutive_errors}). Retrying in 60 seconds...")
                if consecutive_errors >= max_consecutive_errors:
                    logging.error("Too many consecutive errors. Stopping.")
                    break
                time.sleep(60)
                continue
            else:
                consecutive_errors = 0  # Reset error counter on success
                
            distance = calculate_distance(MY_LAT, MY_LNG, iss_lat, iss_lng)
            iss_overhead = distance <= 500
            night_time = is_night()
            
            # Clear console and display updated information
            try:
                os.system('cls' if os.name == 'nt' else 'clear')
            except:
                pass  # Don't crash if clear doesn't work
                
            print(BANNER)
            
            # Display ISS position visualization
            display_iss_position(iss_lat, iss_lng, distance)
            
            # Display conditions
            print(f"\n🌙 Night time: {'Yes' if night_time else 'No'}")
            print(f"🛰️  ISS overhead: {'Yes' if iss_overhead else 'No'}")
            print(f"📧 Notified: {'Yes' if already_notified else 'No'}")
            
            if iss_overhead and night_time and not already_notified:
                logging.info("ISS is overhead and it's night time!")
                send_email_notification(distance)
                already_notified = True
            elif already_notified and (not iss_overhead or not night_time):
                # Reset notification flag when ISS moves away or day breaks
                already_notified = False
                logging.info("Reset notification flag")
            
            # Wait before checking again
            print(f"\n🕒 Next update in 60 seconds... (Press Ctrl+C to stop)")
            time.sleep(60)
            
        except KeyboardInterrupt:
            logging.info("Program stopped by user")
            print("\n\n👋 Stopping ISS tracker. Goodbye!")
            break
        except Exception as e:
            consecutive_errors += 1
            logging.error(f"Unexpected error (attempt {consecutive_errors}/{max_consecutive_errors}): {e}")
            if consecutive_errors >= max_consecutive_errors:
                logging.error("Too many consecutive errors. Stopping.")
                break
            time.sleep(60)  # Wait before retrying after error

if __name__ == "__main__":
    main()