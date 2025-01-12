from flask import Flask, render_template, request, redirect, url_for, session, send_file
import sqlite3
import csv
from io import StringIO

app = Flask(__name__)
app.secret_key = 'your_secret_key'  # Use a secure key for production

# Admin credentials
ADMIN_EMAIL = 'ayiekolai@gmail.com'
ADMIN_PASSWORD = 'LaiTech0740136761*'

def init_db():
    """Initialize the database with a sample table."""
    conn = sqlite3.connect('certificate.db')
    c = conn.cursor()
    c.execute('''CREATE TABLE IF NOT EXISTS certificates (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT,
            certificate_number TEXT,
            course_type TEXT,
            date_issued TEXT,
            user_email TEXT
    )''')
    conn.commit()
    conn.close()

# Initialize database on app startup
init_db()

@app.route('/')
def home():
    return render_template('index.html')

@app.route('/certificate', methods=['GET', 'POST'])
def certificate():
    if request.method == 'POST':
        certificate_number = request.form.get('certificate_number')
        surname = request.form.get('surname')
        course_type = request.form.get('course_type')
        date_issued = request.form.get('date_issued')
        
        conn = sqlite3.connect('certificate.db')
        c = conn.cursor()
        
        # Perform search using LIKE for fuzzy search and exact match
        query = "SELECT * FROM certificates WHERE certificate_number LIKE ? AND name LIKE ?"
        
        # Add filtering for course_type and date_issued if provided
        if course_type:
            query += " AND course_type LIKE ?"
        if date_issued:
            query += " AND date_issued LIKE ?"
        
        c.execute(query, ('%' + certificate_number + '%', '%' + surname + '%', 
                          '%' + course_type + '%', '%' + date_issued + '%'))
        
        certificates = c.fetchall()
        conn.close()
        
        return render_template('index.html', certificates=certificates)
    
    return render_template('index.html')

@app.route('/certificate/<int:certificate_id>')
def certificate_details(certificate_id):
    conn = sqlite3.connect('certificate.db')
    c = conn.cursor()
    c.execute("SELECT * FROM certificates WHERE id = ?", (certificate_id,))
    certificate = c.fetchone()
    conn.close()
    return render_template('certificate_details.html', certificate=certificate)

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        email = request.form['email']
        password = request.form['password']
        if email == ADMIN_EMAIL and password == ADMIN_PASSWORD:
            session['logged_in'] = True
            return redirect(url_for('admin'))
        else:
            return render_template('login.html', error="Invalid credentials")
    return render_template('login.html')

@app.route('/admin')
def admin():
    if not session.get('logged_in'):
        return redirect(url_for('login'))
    conn = sqlite3.connect('certificate.db')
    c = conn.cursor()
    c.execute("SELECT * FROM certificates")
    certificates = c.fetchall()
    conn.close()
    return render_template('admin.html', certificates=certificates)

@app.route('/admin/add', methods=['GET', 'POST'])
def add_certificate():
    if not session.get('logged_in'):
        return redirect(url_for('login'))
    
    if request.method == 'POST':
        name = request.form['name']
        certificate_number = request.form['certificate_number']
        course_type = request.form['course_type']
        date_issued = request.form['date_issued']
        user_email = request.form.get('user_email')  # capturing the user's email for tracking
        
        conn = sqlite3.connect('certificate.db')
        c = conn.cursor()
        c.execute("INSERT INTO certificates (name, certificate_number, course_type, date_issued, user_email) VALUES (?, ?, ?, ?, ?) ",
                  (name, certificate_number, course_type, date_issued, user_email))
        conn.commit()
        conn.close()
        return redirect(url_for('admin'))
    
    return render_template('add_certificate.html')

@app.route('/admin/delete/<int:certificate_id>')
def delete_certificate(certificate_id):
    if not session.get('logged_in'):
        return redirect(url_for('login'))
    
    conn = sqlite3.connect('certificate.db')
    c = conn.cursor()
    c.execute("DELETE FROM certificates WHERE id = ?", (certificate_id,))
    conn.commit()
    conn.close()
    return redirect(url_for('admin'))

@app.route('/admin/edit/<int:certificate_id>', methods=['GET', 'POST'])
def edit_certificate(certificate_id):
    if not session.get('logged_in'):
        return redirect(url_for('login'))

    conn = sqlite3.connect('certificate.db')
    c = conn.cursor()

    if request.method == 'POST':
        name = request.form['name']
        certificate_number = request.form['certificate_number']
        course_type = request.form['course_type']
        date_issued = request.form['date_issued']

        c.execute('''UPDATE certificates SET name = ?, certificate_number = ?, course_type = ?, date_issued = ?
                     WHERE id = ?''', (name, certificate_number, course_type, date_issued, certificate_id))
        conn.commit()
        conn.close()
        return redirect(url_for('admin'))

    c.execute("SELECT * FROM certificates WHERE id = ?", (certificate_id,))
    certificate = c.fetchone()
    conn.close()
    return render_template('edit_certificate.html', certificate=certificate)

@app.route('/admin/export')
def export_certificates():
    if not session.get('logged_in'):
        return redirect(url_for('login'))
    
    conn = sqlite3.connect('certificate.db')
    c = conn.cursor()
    c.execute("SELECT * FROM certificates")
    certificates = c.fetchall()
    conn.close()

    # Create a CSV string from the certificate data
    output = StringIO()
    writer = csv.writer(output)
    writer.writerow(['ID', 'Name', 'Certificate Number', 'Course Type', 'Date Issued', 'User Email'])  # Headers
    for row in certificates:
        writer.writerow(row)
    
    output.seek(0)
    return send_file(output, mimetype='text/csv', attachment_filename='certificates.csv', as_attachment=True)

# Run the Flask app
if __name__ == "__main__":
    app.run(debug=True)
