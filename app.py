from flask import Flask, request, jsonify, render_template
from sqlalchemy import create_engine, text
from datetime import datetime
import os
import psycopg2

def get_db_connection():
    conn = psycopg2.connect(host=os.getenv('POSTGRES_HOST', 'lc_history_postgres'),
                            database=os.environ['POSTGRES_DB'],
                            user=os.environ['POSTGRES_USER'],
                            password=os.environ['POSTGRES_PASSWORD'])
    return conn

app = Flask(__name__)

# Light status
light_status = {"state": "off"}  # Default state

@app.route('/')
def home():
    """Render the main page."""
    return render_template('index.html')

@app.route('/toggle-light', methods=['POST'])
def toggle_light():
    """Toggle the light and record the action in the database."""
    current_state = light_status["state"]
    new_state = "on" if current_state == "off" else "off"
    light_status["state"] = new_state

    # Insert the toggle action into the database
    conn = get_db_connection()
    try:
        with conn.cursor() as cursor:
            cursor.execute(
                'INSERT INTO toggle_actions (action, timestamp) VALUES (%s, %s)',
                (new_state, datetime.utcnow())
            )
        conn.commit()
    finally:
        conn.close()

    return jsonify({"message": f"Light is turned {new_state}", "state": new_state}), 200

@app.route('/light-status', methods=['GET'])
def get_light_status():
    """Get the current status of the light."""
    return jsonify({"state": light_status["state"]}), 200

if __name__ == "__main__":
    app.run(host='0.0.0.0', port=5000)
