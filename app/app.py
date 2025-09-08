import requests
from flask import Flask, render_template, request, jsonify

app = Flask(__name__)

# Remplacez cette URL par l'URL de votre Azure Function après le déploiement
AZURE_FUNCTION_URL = "VOTRE_URL_AZURE_FUNCTION"

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/recommend', methods=['POST'])
def recommend():
    """
    Appelle la fonction Azure pour obtenir les recommandations
    basées sur l'ID utilisateur fourni.
    """
    user_id = request.form.get('user_id')
    if not user_id:
        return jsonify({"error": "Veuillez entrer un ID utilisateur."}), 400

    try:
        response = requests.get(f"{AZURE_FUNCTION_URL}?user_id={user_id}")
        response.raise_for_status()
        
        recommendations = response.json().get('recommendations', [])
        return jsonify(recommendations)
    except requests.exceptions.RequestException as e:
        return jsonify({"error": f"Erreur de connexion à l'API: {str(e)}"}), 500

if __name__ == '__main__':
    app.run(debug=True)