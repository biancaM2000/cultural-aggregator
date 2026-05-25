from flask import Flask, jsonify

app = Flask(__name__)

# Date simulate pentru agregatorul de evenimente
evenimente = [
    {
        "id": 1,
        "oras": "Cluj-Napoca",
        "titlu": "Festivalul International de Film Transilvania (TIFF)",
        "data": "Iunie 2026",
        "categorie": "Film"
    },
    {
        "id": 2,
        "oras": "Bucuresti",
        "titlu": "Concert special la Ateneul Roman",
        "data": "30 Mai 2026",
        "categorie": "Muzica Clasica"
    },
    {
        "id": 3,
        "oras": "Timișoara",
        "titlu": "Expozitie de Arta Contemporana",
        "data": "Iunie 2026",
        "categorie": "Arta"
    },
    {
        "id": 4,
        "oras": "Iasi",
        "titlu": "Festivalul de Teatru Tanar",
        "data": "Mai 2026",
        "categorie": "Teatru"
    }
]

@app.route('/')
def home():
    return jsonify({
        "status": "Online",
        "mesaj": "Bine ai venit la Agregatorul de Evenimente Culturale România!",
        "versiuni_api": "/api/evenimente"
    })

@app.route('/api/evenimente')
def get_evenimente():
    return jsonify(evenimente)

if __name__ == '__main__':
    # Rulam pe portul 5000, accesibil de oriunde (0.0.0.0) pentru Docker
    app.run(host='0.0.0.0', port=5000)
