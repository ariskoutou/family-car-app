import os
import sqlite3
import json
from datetime import datetime
from flask import Flask, render_template, request, redirect, url_for, flash, jsonify

app = Flask(__name__)
app.secret_key = 'family_secret_key_123'

DB_FILE = 'database.db'

def get_db_connection():
    conn = sqlite3.connect(DB_FILE)
    conn.row_factory = sqlite3.Row
    return conn

def init_db():
    conn = get_db_connection()
    # Πίνακας για τα αιτήματα
    conn.execute('''
        CREATE TABLE IF NOT EXISTS car_requests (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            driver TEXT NOT NULL,
            date TEXT NOT NULL,
            time TEXT NOT NULL,
            reason TEXT NOT NULL,
            status TEXT DEFAULT 'Εκκρεμεί'
        )
    ''')
    # Πίνακας για τον κωδικό πρόσβασης
    conn.execute('''
        CREATE TABLE IF NOT EXISTS settings (
            key TEXT PRIMARY KEY,
            value TEXT NOT NULL
        )
    ''')
    # Αν δεν υπάρχει ήδη κωδικός, βάζουμε τον αρχικό '1234'
    conn.execute("INSERT OR IGNORE INTO settings (key, value) VALUES ('parents_password', '1234')")
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
    raw_requests = conn.execute('SELECT * FROM car_requests ORDER BY id DESC').fetchall()
    conn.close()
    
    requests = []
    for r in raw_requests:
        req_dict = dict(r)
        try:
            date_obj = datetime.strptime(req_dict['date'], '%Y-%m-%d')
            req_dict['date'] = date_obj.strftime('%d/%m/%Y')
        except:
            pass
        requests.append(req_dict)
        
    return render_template('index.html', requests=requests)

@app.route('/calendar')
def calendar_page():
    conn = get_db_connection()
    requests = conn.execute("SELECT * FROM car_requests WHERE status != 'Απορρίφθηκε'").fetchall()
    conn.close()
    
    events = []
    for r in requests:
        color = '#ffc107' if r['status'] == 'Εκκρεμεί' else '#198754'
        text_color = '#000000' if r['status'] == 'Εκκρεμεί' else '#ffffff'
        
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
    conn = get_db_connection()
    db_pass = conn.execute("SELECT value FROM settings WHERE key = 'parents_password'").fetchone()
    conn.close()
    current_password = db_pass['value'] if db_pass else '1234'

    if request.method == 'POST':
        password = request.form.get('password')
        if password == current_password:
            return redirect(url_for('parents_dashboard'))
        else:
            flash('Λάθος κωδικός! Προσπαθήστε ξανά.', 'danger')
            return redirect(url_for('parents_login'))
    return render_template('parents_login.html')

@app.route('/parents/change-password', methods=['POST'])
def change_password():
    old_password = request.form.get('old_password')
    new_password = request.form.get('new_password')

    conn = get_db_connection()
    db_pass = conn.execute("SELECT value FROM settings WHERE key = 'parents_password'").fetchone()
    current_password = db_pass['value'] if db_pass else '1234'

    if old_password == current_password:
        conn.execute("UPDATE settings SET value = ? WHERE key = 'parents_password'", (new_password,))
        conn.commit()
        conn.close()
        flash('Ο κωδικός άλλαξε επιτυχώς!', 'success')
    else:
        conn.close()
        flash('Ο παλιός κωδικός είναι λανθασμένος. Η αλλαγή απέτυχε.', 'danger')
        
    return redirect(url_for('parents_login'))

@app.route('/parents/dashboard')
def parents_dashboard():
    conn = get_db_connection()
    raw_requests = conn.execute("SELECT * FROM car_requests WHERE status = 'Εκκρεμεί' ORDER BY id DESC").fetchall()
    conn.close()
    
    formatted_requests = []
    for r in raw_requests:
        req_dict = dict(r)
        try:
            date_obj = datetime.strptime(req_dict['date'], '%Y-%m-%d')
            req_dict['date'] = date_obj.strftime('%d/%m/%Y')
        except:
            pass
        formatted_requests.append(req_dict)
        
    return render_template('parents_dashboard.html', requests=formatted_requests)

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
