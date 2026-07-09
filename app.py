import os
import sqlite3
import json
from flask import Flask, render_template, request, redirect, url_for, flash, jsonify

app = Flask(__name__)
app.secret_key = 'family_secret_key_123'

DB_FILE = 'database.db'

def get_db_connection():
    conn = sqlite3.connect(DB_FILE)
    conn.row_factory = sqlite3.Row
    return conn

def init_db():
    if not os.path.exists(DB_FILE):
        conn = get_db_connection()
        conn.execute('''
            CREATE TABLE car_requests (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                driver TEXT NOT NULL,
                date TEXT NOT NULL,
                time TEXT NOT NULL,
                reason TEXT NOT NULL,
                status TEXT DEFAULT 'Εκκρεμεί'
            )
        ''')
        conn.commit()
        conn.close()

init_db()

@app.route('/', methods=['GET', 'POST'])
def index():
    if request.method == 'POST':
        driver = request.form.get('driver')
        date = request.form.get('date')
        
        time_from = request.form.get('time_from')
        time_to = request.form.get('time_to')
        full_time = f"{time_from} - {time_to}"
        
        reason = request.form.get('reason')

        conn = get_db_connection()
        conn.execute('INSERT INTO car_requests (driver, date, time, reason) VALUES (?, ?, ?, ?)',
                     (driver, date, full_time, reason))
        conn.commit()
        conn.close()
        return redirect(url_for('index'))

    conn = get_db_connection()
    requests = conn.execute('SELECT * FROM car_requests ORDER BY id DESC').fetchall()
    conn.close()
    return render_template('index.html', requests=requests)

@app.route('/calendar')
def calendar_page():
    conn = get_db_connection()
    requests = conn.execute("SELECT * FROM car_requests WHERE status != 'Απορρίφθηκε'").fetchall()
    conn.close()
    
    # Μετατροπή των αιτημάτων σε μορφή FullCalendar Events
    events = []
    for r in requests:
        # Χρώμα ανάλογα με την κατάσταση
        color = '#ffc107' if r['status'] == 'Εκκρεμεί' else '#198754'
        text_color = '#000000' if r['status'] == 'Εκκρεμεί' else '#ffffff'
        
        # Προσπαθούμε να πάρουμε την ώρα "Από" για να μπει σωστά στο ημερολόγιο
        try:
            time_start = r['time'].split(' - ')[0]
            start_datetime = f"{r['date']}T{time_start}"
        except:
            start_datetime = r['date']

        events.append({
            'title': f"{r['driver']} ({r['time']})",
            'start': start_datetime,
            'description': r['reason'],
            'backgroundColor': color,
            'borderColor': color,
            'textColor': text_color
        })
        
    return render_template('calendar.html', events_json=json.dumps(events))

@app.route('/parents', methods=['GET', 'POST'])
def parents_login():
    if request.method == 'POST':
        password = request.form.get('password')
        if password == '1234':
            return redirect(url_for('parents_dashboard'))
        else:
            flash('Λάθος κωδικός! Προσπαθήστε ξανά.', 'danger')
            return redirect(url_for('parents_login'))
    return render_template('parents_login.html')

@app.route('/parents/dashboard')
def parents_dashboard():
    conn = get_db_connection()
    requests = conn.execute("SELECT * FROM car_requests WHERE status = 'Εκκρεμεί' ORDER BY id DESC").fetchall()
    conn.close()
    return render_template('parents_dashboard.html', requests=requests)

@app.route('/admin/decide/<int:request_id>/<string:action>')
def decide_request(request_id, action):
    status = 'Εγκρίθηκε' if action == 'approve' else 'Απορρίφθηκε'
    
    conn = get_db_connection()
    conn.execute('UPDATE car_requests SET status = ? WHERE id = ?', (status, request_id))
    conn.commit()
    conn.close()
    return redirect(url_for('parents_dashboard'))

if __name__ == '__main__':
    app.run(debug=True)
