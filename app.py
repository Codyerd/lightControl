from flask import Flask, request, jsonify, render_template
from flask_socketio import SocketIO, emit
from flask_cors import CORS
from datetime import datetime
import os
import psycopg2
import logging

app = Flask(__name__)
CORS(app)
socketio = SocketIO(app, cors_allowed_origins="*", logger=True)

# Light status
light_status = {"state": "off"}  # Default state

connected_clients = {}  # Stores active ESP32 relay connections

def get_db_connection():
    conn = psycopg2.connect(host=os.getenv('POSTGRES_HOST', 'lc_history_postgres'),
                            database=os.environ['POSTGRES_DB'],
                            user=os.environ['POSTGRES_USER'],
                            password=os.environ['POSTGRES_PASSWORD'])
    return conn

@socketio.on('*')
def catch_all(event, data):
    app.logger.info(event)
    app.logger.info(data)

@socketio.on('register')
def register_device(device_id):
    """ESP32 relay-switch registers itself with the server"""
    app.logger.info("Received register request!")
    if device_id:
        connected_clients[device_id] = request.sid  # Store session ID
        app.logger.info(f"Successfully registered {device_id}!")
        # emit("registration_success", {"message": "Registered successfully", "device_id": device_id}, room=request.sid)

@app.route('/')
def home():
    """Render the main page."""
    return render_template('index.html')


@app.route('/light-status', methods=['GET'])
def get_light_status():
    """Get the current status of the light."""
    return jsonify({"state": light_status["state"]}), 200


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
                (new_state, datetime.now())
            )
        conn.commit()
    finally:
        conn.close()
    # Send WebSocket message only to the ESP32 relay-switch
    if "esp32_switch" in connected_clients:
        socketio.emit("light_status", {"state": new_state}, to=connected_clients["esp32_switch"])
        app.logger.info(f"message: Light is turned {new_state}")
    else:
        app.logger.warning("error: ESP32 switch not connected")

    return jsonify({"message": f"Light is turned {new_state}", "state": new_state}), 200


@app.route('/toggle-history', methods=['GET'])
def show_history():
    """Show the toggle action history."""
    conn = get_db_connection()
    try:
        with conn.cursor() as cur:
            cur.execute('SELECT * FROM toggle_actions;')
            history = [
                {
                    "timestamp": row[2].strftime('%Y-%m-%d %H:%M:%S'),
                    "act": row[1],
                }
                for row in cur.fetchall()
            ]
        conn.commit()
    except Exception as e:
        print(f"An error occurred when fetching toggle history: {e}")
        history = []
    finally:
        conn.close()

    return render_template('history.html', actions=history)


@app.route('/comments', methods=['POST'])
def add_comment():
    """Add a new comment to the board."""
    data = request.get_json()
    comment = data.get('comment')
    if not comment:
        return jsonify({"error": "Comment cannot be empty"}), 400

    ip_address = request.remote_addr
    conn = get_db_connection()
    try:
        with conn.cursor() as cur:
            cur.execute(
                'INSERT INTO comments (timestamp, comment, ip_address) VALUES (%s, %s, %s)',
                (datetime.now(), comment, ip_address)
            )
            conn.commit()
        return jsonify({"message": "Comment added successfully"}), 201
    except Exception as e:
        print(f"Error adding comment: {e}")
        return jsonify({"error": "Failed to add comment"}), 500
    finally:
        conn.close()


@app.route('/comments', methods=['GET'])
def get_comment():
    """Get all comments from database."""
    conn = get_db_connection()
    user_ip = str(request.remote_addr).strip()
    try:
        with conn.cursor() as cur:
            cur.execute('SELECT id, comment, timestamp, ip_address FROM comments ORDER BY timestamp DESC;')
            comments = [
                {
                    "id": row[0],
                    "comment": row[1],
                    "timestamp": row[2].strftime('%Y-%m-%d %H:%M'),
                    "delete": 1 if row[3] == user_ip.strip() else 0
                }
                for row in cur.fetchall()
            ]
    except Exception as e:
        print(f"An error occurred when fetching comments: {e}")
        comments = []
    finally:
        conn.close()

    return jsonify(comments), 200


@app.route('/comments/<int:comment_id>', methods=['DELETE'])
def delete_comment(comment_id):
    """Delete an existing comment by id."""
    conn = get_db_connection()
    try:
        with conn.cursor() as cur:
            cur.execute(
                'DELETE FROM comments WHERE id = %s;',
                (comment_id,)
            )
            conn.commit()
        return jsonify({"message": "Comment deleted successfully"}), 200
    except Exception as e:
        print(f"Error deleting comment: {e}")
        return jsonify({"error": "Failed to delete comment"}), 500
    finally:
        conn.close()

if __name__ == "__main__":
    # app.run(host='0.0.0.0', port=5000)
    socketio.run(app, host='0.0.0.0', port=5000, debug=True, allow_unsafe_werkzeug=True)
