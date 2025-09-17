# 🛰️ ISS Tracker CLI

A Python-based command-line tool that tracks the [International Space Station (ISS)](https://www.nasa.gov/mission_pages/station/main/index.html) in real time, visualizes its location on an ASCII world map, and notifies you by email when it's passing over your location at night.  

---

## ✨ Features
- 🌌 Real-time ISS position tracking using [Open Notify API](http://api.open-notify.org/iss-now.json)
- 🗺️ ASCII-based world map visualization
- 🌙 Automatic night-time detection using [Sunrise-Sunset API](https://sunrise-sunset.org/api)
- 📧 Email alerts when ISS is overhead at night
- 📝 Detailed logging system

---

## ⚙️ Setup

## 1. Clone the repo
```bash
git clone https://github.com/your-username/iss-tracker-cli.git
cd iss-tracker-cli

---

## 2. Create and fill .env
MY_EMAIL=youremail@gmail.com
EMAIL_PASSWORD=your_app_password
MY_LAT=22.470493
MY_LNG=88.307407
TIMEZONE_OFFSET=5.5
⚠️ Use an App Password if using Google accounts (not your main password).
---
##3. Install dependencies
pip install -r requirements.txt
---
🚀 Usage
python main.py
The program will print your location vs ISS location on an ASCII map.

If ISS is within 500 km and it's night, you’ll get an email notification.
---
📸 Screenshots

Initial Banner

  _____ _____ ____    ____  _   _ ____  _     _____ 
 |_   _|  ___/ ___|  / ___|| | | |  _ \| |   | ____|
   | | | |_  \___ \  \___ \| | | | |_) | |   |  _|  
   | | |  _|  ___) |  ___) | |_| |  __/| |___| |___ 
   |_| |_|   |____/  |____/ \___/|_|   |_____|_____|
   
✨ ISS TRACKER ACTIVATED ✨
Monitoring your position: 22.470493, 88.307407
Notification email: youremail@gmail.com

---
Map View

🌎 Your Position vs ISS Position:
・・・・・・・・・・・・・・・・・・・・・・・・・・・・・・・・・・・・・・・
・・・・・・・・・・・・・・・・・・・・・・・・・・・・・・・・・・・・・・・
・・・・・🏠・・・・・・・・・・・・・・・・・・・・・・🛰️・・・・・・・・・・・・・・・・

📍 Your position: 22.47, 88.30
🛰️ ISS position: 25.64, 90.12
📏 Distance: 321.43 km
🧭 Direction: North-East
---
📜 License

This project is licensed under the MIT License. You’re free to use, modify, and share it.

Created with ❤️ using Python By- Jay Mondal
