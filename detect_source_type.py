"""
Module de détection de type de source d'images.

Ce module permet d'analyser des images pour déterminer leur type de source (par exemple, si elles proviennent d'un appareil photo ou d'un écran d'ordinateur). Il utilise des techniques d'analyse d'images pour détecter les caractéristiques spécifiques de chaque type de source.

Les fonctions de ce module peuvent être utilisées pour analyser des images individuelles ou des dossiers entiers d'images. Les résultats de l'analyse sont stockés dans des dictionnaires qui peuvent être facilement manipulés et enregistrés dans des fichiers CSV.
"""

import os
# Import du module os pour utiliser les fonctions de manipulation de fichiers et de dossiers

import csv
# Import du module csv pour lire et écrire des fichiers CSV

from PIL import Image
# Import du module PIL (Python Imaging Library) pour manipuler les images

import exifread
# Import du module exifread pour lire les métadonnées EXIF des images (non utilisé dans ce module)

# Résolutions typiques d'écrans d'appareils Apple
IPHONE_SCREENSHOTS = [
    (1170, 2532), (1284, 2778), (1125, 2436), (1242, 2688),
    (828, 1792), (750, 1334)
]
# Liste de tuples contenant les résolutions d'écran d'iPhone

IPAD_SCREENSHOTS = [
    (2048, 2732), (1668, 2388), (1640, 2360), (1536, 2048)
]
# Liste de tuples contenant les résolutions d'écran d'iPad

def is_close(a, b, tol=0.03):
    """
    Vérifie si deux valeurs sont proches l'une de l'autre.

    Args:
        a (float): La première valeur à comparer.
        b (float): La deuxième valeur à comparer.
        tol (float, optionnel): La tolérance de comparaison (par défaut : 0.03).

    Returns:
        bool: True si les valeurs sont proches, False sinon.
    """
    return abs(a - b) / max(a, b) < tol
# Fonction pour vérifier si deux valeurs sont proches l'une de l'autre

def is_screenshot_size(width, height, known_sizes):
    """
    Vérifie si une taille d'image correspond à une taille d'écran connue.

    Args:
        width (int): La largeur de l'image.
        height (int): La hauteur de l'image.
        known_sizes (list): La liste des tailles d'écran connues.

    Returns:
        bool: True si la taille d'image correspond à une taille d'écran connue, False sinon.
    """
    for ref_w, ref_h in known_sizes:
        if (is_close(width, ref_w) and is_close(height, ref_h)) or (is_close(width, ref_h) and is_close(height, ref_w)):
            return True
    return False
# Fonction pour vérifier si une taille d'image correspond à une taille d'écran connue

def guess_by_size(width, height):
    """
    Devine le type de source d'une image en fonction de sa taille.

    Args:
        width (int): La largeur de l'image.
        height (int): La hauteur de l'image.

    Returns:
        str: Le type de source de l'image (par exemple : "Screenshot iPhone", "Screenshot iPad", etc.).
    """
    wh = (width, height)
    whr = (height, width)
    if wh in IPHONE_SCREENSHOTS or whr in IPHONE_SCREENSHOTS:
        return "Screenshot iPhone"
    if wh in IPAD_SCREENSHOTS or whr in IPAD_SCREENSHOTS:
        return "Screenshot iPad"
    return None
# Fonction pour deviner le type de source d'une image en fonction de sa taille

from device_image_types import DEVICE_IMAGE_TYPES, IPHONE_MODELS, IPAD_MODELS, ORIENTATIONS, SOURCES, DEVICE_RESOLUTIONS, is_model_resolution, DEVICE_RESOLUTION_TOLERANCE
# Import des constantes et fonctions du module device_image_types

