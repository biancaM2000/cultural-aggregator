from flask import Flask, jsonify, request, render_template
import os
import psycopg2
from psycopg2.extras import RealDictCursor
import time

app = Flask(__name__)

def get_db_connection():
    retries = 5
    while retries > 0:
        try:
            conn = psycopg2.connect(
                host=os.environ.get('DB_HOST', 'localhost'),
                database=os.environ.get('DB_NAME', 'cultural_db'),
                user=os.environ.get('DB_USER', 'postgres'),
                password=os.environ.get('DB_PASSWORD', 'devops_secret_2026')
            )
            return conn
        except psycopg2.OperationalError:
            retries -= 1
            print("Baza de date nu este gata sau nu se poate conecta. Incearca din nou in 2 secunde...")
            time.sleep(2)
    raise Exception("Nu s-a putut stabili conexiunea cu baza de date.")

def init_db():
    conn = get_db_connection()
    cur = conn.cursor()
    cur.execute('''
        CREATE TABLE IF NOT EXISTS evenimente (
            id SERIAL PRIMARY KEY,
            titlu VARCHAR(150) NOT NULL,
            oras VARCHAR(50) NOT NULL,
            data VARCHAR(50) NOT NULL,
            categorie VARCHAR(50) NOT NULL
        );
    ''')
    
    cur.execute('SELECT COUNT(*) FROM evenimente;')
    if cur.fetchone()[0] == 0:
        date_initiale = [
            ('Festivalul International de Film Transilvania (TIFF)', 'Cluj-Napoca', 'Iunie 2026', 'Film'),
            ('Concert special la Ateneul Roman', 'Bucuresti', '30 Mai 2026', 'Muzica Clasica'),
            ('Expozitie de Arta Contemporana', 'Timisoara', 'Iunie 2026', 'Arta'),
            ('Festivalul de Teatru Tanar', 'Iasi', 'Mai 2026', 'Teatru')
        ]
        for ev in date_initiale:
            cur.execute(
                'INSERT INTO evenimente (titlu, oras, data, categorie) VALUES (%s, %s, %s, %s);',
                ev
            )
    conn.commit()
    cur.close()
    conn.close()

# fornt end route   
@app.route('/')
def home():
    conn = get_db_connection()
    cur = conn.cursor(cursor_factory=RealDictCursor)
    
    # Filtrare optionala dupa oras
    oras_filtru = request.args.get('oras')
    if oras_filtru:
        cur.execute('SELECT * FROM evenimente WHERE oras ILIKE %s ORDER BY id ASC;', (oras_filtru,))
    else:
        cur.execute('SELECT * FROM evenimente ORDER BY id ASC;')
        
    evenimente = cur.fetchall()
    cur.close()
    conn.close()
    
    # Trimitem datele direct in template pentru a fi afisate in HTML
    return render_template('index.html', evenimente=evenimente)

# ruta back-end pentru API-ul RESTful care returnează evenimentele în format JSON
@app.route('/api/evenimente', methods=['GET'])
def get_evenimente():
    conn = get_db_connection()
    cur = conn.cursor(cursor_factory=RealDictCursor)
    oras_filtru = request.args.get('oras')
    
    if oras_filtru:
        cur.execute('SELECT * FROM evenimente WHERE oras ILIKE %s;', (oras_filtru,))
    else:
        cur.execute('SELECT * FROM evenimente ORDER BY id ASC;')
        
    evenimente = cur.fetchall()
    cur.close()
    conn.close()
    return jsonify(evenimente)

if __name__ == '__main__':
    init_db()
    app.run(host='0.0.0.0', port=5000)