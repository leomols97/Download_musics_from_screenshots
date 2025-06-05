import os
from googleapiclient.discovery import build
import datetime
import re

def search_youtube_api(query, api_key, max_results=5):
    youtube = build("youtube", "v3", developerKey=api_key)
    request = youtube.search().list(
        part="snippet",
        q=query,
        maxResults=max_results,
        type="video",
        videoCategoryId="10" # catégorie Musique
    )
    response = request.execute()
    results = []
    for item in response.get("items", []):
        title = item["snippet"]["title"]
        description = item["snippet"].get("description", "")
        video_id = item["id"]["videoId"]
        url = f"https://www.youtube.com/watch?v={video_id}"
        if is_valid_music_result(title, description):
            results.append({"platform": "YouTube", "title": title, "url": url})
    return results


def log_url(result):
    now = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    with open("music_search.log", "a", encoding="utf-8") as f:
        for r in result:
            f.write(f"[{now}] [{r['platform']}] {r['title']} -> {r['url']}\n")

def is_valid_music_result(title, description=None):
    # Liste noire de mots/phrases à éviter
    blacklist = [
        r"official\s*video", r"clip officiel", r"vidéo officielle",
        r"lyrics?", r"paroles?", r"karaok[eé]", r"cover",
        r"remix", r"live", r"direct", r"concert", r"émission",
        r"making of", r"audio\s*officiel", r"visualiser", r"visualizer", r"instrumental", r"film"
    ]
    pattern = re.compile('|'.join(blacklist), re.IGNORECASE)
    # On filtre sur le titre et la description
    if pattern.search(title):
        return False
    if description and pattern.search(description):
        return False
    return True

def best_music_result(results, query):
    """
    Retourne le résultat le plus pertinent parmi les résultats valides.
    - Score fort si le titre contient exactement tous les mots du query.
    - Sinon, résultat avec le titre le plus court.
    """
    query_words = set(query.lower().split())
    scored = []
    for r in results:
        title = r['title'].lower()
        # Score : nombre de mots du query présents dans le titre
        score = sum(1 for w in query_words if w in title)
        # Bonus négatif pour la longueur (plus c'est court, mieux c'est)
        score -= len(title) / 100
        scored.append((score, r))
    # Trie par score décroissant
    scored.sort(key=lambda x: x[0], reverse=True)
    return scored[0][1] if scored else None

if __name__ == "__main__":
    query = input("Titre + Artiste : ")
    full_query = f"{query} music hq"

    YT_API_KEY = os.environ.get("YT_API_KEY")
    if not YT_API_KEY:
        print("Erreur : La clé API YouTube doit être définie dans la variable d'environnement YT_API_KEY.")
        exit(1)

    res = search_youtube_api(full_query, api_key=YT_API_KEY)
    if not res:
        print("Aucun résultat satisfaisant trouvé.")
    else:
        # Sélection du meilleur résultat IA/simple scoring
        best = best_music_result(res, query)
        print("\nMeilleur résultat :")
        print(f"[{best['platform']}] {best['title']} -> {best['url']}")
        # Log seulement le meilleur
        log_url([best])