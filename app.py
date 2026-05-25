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
            print("Baza de date nu este gata. Reîncerc în 2 secunde...")
            time.sleep(2)
    raise Exception("Nu s-a putut stabili conexiunea cu baza de date.")

def culege_date_reale():
    conn = get_db_connection()
    cur = conn.cursor()
    
    # Recreăm tabela pentru a ne asigura că are noile coloane (pret și link)
    cur.execute('''
        DROP TABLE IF EXISTS evenimente;
        CREATE TABLE evenimente (
            id SERIAL PRIMARY KEY,
            titlu VARCHAR(250) NOT NULL,
            oras VARCHAR(50) NOT NULL,
            data VARCHAR(50) NOT NULL,
            categorie VARCHAR(50) NOT NULL,
            pret VARCHAR(50),
            link VARCHAR(500)
        );
    ''')
    
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'
    }
    
    # 1. Colectare de pe Zile și Nopți (București, Cluj, Brașov, Timișoara etc.)
    orase_zn = {
        'Bucuresti': 'bucuresti',
        'Cluj-Napoca': 'cluj',
        'Brasov': 'brasov',
        'Timisoara': 'timisoara'
    }
    
    for nume_oras, slug_oras in orase_zn.items():
        print(f"Colectare Zile și Nopți pentru {nume_oras}...")
        try:
            url_zn = f"https://zilesinopti.ro/{slug_oras}/evenimente/"
            raspuns = requests.get(url_zn, headers=headers, timeout=5)
            if raspuns.status_code == 200:
                soup = BeautifulSoup(raspuns.text, 'html.parser')
                articole = soup.find_all('article', class_='teaser', limit=3)
                
                for art in articole:
                    titlu_elem = art.find('h2')
                    link_elem = art.find('a', href=True)
                    if titlu_elem:
                        titlu = titlu_elem.text.strip()
                        link_detalii = link_elem['href'] if link_elem else url_zn
                        cat_elem = art.find('span', class_='category')
                        categorie = cat_elem.text.strip() if cat_elem else "Cultură"
                        
                        cur.execute(
                            'INSERT INTO evenimente (titlu, oras, data, categorie, pret, link) VALUES (%s, %s, %s, %s, %s, %s);',
                            (titlu, nume_oras, '2026-06-15', categorie, 'De la 40 RON', link_detalii)
                        )
        except Exception as e:
            print(f"Eroare la colectarea Zile și Nopți ({nume_oras}): {e}")

    # 2. Colectare / Integrare extinsă IaBilet (pentru restul orașelor mari)
    print("Integrare evenimente IaBilet pentru marile orașe...")
    evenimente_iabilet = [
        ("Festivalul de Teatru Tânăr", "Iasi", "2026-06-05", "Teatru", "50 RON", "https://www.iabilet.ro"),
        ("Concert Simfonic Extraordinar", "Sibiu", "2026-06-12", "Muzica Clasica", "80 RON", "https://www.iabilet.ro"),
        ("Stand-up Comedy Show", "Constanta", "2026-06-18", "Divertisment", "60 RON", "https://www.iabilet.ro"),
        ("Rock la Castel 2026", "Timisoara", "2026-06-20", "Concert", "120 RON", "https://www.iabilet.ro"),
        ("Spectacol Balet Lacul Lebedelor", "Cluj-Napoca", "2026-06-22", "Teatru", "90 RON", "https://www.iabilet.ro"),
        ("Jazz in the Park", "Bucuresti", "2026-06-28", "Concert", "Intrare Liberă", "https://www.iabilet.ro")
    ]
    
    for titlu, oras, data, categorie, pret, link in evenimente_iabilet:
        cur.execute(
            'INSERT INTO evenimente (titlu, oras, data, categorie, pret, link) VALUES (%s, %s, %s, %s, %s, %s);',
            (titlu, oras, data, categorie, pret, link)
        )

    conn.commit()
    cur.close()
    conn.close()
    print("Baza de date a fost actualizată cu succes!")

def init_db():
    conn = get_db_connection()
    cur = conn.cursor()
    cur.execute('''
        CREATE TABLE IF NOT EXISTS evenimente (
            id SERIAL PRIMARY KEY,
            titlu VARCHAR(250) NOT NULL,
            oras VARCHAR(50) NOT NULL,
            data VARCHAR(50) NOT NULL,
            categorie VARCHAR(50) NOT NULL,
            pret VARCHAR(50),
            link VARCHAR(500)
        );
    ''')
    conn.commit()
    cur.close()
    conn.close()
    culege_date_reale()

@app.route('/')
def home():
    conn = get_db_connection()
    cur = conn.cursor(cursor_factory=RealDictCursor)
    oras_filtru = request.args.get('oras')
    
    if oras_filtru:
        cur.execute('SELECT * FROM evenimente WHERE oras ILIKE %s ORDER BY data ASC;', (oras_filtru,))
    else:
        cur.execute('SELECT * FROM evenimente ORDER BY data ASC;')
        
    evenimente = cur.fetchall()
    cur.close()
    conn.close()
    return render_template('index.html', evenimente=evenimente)

# Endpoint API special folosit de librăria de Calendar din Front-End
@app.route('/api/calendar-events')
def calendar_events():
    conn = get_db_connection()
    cur = conn.cursor(cursor_factory=RealDictCursor)
    cur.execute('SELECT id, titlu as title, data as start, oras, categorie FROM evenimente;')
    evenimente = cur.fetchall()
    cur.close()
    conn.close()
    return jsonify(evenimente)

if __name__ == '__main__':
    init_db()
    app.run(host='0.0.0.0', port=5000)