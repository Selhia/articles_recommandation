import logging
import json
import os
import io
import pickle
import pandas as pd
import numpy as np
import azure.functions as func
from surprise import SVD
from sklearn.metrics.pairwise import cosine_similarity
from azure.storage.blob import BlobServiceClient

# Variables d'environnement pour votre connexion Blob Storage
CONNECTION_STRING = os.environ.get("AZURE_STORAGE_CONNECTION_STRING")
CONTAINER_NAME = os.environ.get("AZURE_STORAGE_CONTAINER_NAME")
BLOB_NAME = "trained_model_and_assets.pkl"


# Utiliser une variable globale pour mettre en cache le modèle
global model_assets
model_assets = None

def load_model_from_blob():
    """Charge le modèle et les assets depuis Azure Blob Storage."""
    if not all([CONNECTION_STRING, CONTAINER_NAME]):
        logging.error("Variables d'environnement AZURE_STORAGE_CONNECTION_STRING ou BLOB_CONTAINER_NAME non définies.")
        return None
    try:
        blob_service_client = BlobServiceClient.from_connection_string(CONNECTION_STRING)
        blob_client = blob_service_client.get_blob_client(container=CONTAINER_NAME, blob=BLOB_NAME)
        
        blob_data = blob_client.download_blob().readall()
        return pickle.load(io.BytesIO(blob_data))
    except Exception as e:
        logging.error(f"Erreur lors du chargement du modèle depuis le stockage Blob: {e}")
        return None

def get_popular_articles(df_articles, df_clicks, num_recommendations=5):
    """
    Recommande les articles les plus populaires.
    """
    popular_article_ids = df_clicks['click_article_id'].value_counts().head(num_recommendations).index.tolist()
    
    # Pour garantir les titres, fusionner avec df_articles
    popular_articles_with_titles = df_articles[df_articles['article_id'].isin(popular_article_ids)]
    
    # Ordonner par popularité
    popular_articles_with_titles['popularity_rank'] = popular_articles_with_titles['article_id'].apply(lambda x: popular_article_ids.index(x))
    popular_articles_with_titles = popular_articles_with_titles.sort_values(by='popularity_rank')

    return [{'article_id': row['article_id'], 'title': row['title']} for _, row in popular_articles_with_titles.iterrows()]

def recommend_cf(df_clicks, df_articles, model_svd, user_id, num_recommendations=5):
    """
    Recommande des articles en utilisant le filtrage collaboratif (SVD).
    """
    articles_seen = df_clicks[df_clicks['user_id'] == user_id]['click_article_id'].tolist()
    all_articles = df_articles['article_id'].unique()
    articles_to_predict = [aid for aid in all_articles if aid not in articles_seen]
    
    predictions = [model_svd.predict(user_id, article_id) for article_id in articles_to_predict]
    predictions.sort(key=lambda x: x.est, reverse=True)
    
    recommended_articles = []
    for pred in predictions[:num_recommendations]:
        article_info = df_articles[df_articles['article_id'] == pred.iid].iloc[0]
        recommended_articles.append({
            'article_id': pred.iid, 
            'title': article_info['title'],
            'predicted_score': pred.est
        })
    return recommended_articles

def recommend_cb(df_clicks, df_articles_with_embeddings, article_embeddings_matrix, user_id, num_recommendations=5):
    """
    Recommande des articles en utilisant le filtrage basé sur le contenu.
    """
    user_clicked_ids = df_clicks[df_clicks['user_id'] == user_id]['click_article_id'].tolist()
    if not user_clicked_ids:
        return []

    # Créer un profil utilisateur en moyennant les embeddings des articles cliqués
    user_profile_embedding = np.mean([
        df_articles_with_embeddings[df_articles_with_embeddings['article_id'] == aid]['embedding'].iloc[0]
        for aid in user_clicked_ids if aid in df_articles_with_embeddings['article_id'].values
    ], axis=0).reshape(1, -1)

    all_embeddings = np.array(df_articles_with_embeddings['embedding'].tolist())
    similarities = cosine_similarity(user_profile_embedding, all_embeddings).flatten()
    
    similar_articles_df = pd.DataFrame({'article_id': df_articles_with_embeddings['article_id'], 'similarity': similarities})
    recommended_articles = similar_articles_df[~similar_articles_df['article_id'].isin(user_clicked_ids)] \
                                              .sort_values(by='similarity', ascending=False) \
                                              .head(num_recommendations)
    
    # Récupérer les titres pour la réponse
    recommended_articles_with_titles = pd.merge(recommended_articles, df_articles_with_embeddings[['article_id', 'title']], on='article_id')
    
    return [{'article_id': row['article_id'], 'title': row['title']} for _, row in recommended_articles_with_titles.iterrows()]

def recommend_hybrid(model_assets, user_id, num_recommendations=5, cf_threshold=5):
    """
    Logique de recommandation hybride.
    """
    df_clicks = model_assets['df_clicks']
    df_articles = model_assets['df_articles']
    model_svd = model_assets['model_svd']
    
    # Cas "Cold Start" : utilisateur non présent dans les données de clics
    if user_id not in df_clicks['user_id'].unique():
        return get_popular_articles(df_articles, df_clicks, num_recommendations)

    # Cas "Warm Start" ou "Hot Start" :
    user_history_count = df_clicks[df_clicks['user_id'] == user_id].shape[0]
    
    if user_history_count >= cf_threshold:
        # Hot Start : utilise le SVD (filtrage collaboratif)
        return recommend_cf(df_clicks, df_articles, model_svd, user_id, num_recommendations)
    else:
        # Warm Start : utilise le filtrage basé sur le contenu
        df_articles_with_embeddings = model_assets['df_articles_with_embeddings']
        article_embeddings_matrix = model_assets['article_embeddings_matrix']
        return recommend_cb(df_clicks, df_articles_with_embeddings, article_embeddings_matrix, user_id, num_recommendations)


def main(req: func.HttpRequest) -> func.HttpResponse:
    logging.info('Python HTTP trigger function processed a request.')

    # Charger le modèle depuis le Blob Storage s'il n'est pas déjà en cache
    global model_assets
    if model_assets is None:
        model_assets = load_model_from_blob()
        if model_assets is None:
            return func.HttpResponse(
                "Le service de recommandation n'est pas disponible pour le moment.",
                status_code=503,
                headers={"Access-Control-Allow-Origin": "*"}
            )

    user_id_str = req.params.get('user_id')
    if not user_id_str:
        try:
            req_body = req.get_json()
        except ValueError:
            return func.HttpResponse(
                "Veuillez passer un 'user_id' dans la chaîne de requête ou le corps de la requête.",
                status_code=400,
                headers={"Access-Control-Allow-Origin": "*"}
            )
        else:
            user_id_str = req_body.get('user_id')

    if user_id_str:
        try:
            user_id = int(user_id_str)
            recommendations = recommend_hybrid(model_assets, user_id)
            
            response_data = {
                "user_id": user_id,
                "recommendations": recommendations
            }
            return func.HttpResponse(
                json.dumps(response_data, indent=4),
                mimetype="application/json",
                status_code=200,
                headers={"Access-Control-Allow-Origin": "*"}
            )
        except (ValueError, KeyError) as e:
            return func.HttpResponse(
                f"Erreur lors du traitement de l'ID utilisateur ou du modèle: {str(e)}",
                status_code=500,
                headers={"Access-Control-Allow-Origin": "*"}
            )
    else:
        return func.HttpResponse(
            "Veuillez fournir un ID utilisateur valide.",
            status_code=400,
            headers={"Access-Control-Allow-Origin": "*"}
        )