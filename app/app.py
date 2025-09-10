import requests
from flask import Flask, render_template, request, jsonify

app = Flask(__name__)

# URL de base de votre fonction Azure (sans les paramètres)
# Assurez-vous que cette URL est correcte et qu'elle ne contient pas le paramètre '?code='
AZURE_FUNCTION_URL_BASE = "https://recommandationapp-bed3ftg0apbce2a4.francecentral-01.azurewebsites.net/api/RecommenderFunction"

# Votre clé d'authentification
AZURE_FUNCTION_CODE = "I6g5w-LElDwADCIEAfqF6wfEvJPJDjVrZL5YgUSzli4NAzFuZlFCgQ=="

@app.route('/')
def index():
    """
    Cette route sert la page d'accueil avec le formulaire de recommandation.
    """
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
        # La bibliothèque 'requests' gère correctement l'ajout des paramètres
        params = {
            'code': AZURE_FUNCTION_CODE,
            'user_id': user_id
        }
        
        response = requests.get(AZURE_FUNCTION_URL_BASE, params=params)
        response.raise_for_status()
        
        recommendations = response.json().get('recommendations', [])
        return jsonify(recommendations)
    except requests.exceptions.RequestException as e:
        return jsonify({"error": f"Erreur de connexion à l'API: {str(e)}"}), 500

if __name__ == '__main__':
    app.run(debug=True)