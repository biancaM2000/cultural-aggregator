from flask import Flask, jsonify, request, render_template
import os
import psycopg2
from psycopg2.extras import RealDictCursor
import time
import requests
from bs4 import BeautifulSoup

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
            print("Baza de date nu este gata, reincearca in cateva secunde...")
            time.sleep(2)
    raise Exception("Nu s-a putut stabili conexiunea cu baza de date.")

def culege_date_reale():
    conn = get_db_connection()
    cur = conn.cursor()
    
    cur.execute('TRUNCATE TABLE evenimente;')
    
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'
    }
    
    print("Începe colectarea datelor de pe Zile și Nopți...")
    try:
        # Colectare evenimente din Bucuresti - zile si nopti
        url_zn = "https://zilesinopti.ro/bucuresti/evenimente/"
        raspuns = requests.get(url_zn, headers=headers, timeout=10)
        if raspuns.status_code == 200:
            soup = BeautifulSoup(raspuns.text, 'html.parser')
            articole = soup.find_all('article', class_='teaser', limit=5)
            
            for art in articole:
                titlu_elem = art.find('h2')
                if titlu_elem:
                    titlu = titlu_elem.text.strip()
                    # Extragem categoria sau data din tag-uri
                    cat_elem = art.find('span', class_='category')
                    categorie = cat_elem.text.strip() if cat_elem else "Cultură"
                    
                    cur.execute(
                        'INSERT INTO evenimente (titlu, oras, data, categorie) VALUES (%s, %s, %s, %s);',
                        (titlu, 'Bucuresti', 'Mai-Iunie 2026', categorie)
                    )
    except Exception as e:
        print(f"Eroare la colectarea de pe Zile și Nopți: {e}")

    print("Colectare date de pe IaBilet...")
    try:
        # Folosim un endpoint public/mock simulat din IaBilet pentru a extrage festivaluri din tara
        # Pentru a evita blocajele stricte de IP pe serverele AWS, simulez colecatrea cu date hardcodate   
        evenimente_iabilet = [
            ("Festivalul Rock la Castel", "Timisoara", "12-14 Iunie 2026", "Concert"),
            ("Stand-up Comedy Show National", "Cluj-Napoca", "05 Iunie 2026", "Teatru/Divertisment"),
            ("Opera Live în Piața Mare", "Iasi", "20 Iunie 2026", "Muzica"),
            ("Festivalul de Jazz", "Cluj-Napoca", "18 Iunie 2026", "Concert")
        ]
        
        for titlu, oras, data, categorie in evenimente_iabilet:
            cur.execute(
                'INSERT INTO evenimente (titlu, oras, data, categorie) VALUES (%s, %s, %s, %s);',
                (titlu, oras, data, categorie)
            )
            
    except Exception as e:
        print(f"Eroare la colectarea de pe IaBilet: {e}")

    conn.commit()
    cur.close()
    conn.close()
    print("Colectarea datelor s-a finalizat cu succes!")

def init_db():
    conn = get_db_connection()
    cur = conn.cursor()
    cur.execute('''
        CREATE TABLE IF NOT EXISTS evenimente (
            id SERIAL PRIMARY KEY,
            titlu VARCHAR(250) NOT NULL,
            oras VARCHAR(50) NOT NULL,
            data VARCHAR(50) NOT NULL,
            categorie VARCHAR(50) NOT NULL
        );
    ''')
    conn.commit()
    cur.close()
    conn.close()
    
    # culege date reale 
    culege_date_reale()

@app.route('/')
def home():
    conn = get_db_connection()
    cur = conn.cursor(cursor_factory=RealDictCursor)
    oras_filtru = request.args.get('oras')
    
    if oras_filtru:
        cur.execute('SELECT * FROM evenimente WHERE oras ILIKE %s ORDER BY id ASC;', (oras_filtru,))
    else:
        cur.execute('SELECT * FROM evenimente ORDER BY id ASC;')
        
    evenimente = cur.fetchall()
    cur.close()
    conn.close()
    return render_template('index.html', evenimente=evenimente)

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