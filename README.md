Projet de Système de Recommandation Hybride pour Articles
Ce projet a pour but de créer un système de recommandation d'articles en utilisant une approche hybride pour gérer différents profils d'utilisateurs. L'application est conçue pour être déployée sur Azure, avec une fonction serverless pour la logique de recommandation (Azure Function) et une interface utilisateur web (Flask/Streamlit) pour l'interaction.

🌟 Caractéristiques principales
Système de recommandation hybride : Combine trois approches pour optimiser la pertinence des recommandations.

Articles populaires : Pour les nouveaux utilisateurs (stratégie "cold start").

Filtrage basé sur le contenu : Pour les utilisateurs avec un historique de clics limité (stratégie "warm start").

Filtrage collaboratif (SVD) : Pour les utilisateurs avec un historique de clics riche (stratégie "hot start").

Architecture Serverless : La logique métier est déployée en tant qu'Azure Function, garantissant une mise à l'échelle automatique et une exécution rentable.

Interface utilisateur simple : Une application Flask ou Streamlit pour interagir avec le système de recommandation.

🚀 Structure du projet
Le projet est organisé de la manière suivante :

app/ : Contient le code de l'application web (Flask ou Streamlit) et ses dépendances.

azure-function/ : Contient le code de la fonction Azure, ses configurations et le modèle de recommandation.

MVP_avec_surprise_corrige_par_gemini.ipynb : Le notebook Jupyter original utilisé pour le développement et l'entraînement du modèle.

🛠️ Configuration et installation
Prérequis

Python 3.9 ou supérieur

Pip (gestionnaire de paquets Python)

Un compte Azure

Les outils Azure Functions Core Tools (pour le développement local)

Étape 1 : Entraînement et exportation du modèle

Ouvrez le notebook MVP_avec_surprise_corrige_par_gemini.ipynb dans Google Colab ou Jupyter.

Exécutez toutes les cellules pour entraîner les modèles et générer le fichier trained_model_and_assets.pkl.

Téléchargez ce fichier sur votre machine locale.

Étape 2 : Déploiement du modèle sur Azure Blob Storage

Le fichier de modèle étant trop volumineux pour être géré par Git, il doit être stocké sur Azure Blob Storage.

Dans votre compte Azure, créez un conteneur Blob (par exemple, recommender-models).

Téléchargez le fichier trained_model_and_assets.pkl dans ce conteneur.

Récupérez la chaîne de connexion ("Connection String") de votre compte de stockage.

Étape 3 : Déploiement de l'Azure Function

Accédez au dossier azure-function/.

Dans les paramètres d'application de votre fonction sur le portail Azure, ajoutez les variables d'environnement suivantes :

AZURE_STORAGE_CONNECTION_STRING : La chaîne de connexion de votre compte de stockage.

BLOB_CONTAINER_NAME : Le nom de votre conteneur Blob (ex: recommender-models).

Déployez la fonction Azure en utilisant les outils de développement (Visual Studio Code, Azure CLI, etc.).

Une fois déployée, copiez l'URL de la fonction HTTP.

Étape 4 : Exécution de l'application Web

Accédez au dossier app/.

Installez les dépendances : pip install -r requirements.txt.

Dans le fichier app.py, remplacez l'URL VOTRE_URL_AZURE_FUNCTION par l'URL de votre fonction Azure.

Exécutez l'application : flask run 

Ouvrez votre navigateur et naviguez vers l'URL affichée pour interagir avec l'application.

