from flask import Flask, request, jsonify, render_template
from sqlalchemy import create_engine, text
from datetime import datetime
import os


DATABASE_URL = os.getenv(
    "DATABASE_URL",
    "postgresql://postgres:postgres@localhost:5432/toggle_history"
)

engine = create_engine(DATABASE_URL)
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
    with engine.connect() as connection:
        query = text('INSERT INTO toggle_actions (action, timestamp) VALUES (:action, :timestamp)')
        connection.execute(query, {'action': new_state, 'timestamp': datetime.utcnow()})

    return jsonify({"message": f"Light is turned {new_state}", "state": new_state}), 200

@app.route('/light-status', methods=['GET'])
def get_light_status():
    """Get the current status of the light."""
    return jsonify({"state": light_status["state"]}), 200

if __name__ == "__main__":
    app.run(host='0.0.0.0', port=5000)
