"""
Module main.py
Pipeline principal pour l'extraction de musique à partir de screenshots Apple.
Ce script détecte le device, extrait le texte via OCR, recherche la musique sur YouTube, et sauvegarde les résultats.
"""

# Import du module os pour la gestion des chemins, dossiers et variables d'environnement
import os
# Import de PIL (Pillow) pour ouvrir et manipuler les images
from PIL import Image
# Import de pytesseract pour l'OCR
import pytesseract
# Import de la fonction de crop adaptée au device/type
from where_to_crop import get_crop_box
# Import de la fonction de recherche YouTube
from music_search import search_youtube_api
# Import de la fonction d'analyse device/source
from detect_source_type import analyze_image
# Import de la liste des combinaisons device/orientation/source supportées
from device_image_types import DEVICE_IMAGE_TYPES
# Import du module sys pour la gestion des arguments et de la sortie
import sys
# Import du module csv pour la sauvegarde des résultats
import csv
# Import du module datetime pour le timestamp dans les logs
import datetime


def process_image(image_path, device_type):
    """
    Extrait le texte OCR d'une image, après crop adapté selon le device/type.

    Args:
        image_path (str): Chemin vers l'image à traiter.
        device_type (str): Chaîne décrivant le device/orientation/source (pour le crop).

    Returns:
        str: Texte extrait de l'image (nettoyé).
    """
    # Ouvre l'image à partir du chemin fourni
    img = Image.open(image_path)
    # Détermine la zone de crop optimale selon le device/type
    crop_box = get_crop_box(img, os.path.basename(image_path), device_type=device_type)
    if crop_box:
        # Si un crop est défini, on applique le crop
        cropped = img.crop(crop_box)
        if os.environ.get("DEBUG_CROP") == "1":
            # Sauvegarde le crop dans un sous-dossier 'debug_crops' (crée-le si besoin)
            os.makedirs("debug_crops", exist_ok=True)
            cropped.save(os.path.join("debug_crops", os.path.basename(image_path)))
        img = cropped
    # Effectue l'OCR sur l'image (croppée ou non)
    text = pytesseract.image_to_string(img, lang='eng')
    # Retourne le texte extrait, nettoyé des espaces superflus
    return text.strip()


def log_full(info, log_path="main_pipeline.log"):
    """
    Ajoute une ligne détaillée dans le fichier log principal pour chaque image traitée.

    Args:
        info (dict): Dictionnaire contenant les infos à logger (image, device_type, texte, youtube).
        log_path (str): Chemin du fichier log (par défaut 'main_pipeline.log').
    """
    with open(log_path, "a", encoding="utf-8") as f:
        # Récupère la date et l'heure courante pour le log
        now = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        # Écrit une ligne formatée avec toutes les infos importantes
        f.write(f"[{now}] IMAGE: {info['image']} | TYPE: {info['device_type']} | TEXTE: {info['extracted_text']} | YOUTUBE: {info['youtube_url']}\n")


def main():
    """
    Pipeline principal :
    - Parcourt tous les screenshots d'un dossier
    - Détecte le device et le contexte
    - Extrait le texte OCR avec crop adapté
    - Recherche la musique sur YouTube
    - Sauvegarde les résultats et les logs
    """
    # Détermine le dossier contenant les screenshots à traiter
    screenshots_dir = os.path.join(os.path.dirname(__file__), "screenshots")
    # Récupère la clé API YouTube depuis les variables d'environnement
    YT_API_KEY = os.environ.get("YT_API_KEY")
    if not YT_API_KEY:
        # Affiche une erreur et arrête le script si la clé est absente
        print("Erreur : Variable d'environnement YT_API_KEY absente.")
        sys.exit(1)

    results = []  # Liste pour stocker les résultats finaux
    # Parcourt tous les fichiers du dossier screenshots
    for filename in sorted(os.listdir(screenshots_dir)):
        # Vérifie que le fichier est une image supportée
        if filename.lower().endswith(('.png', '.jpg', '.jpeg', '.bmp')):
            img_path = os.path.join(screenshots_dir, filename)
            print(f"\n=== Traitement de {filename} ===")

            # 1. Détection du device, de l'orientation et du type/source
            info = analyze_image(img_path)
            device = info["device"]
            orientation = info["orientation"]
            source = info["source"]

            # Tri 1 : vérifie si le device est connu
            device_known = any(d["device"] == device for d in DEVICE_IMAGE_TYPES)
            if not device_known:
                print(f"Appareil non reconnu : {device}. Fichier ignoré.")
                continue

            # Tri 2 : vérifie si la combinaison device/orientation/source est supportée
            match = next((d for d in DEVICE_IMAGE_TYPES if d["device"] == device and d["orientation"] == orientation and d["source"] == source), None)
            if not match:
                print(f"Type d'image/source non reconnu pour {device}, {orientation}, {source}. Fichier ignoré.")
                continue

            # Si tout est OK, construit la chaîne de type
            device_type = f"{device} {orientation} {source}"
            print(f"Type détecté : {device_type}")

            # 2. OCR avec crop adapté au device/type
            extracted_text = process_image(img_path, device_type)
            print(f"Texte extrait : {extracted_text}")

            if not extracted_text.strip():
                # Si aucun texte n'est extrait, log et passe au suivant
                print("→ Aucun texte extrait, passage au suivant.")
                log_full({
                    "image": filename,
                    "device_type": device_type,
                    "extracted_text": "",
                    "youtube_title": "",
                    "youtube_url": "AUCUN RESULTAT"
                })
                continue

            # 3. Recherche musicale YouTube (requête enrichie)
            query = f"{extracted_text} music hq"
            music_results = search_youtube_api(query, api_key=YT_API_KEY)
            if not music_results:
                # Si aucun résultat, log et passe au suivant
                print("→ Aucun résultat musical trouvé.")
                log_full({
                    "image": filename,
                    "device_type": device_type,
                    "extracted_text": extracted_text,
                    "youtube_title": "",
                    "youtube_url": "AUCUN RESULTAT"
                })
                continue

            # Prend le meilleur résultat YouTube
            best = music_results[0]
            print(f"Meilleur résultat YouTube : {best['title']} → {best['url']}")

            # Ajoute le résultat à la liste finale et log
            results.append({
                "image": filename,
                "device_type": device_type,
                "extracted_text": extracted_text,
                "youtube_title": best["title"],
                "youtube_url": best["url"]
            })
            log_full({
                "image": filename,
                "device_type": device_type,
                "extracted_text": extracted_text,
                "youtube_title": best["title"],
                "youtube_url": best["url"]
            })

    # Sauvegarde des résultats dans un fichier CSV
    output_csv = "main_pipeline_results.csv"
    with open(output_csv, "w", newline='', encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=["image", "device_type", "extracted_text", "youtube_title", "youtube_url"])
        writer.writeheader()
        writer.writerows(results)
    print(f"\nPipeline terminé. Résultats enregistrés dans {output_csv} et main_pipeline.log")


if __name__ == "__main__":
    # Point d'entrée du script si exécuté directement
    main()
