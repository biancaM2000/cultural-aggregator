from flask import Flask, jsonify, request
import os
import psycopg2
from psycopg2.extras import RealDictCursor
import time

app = Flask(__name__)

# conectare la baza de date cu retry logic pentru a astepta pana cand baza de date este gata sa accepte conexiuni
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
            print("Baza de date nu este gata încă. Reîncerc în 2 secunde...")
            time.sleep(2)
    raise Exception("Nu s-a putut stabili conexiunea cu baza de date.")

# initializare baza de dare si creare tabela daca nu exista
def init_db():
    conn = get_db_connection()
    cur = conn.cursor()
    
    # creare tabela evenimente daca nu exista deja
    cur.execute('''
        CREATE TABLE IF NOT EXISTS evenimente (
            id SERIAL PRIMARY KEY,
            titlu VARCHAR(100) NOT NULL,
            oras VARCHAR(50) NOT NULL,
            data VARCHAR(50) NOT NULL,
            locatie VARCHAR(100) NOT NULL
        );
    ''')
    
    # daca tabela este goala, inseram datele initiale
    cur.execute('SELECT COUNT(*) FROM evenimente;')
    if cur.fetchone()[0] == 0:
        date_initiale = [
            ('Festivalul International de Film Transilvania (TIFF)', 'Cluj-Napoca', '29 Mai - 7 Iunie 2026', 'Piata Unirii'),
            ('Concert Filarmonica George Enescu', 'Bucuresti', '30 Mai 2026', 'Ateneul Roman'),
            ('Expozitie de Arta Contemporana', 'Timisoara', '1 Iunie 2026', 'Muzeul de Arta'),
            ('Festivalul de Teatru de Strada', 'Iasi', '5 Iunie 2026', 'Palatul Culturii')
        ]
        for ev in date_initiale:
            cur.execute(
                'INSERT INTO evenimente (titlu, oras, data, locatie) VALUES (%s, %s, %s, %s);',
                ev
            )
    
    conn.commit()
    cur.close()
    conn.close()

@app.route('/')
def home():
    return jsonify({
        "status": "success",
        "mesaj": "Bine ai venit la Agregatorul de Evenimente Culturale Romania v2 (cu baza de date)!"
    })

@app.route('/api/evenimente', methods=['GET'])
def get_evenimente():
    conn = get_db_connection()
    # dictionary cursor pentru a returna rezultatele ca liste de dictionare in loc de tuple
    cur = conn.cursor(cursor_factory=RealDictCursor)
    
    # adaug filtrare dupa oras daca este specificat in query params
    oras_filtru = request.args.get('oras')
    if oras_filtru:
        cur.execute('SELECT * FROM evenimente WHERE oras ILIKE %s;', (oras_filtru,))
    else:
        cur.execute('SELECT * FROM evenimente;')
        
    evenimente = cur.fetchall()
    cur.close()
    conn.close()
    return jsonify(evenimente)

if __name__ == '__main__':
    init_db()
    app.run(host='0.0.0.0', port=5000)