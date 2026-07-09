import sqlite3
from flask import Flask, render_template, request, redirect, url_for, flash

app = Flask(__name__)
# Το secret_key είναι απαραίτητο για να λειτουργούν τα μηνύματα λάθους (flash messages)
app.secret_key = 'super_secret_key_family_car'

def get_db_connection():
    conn = sqlite3.connect('database.db')
    conn.row_factory = sqlite3.Row
    return conn

# Δημιουργία του πίνακα στη βάση αν δεν υπάρχει ήδη
def init_db():
    conn = get_db_connection()
    conn.execute('''
        CREATE TABLE IF NOT EXISTS car_requests (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            driver TEXT NOT NULL,
            date TEXT NOT NULL,
            time TEXT NOT NULL,
            reason TEXT,
            status TEXT DEFAULT 'Εκκρεμεί'
        )
    ''')
    conn.commit()
    conn.close()

init_db()

# 1. ΑΡΧΙΚΗ ΣΕΛΙΔΑ (Παιδιά - Υποβολή Αιτήματος)
@app.route('/', methods=['GET', 'POST'])
def index():
    conn = get_db_connection()
    if request.method == 'POST':
        driver = request.form['driver']
        date = request.form['date']
        time = request.form['time']
        reason = request.form['reason']
        
        conn.execute('INSERT INTO car_requests (driver, date, time, reason) VALUES (?, ?, ?, ?)',
                     (driver, date, time, reason))
        conn.commit()
        return redirect(url_for('index'))
    
    # Εμφάνιση όλων των αιτημάτων στην αρχική σελίδα για να βλέπουν όλοι το πρόγραμμα
    requests_db = conn.execute('SELECT * FROM car_requests ORDER BY date DESC').fetchall()
    conn.close()
    return render_template('index.html', requests=requests_db)

# 2. ΣΕΛΙΔΑ ΕΙΣΟΔΟΥ ΓΟΝΕΩΝ (Ζητάει κωδικό)
@app.route('/parents', methods=['GET', 'POST'])
def parents():
    if request.method == 'POST':
        password = request.form.get('password')
        # Εδώ είναι ο κωδικός πρόσβασης. Άλλαξέ τον αν θες!
        if password == '1234':
            conn = get_db_connection()
            requests_db = conn.execute('SELECT * FROM car_requests WHERE status = "Εκκρεμεί" ORDER BY date DESC').fetchall()
            conn.close()
            # Αν ο κωδικός είναι σωστός, τους δείχνει τα αιτήματα
            return render_template('parents_dashboard.html', requests=requests_db)
        else:
            # Αν είναι λάθος, βγάζει κόκκινο μήνυμα
            flash('Λάθος κωδικός πρόσβασης! Προσπαθήστε ξανά.', 'danger')
            return render_template('parents_login.html')
            
    return render_template('parents_login.html')

# 3. ΕΓΚΡΙΣΗ Ή ΑΠΟΡΡΙΨΗ ΑΙΤΗΜΑΤΟΣ ΑΠΟ ΤΟΥΣ ΓΟΝΕΙΣ
@app.route('/admin/decide/<int:req_id>/<string:action>')
def decide_request(req_id, action):
    new_status = 'Εγκρίθηκε' if action == 'approve' else 'Απορρίφθηκε'
    
    conn = get_db_connection()
    conn.execute('UPDATE car_requests SET status = ? WHERE id = ?', (new_status, req_id))
    conn.commit()
    conn.close()
    return redirect(url_for('index'))

if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=5000)