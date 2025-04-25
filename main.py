import json
from flask import Flask, request, jsonify
import pyodbc
from datetime import datetime
from dotenv import load_dotenv
import os
import requests
import threading

load_dotenv()

app = Flask(__name__)

app.config['SERVER'] = os.getenv('SERVER')
app.config['DATABASE'] = os.getenv('DATABASE')
app.config['DB_USERNAME'] = os.getenv('DB_USERNAME')
app.config['DB_PASSWORD'] = os.getenv('DB_PASSWORD')
app.config['TELEGRAM_BOT_TOKEN'] = os.getenv('TELEGRAM_BOT_TOKEN')
app.config['CHAT_ID'] = os.getenv('CHAT_ID')
app.config['TEMP_WARNING'] = os.getenv('TEMP_WARNING')
app.config['HUM_WARNING'] = os.getenv('HUM_WARNING')

# Cấu hình kết nối đến SQL Server
conn_str = f"DRIVER={{SQL Server}};SERVER={app.config['SERVER']};DATABASE={app.config['DATABASE']};UID={app.config['DB_USERNAME']};PWD={app.config['DB_PASSWORD']}"

def save_to_db(sensor_id, temp, hum, sound, light, factory, location):
    try:
        conn = pyodbc.connect(conn_str)
        cursor = conn.cursor()
        cursor.execute("""
            IF NOT EXISTS (SELECT * FROM sysobjects WHERE name='sensor_data_test' AND xtype='U')
            CREATE TABLE sensor_data_test (
                id INT IDENTITY(1,1) PRIMARY KEY,
                sensor_id NCHAR(10) NOT NULL,
                temperature FLOAT NOT NULL,
                humidity FLOAT NOT NULL,
                sound FLOAT NOT NULL,
                light FLOAT NOT NULL,
                factory NCHAR(10) NOT NULL,
                location NCHAR(10) NOT NULL,
                timestamp DATETIME NOT NULL
            );
        """)
        conn.commit()

        timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')

        cursor.execute("INSERT INTO sensor_data_test (sensor_id, temperature, humidity, sound, light, factory, location, timestamp) VALUES (?, ?, ?, ?, ?, ?, ?, ?)",
                       (sensor_id, temp, hum, sound, light, factory, location, timestamp))
        conn.commit()
        conn.close()
        return True
    except Exception as e:
        print("Lỗi kết nối SQL Server:", e)
        return False

@app.route('/upload', methods=['POST'])
def upload():
    try:
        print("UPLOAD", request.get_json())
        data = request.get_json()
    
        sensor_id = data.get("sensor_id")
        temperature = data.get("temperature")
        humidity = data.get("humidity")
        sound = data.get("sound")
        light = data.get("light")
        factory = data.get("factory")
        location = data.get("location")

        isSuccess = save_to_db(sensor_id, temperature, humidity, sound, light, factory, location)
        check_warning(sensor_id, temperature, humidity, sound, light, factory, location)
        if isSuccess:
            return jsonify({"status": "success"}), 200
        return jsonify({"status": "fail"}), 400
    except Exception as e:
        print(e)
        return jsonify({"status": "fail"}), 400
    
def check_warning(sensor_id, temperature, humidity, sound, light, factory, location):
    try : 
        print("check_warning", temperature, humidity, app.config['TEMP_WARNING'], app.config['HUM_WARNING'])
        current_time = datetime.now().strftime("%H:%M:%S %d/%m/%Y")
        if temperature >= float(app.config['TEMP_WARNING']):
            alert_message = f"[{current_time}]\n🔥 High Temperature Warning! <strong>{temperature}°C</strong> at <strong>Factory {factory}</strong>, <strong>{sensor_id}</strong>."
            send_telegram_message(alert_message)
        if humidity >= float(app.config['HUM_WARNING']):
            alert_message = f"[{current_time}]\n💧 High Humidity Warning! <strong>{humidity}%</strong> at <strong>Factory {factory}</strong>, <strong>{sensor_id}</strong>."
            send_telegram_message(alert_message)
    except Exception as e:
        print(e)
    

@app.route('/', methods=['GET'])
def home():
    return jsonify({"status": "success"}), 200

def db():
    return pyodbc.connect(conn_str)

def serialize_datetime(obj):
    if isinstance(obj, datetime):
        return obj.isoformat()
    raise TypeError("Type not serializable")

def query_db(query, args=(), one=False):
    cur = db().cursor()
    cur.execute(query, args)
    r = [dict((cur.description[i][0], value) \
               for i, value in enumerate(row)) for row in cur.fetchall()]
    cur.connection.close()
    return (r[0] if r else None) if one else r

@app.route('/data', methods=['GET'])
def get_all_data():
    try:
        rows = query_db("""SELECT * 
        FROM sensor_data_test 
        ORDER BY id DESC
        OFFSET 0 ROWS FETCH NEXT 50 ROWS ONLY
        """)
        print(rows)
        return json.dumps(rows, default=serialize_datetime)
    except Exception as e:
        return jsonify({"error": str(e)})
    
def send_telegram_message(message):
    """ Sends a Telegram message asynchronously using a separate thread. """
    def send():
        try:
            url = f"https://api.telegram.org/bot{app.config['TELEGRAM_BOT_TOKEN']}/sendMessage"
            payload = {
                "chat_id": app.config['CHAT_ID'], 
                "text": message, 
                "parse_mode": "HTML"
            }
            response = requests.post(url, json=payload)
            response.raise_for_status()
            print("Telegram message sent successfully!")
        except requests.exceptions.RequestException as e:
            print(f"Error sending Telegram message: {e}")

    # Run the function in a new thread
    threading.Thread(target=send, daemon=True).start()

if __name__ == '__main__':
    app.run(host="0.0.0.0", port=5000)