def get_device_and_orientation(width, height, tolerance=None):
    """
    Détecte le modèle d'appareil et l'orientation d'une image en fonction de sa taille.

    Args:
        width (int): La largeur de l'image.
        height (int): La hauteur de l'image.
        tolerance (float, optionnel): La tolérance de comparaison (par défaut : DEVICE_RESOLUTION_TOLERANCE).

    Returns:
        tuple: Un tuple contenant le modèle d'appareil et l'orientation de l'image.
    """
    # Détermine l'orientation principale selon le ratio largeur/hauteur
    orientation = "portrait" if height > width else "landscape"
    # Si aucune tolérance n'est fournie, utiliser la valeur globale
    if tolerance is None:
        tolerance = DEVICE_RESOLUTION_TOLERANCE
    # Boucle sur tous les modèles connus pour trouver le meilleur match
    for model, (ref_w, ref_h) in DEVICE_RESOLUTIONS.items():
        # Cas normal : la résolution correspond à celle du modèle (avec tolérance)
        if is_model_resolution(width, height, model, tolerance):
            return (model, orientation)
        # Cas split-screen vertical (largeur ≈ moitié, hauteur ≈ canonique)
        if abs(width - ref_w / 2) / ref_w < tolerance and abs(height - ref_h) / ref_h < tolerance:
            return (model, orientation + "_split")
        # Cas split-screen horizontal (hauteur ≈ moitié, largeur ≈ canonique)
        if abs(height - ref_h / 2) / ref_h < tolerance and abs(width - ref_w) / ref_w < tolerance:
            return (model, orientation + "_split")
    # Aucun modèle trouvé, retourne "unknown"
    return ("unknown", orientation)
# Fonction pour détecter le modèle d'appareil et l'orientation d'une image en fonction de sa taille

def detect_source_type(img_path):
    """
    Détermine le type de source d'une image.

    Args:
        img_path (str): Le chemin de l'image.

    Returns:
        str: Le type de source de l'image (par exemple : "Photo", "Screenshot", etc.).
    """
    # Dummy : à remplacer par une vraie détection (via OCR, pixels, etc.)
    # Pour l'instant, retourne "Photo" par défaut
    return "Photo"
# Fonction pour déterminer le type de source d'une image

def analyze_image(img_path):
    """
    Analyse une image pour déterminer son type de source et son modèle d'appareil.

    Args:
        img_path (str): Le chemin de l'image.

    Returns:
        dict: Un dictionnaire contenant les informations sur l'image (type de source, modèle d'appareil, etc.).
    """
    from PIL import Image
    with Image.open(img_path) as img:
        width, height = img.size
    device, orientation = get_device_and_orientation(width, height)
    source = detect_source_type(img_path)
    print(f"[LOG] {img_path} | resolution: {width}x{height} | device: {device}, orientation: {orientation}, source: {source}")
    return {"device": device, "orientation": orientation, "source": source}
# Fonction pour analyser une image

def impr(folder):
    """
    Analyse les images d'un dossier pour déterminer leur type de source et leur modèle d'appareil.

    Args:
        folder (str): Le chemin du dossier.

    Returns:
        list: Une liste de dictionnaires contenant les informations sur les images (type de source, modèle d'appareil, etc.).
    """
    results = []
    for filename in sorted(os.listdir(folder)):
        if filename.lower().endswith(('.png', '.jpg', '.jpeg', '.bmp')):
            path = os.path.join(folder, filename)
            typ = analyze_image(path)
            results.append({'filename': filename, 'type': typ})
            print(f"{filename} : {typ}")
    return results
# Fonction pour analyser les images d'un dossier

def analyze_folder(folder):
    """
    Analyse les images d'un dossier pour déterminer leur type de source et leur modèle d'appareil.

    Args:
        folder (str): Le chemin du dossier.

    Returns:
        list: Une liste de dictionnaires contenant les informations sur les images (type de source, modèle d'appareil, etc.).
    """
    results = []
    for filename in sorted(os.listdir(folder)):
        if filename.lower().endswith(('.png', '.jpg', '.jpeg', '.bmp')):
            path = os.path.join(folder, filename)
            typ = analyze_image(path)
            results.append({'filename': filename, 'type': typ})
            print(f"{filename} : {typ}")
    return results

if __name__ == "__main__":
    folder = os.path.join(os.path.dirname(__file__), "screenshots")
    output_csv = "screenshot_analysis.csv"
    res = analyze_folder(folder)
    # Sauvegarde CSV
    with open(output_csv, "w", newline='', encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=["filename", "type"])
        writer.writeheader()
        writer.writerows(res)
    print(f"\nAnalyse terminée. Résultats enregistrés dans {output_csv}")
