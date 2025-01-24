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

    return jsonify({"message": f"Light is turned {new_state}", "state": new_state}), 200


@app.route('/toggle-history', methods=['GET'])
def show_history():
    """Show the toggle action history."""
    conn = get_db_connection()
    try:
        with conn.cursor() as cur:
            cur.execute('SELECT * FROM toggle_actions;')
            history = cur.fetchall()
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
    try:
        with conn.cursor() as cur:
            cur.execute('SELECT id, comment, timestamp FROM comments ORDER BY timestamp DESC;')
            comments = [
                {
                    "id": row[0],
                    "comment": row[1],
                    "timestamp": row[2].strftime('%Y-%m-%d %H:%M')
                }
                for row in cur.fetchall()
            ]
        conn.commit()
    except Exception as e:
        print(f"An error occurred when fetching comments: {e}")
        comments = []
    finally:
        conn.close()

    return jsonify(comments), 200



if __name__ == "__main__":
    app.run(host='0.0.0.0', port=5000)
