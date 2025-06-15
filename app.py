from flask import Flask, request, jsonify, g, render_template
import sqlite3
from flask_cors import CORS
import atexit

app = Flask(__name__)
CORS(app)  # อนุญาตให้เรียก API จากโดเมนอื่นได้

# Database Configuration
def get_db():
    """Get database connection with connection pooling"""
    if 'db' not in g:
        g.db = sqlite3.connect('trades.db')
        g.db.row_factory = sqlite3.Row  # เพื่อให้ได้ผลลัพธ์เป็น dictionary
    return g.db

def close_db(e=None):
    """Close database connection"""
    db = g.pop('db', None)
    if db is not None:
        db.close()

# Register function to close db when app shuts down
atexit.register(close_db)
app.teardown_appcontext(close_db)

def init_db():
    """Initialize database with required tables"""
    with app.app_context():
        db = get_db()
        db.execute('''
            CREATE TABLE IF NOT EXISTS trades (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                date TEXT NOT NULL,
                type TEXT NOT NULL,
                amount REAL NOT NULL,
                balance REAL NOT NULL
            )
        ''')
        db.commit()

# Routes
@app.route('/')
def home():
    return render_template('index.html')

@app.route('/trades', methods=['POST'])
def add_trade():
    try:
        data = request.get_json()
        
        # Validate required fields
        if not data:
            return jsonify({'error': 'No data provided'}), 400
            
        required_fields = ['date', 'type', 'amount', 'balance']
        if not all(field in data for field in required_fields):
            return jsonify({'error': 'Missing required fields'}), 400

        # Insert to database
        db = get_db()
        db.execute('''
            INSERT INTO trades (date, type, amount, balance)
            VALUES (?, ?, ?, ?)
        ''', (
            data['date'],
            data['type'],
            float(data['amount']),
            float(data['balance'])
        ))
        db.commit()
        
        return jsonify({'message': 'Trade added successfully!'}), 201
        
    except ValueError as e:
        return jsonify({'error': 'Invalid number format'}), 400
    except sqlite3.Error as e:
        return jsonify({'error': f'Database error: {str(e)}'}), 500
    except Exception as e:
        return jsonify({'error': f'Unexpected error: {str(e)}'}), 500

@app.route('/trades', methods=['GET'])
def get_trades():
    try:
        db = get_db()
        trades = db.execute('SELECT * FROM trades ORDER BY date DESC').fetchall()
        
        # Convert to list of dictionaries
        trades_list = [dict(trade) for trade in trades]
        return jsonify(trades_list)
        
    except sqlite3.Error as e:
        return jsonify({'error': f'Database error: {str(e)}'}), 500
    except Exception as e:
        return jsonify({'error': f'Unexpected error: {str(e)}'}), 500

@app.route('/trades', methods=['DELETE'])
def clear_trades():
    try:
        db = get_db()
        db.execute('DELETE FROM trades')
        db.commit()
        return jsonify({'message': 'All trades cleared successfully!'}), 200
    except sqlite3.Error as e:
        return jsonify({'error': f'Database error: {str(e)}'}), 500
    except Exception as e:
        return jsonify({'error': f'Unexpected error: {str(e)}'}), 500

# Run the application
if __name__ == '__main__':
    init_db()  # Initialize database tables
    print("Starting Trading API...")
    print("Running Flask server...")
    app.run(debug=True, host='0.0.0.0', port=5000)
