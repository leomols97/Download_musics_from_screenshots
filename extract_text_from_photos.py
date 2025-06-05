"""
Module extract_text_from_photos.py
Ce module gère l'extraction de texte OCR à partir de photos ou de screenshots Apple.
Il utilise pytesseract pour l'OCR, PIL pour la gestion d'image, et permet d'appliquer un crop adapté selon le device, l'orientation et le type de contenu (Shazam, YouTube, etc).

Fonctionnalités :
- Tolérance de crop globale et paramétrable par device/type
- Fonctions spécialisées pour chaque type de contenu
- Dispatcher qui applique la bonne logique de crop/ocr selon le contexte
"""

import os
import re
import numpy as np
import pytesseract
from PIL import Image

# Tolérance de crop par (device, content_type), valeurs par défaut ajustables
CROP_TOLERANCE = {
    ("iPhone", "Shazam"): 0.01,  # très précis pour Dynamic Island
    ("iPhone", "YouTube"): 0.03,
    ("iPad", "YouTube"): 0.04,
    # ... ajouter d'autres cas si besoin
    "default": 0.015
}


def get_crop_box(device, orientation, content_type, width, height):
    """
    Retourne la box de crop (left, upper, right, lower) en pixels selon le device, orientation et type de contenu.
    Les proportions sont ajustées pour chaque cas d'usage (voir consignes utilisateur).
    """
    # iPhone Shazam (Dynamic Island ou notif en haut)
    if device == "iPhone" and content_type == "Shazam":
        # Zone très haute de l'écran, Dynamic Island (environ 0 à 13% hauteur)
        top = 0
        bottom = int(0.13 * height)
        return (0, top, width, bottom)
    # iPhone YouTube
    if device == "iPhone" and content_type == "YouTube":
        # Zone juste au-dessus du nombre de vues (généralement ~65% à 80% hauteur)
        top = int(0.65 * height)
        bottom = int(0.80 * height)
        return (0, top, width, bottom)
    # iPad YouTube
    if device == "iPad" and content_type == "YouTube":
        # Zone juste au-dessus du nombre de vues, mais sur iPad (adapter)
        top = int(0.60 * height)
        bottom = int(0.78 * height)
        return (0, top, width, bottom)
    # iPhone Shazam Notification (titre + artiste en haut)
    if device == "iPhone" and content_type == "ShazamNotif":
        top = 0
        bottom = int(0.17 * height)
        return (0, top, width, bottom)
    # iPhone Shazam/Apple Music (titre + artiste sous Dynamic Island)
    if device == "iPhone" and content_type == "AppleMusic":
        top = int(0.13 * height)
        bottom = int(0.24 * height)
        return (0, top, width, bottom)
    # fallback : full image
    return (0, 0, width, height)


def extract_shazam_text(img, device, orientation):
    """
    Extrait le texte clé (titre + artiste) d'une notification Shazam sur iPhone.
    S'arrête dès qu'une ligne contient '©' ou un nombre, et ne garde que les lignes juste au-dessus.
    Ne retourne jamais plus de 2 lignes, et jamais de ligne vide, numérique seule, copyright ou bouton.
    """
    width, height = img.size
    crop_box = get_crop_box(device, orientation, "Shazam", width, height)
    cropped = img.crop(crop_box)
    text = pytesseract.image_to_string(cropped, lang='eng')
    lines = []
    for l in text.splitlines():
        l_strip = l.strip()
        if not l_strip:
            continue
        if l_strip.startswith('©') or re.match(r'^\d+$', l_strip) or '©' in l_strip or re.match(r'.*\d+.*', l_strip):
            break
        lines.append(l_strip)
        if len(lines) == 2:
            break
    return " ".join(lines) if lines else ""


def extract_shazam_notif_text(img, device, orientation):
    """
    Extrait le texte clé d'une notification Shazam sur Dynamic Island (ex: 'Wait Mustafa Hussam').
    Ne retourne que les 2 premières lignes non vides, jamais de copyright, jamais de nombre seul.
    """
    width, height = img.size
    crop_box = get_crop_box(device, orientation, "ShazamNotif", width, height)
    cropped = img.crop(crop_box)
    text = pytesseract.image_to_string(cropped, lang='eng')
    lines = []
    for l in text.splitlines():
        l_strip = l.strip()
        if not l_strip:
            continue
        if l_strip.startswith('©') or re.match(r'^\d+$', l_strip) or '©' in l_strip or re.match(r'.*\d+.*', l_strip):
            break
        lines.append(l_strip)
        if len(lines) == 2:
            break
    return " ".join(lines) if lines else ""


def extract_apple_music_text(img, device, orientation):
    """
    Extrait le texte clé (titre + artiste) depuis Apple Music ou Shazam sous Dynamic Island.
    S'arrête dès qu'une ligne contient '©' ou un nombre, et ne garde que les lignes juste au-dessus.
    """
    width, height = img.size
    crop_box = get_crop_box(device, orientation, "AppleMusic", width, height)
    cropped = img.crop(crop_box)
    text = pytesseract.image_to_string(cropped, lang='eng')
    lines = []
    for l in text.splitlines():
        l_strip = l.strip()
        if not l_strip:
            continue
        if l_strip.startswith('©') or re.match(r'^\d+$', l_strip) or '©' in l_strip or re.match(r'.*\d+.*', l_strip):
            break
        lines.append(l_strip)
        if len(lines) == 2:
            break
    return " ".join(lines) if lines else ""


def extract_youtube_text(img, device, orientation):
    """
    Extrait dynamiquement le titre complet d'une vidéo YouTube sur iPhone/iPad.
    - Détecte la barre de lecture (fine ligne blanche/grise/rouge, tolérance sur la couleur, typiquement à 65-75% hauteur sur iPhone, 85-93% sur iPad)
    - Repère la ligne 'vues/views' via regex ([0-9][0-9\., kKmM]*\s*(vues|views))
    - Fait l'OCR uniquement entre ces deux bornes
    - Filtre strictement le texte : jamais de ligne vide, numérique seule, copyright, ni la ligne 'vues/views' ou ce qui est en dessous
    """
    img_array = np.array(img.convert('RGB'))
    h, w, _ = img_array.shape
    # 1. Détection de la barre de lecture (ligne fine blanche/grise/rouge)
    barre_lecture_y = None
    search_start = int(0.65 * h) if device == 'iPhone' else int(0.85 * h)
    search_end = int(0.93 * h) if device == 'iPad' else int(0.80 * h)
    for y in range(search_start, search_end):
        line = img_array[y, :, :]
        # Cherche une ligne quasi-unie blanche/grise/rouge (tolérance sur la couleur)
        if np.mean(np.abs(line - [255,255,255])) < 18 or np.mean(np.abs(line - [230,230,230])) < 18 or np.mean(np.abs(line - [200,200,200])) < 22 or np.mean(np.abs(line - [220,0,0])) < 30:
            # Ligne candidate
            if np.std(line, axis=0).mean() < 25:  # Assez uniforme
                barre_lecture_y = y
                break
    # 2. OCR sur la zone basse pour repérer la ligne 'vues/views'
    vues_views_y = None
    ocr_zone_top = barre_lecture_y+1 if barre_lecture_y else search_start
    ocr_zone_bottom = min(h, ocr_zone_top+int(0.25*h))
    cropped_bottom = img.crop((0, ocr_zone_top, w, ocr_zone_bottom))
    text_bottom = pytesseract.image_to_string(cropped_bottom, lang='eng')
    # Cherche la ligne 'vues/views' et approxime sa position
    for idx, line in enumerate(text_bottom.splitlines()):
        if re.search(r'[0-9][0-9\., kKmM]*\s*(vues|views)', line, re.IGNORECASE):
            vues_views_y = ocr_zone_top + int((idx/len(text_bottom.splitlines()))*(ocr_zone_bottom-ocr_zone_top))
            break
    # 3. Crop dynamique entre barre_lecture_y et vues_views_y
    if barre_lecture_y and vues_views_y and vues_views_y > barre_lecture_y:
        crop_box = (0, barre_lecture_y, w, vues_views_y)
        cropped = img.crop(crop_box)
        text = pytesseract.image_to_string(cropped, lang='eng')
        # 4. Filtrage strict
        lines = []
        for l in text.splitlines():
            l_strip = l.strip()
            if not l_strip:
                continue
            if re.search(r'[0-9][0-9\., kKmM]*\s*(vues|views)', l_strip, re.IGNORECASE):
                break
            if l_strip.startswith('©') or re.match(r'^\d+$', l_strip) or '©' in l_strip:
                continue
            lines.append(l_strip)
            if len(lines) == 2:
                break
        return " ".join(lines) if lines else ""
    else:
        # fallback : crop fixe (x : 0-1, y : 0.37-0.45 pour iPhone, 0.90-0.94 pour iPad)
        if device == "iPhone":
            crop_box = (0, int(0.37 * h), w, int(0.45 * h))
        elif device == "iPad":
            crop_box = (0, int(0.90 * h), w, int(0.94 * h))
        else:
            crop_box = (0, int(0.37 * h), w, int(0.45 * h))
        cropped = img.crop(crop_box)
        text = pytesseract.image_to_string(cropped, lang='eng')
        lines = []
        for l in text.splitlines():
            l_strip = l.strip()
            if not l_strip:
                continue
            if l_strip.startswith('©') or re.match(r'^\d+$', l_strip) or '©' in l_strip:
                continue
            lines.append(l_strip)
            if len(lines) == 2:
                break
        return " ".join(lines) if lines else ""


def extract_key_text(img, device, orientation, content_type):
    """
    Dispatcher qui sélectionne la bonne fonction d'extraction selon le type de contenu et le device.
    """
    if content_type == "Shazam":
        return extract_shazam_text(img, device, orientation)
    elif content_type == "ShazamNotif":
        return extract_shazam_notif_text(img, device, orientation)
    elif content_type == "AppleMusic":
        return extract_apple_music_text(img, device, orientation)
    elif content_type == "YouTube":
        return extract_youtube_text(img, device, orientation)
    else:
        # fallback : OCR plein écran
        return pytesseract.image_to_string(img, lang='eng')


def extract_text(image_path, lang='eng'):
    """
    Extrait le texte d'une image via OCR (plein écran, fallback ou debug).
    Args:
        image_path (str): Chemin vers l'image à traiter.
        lang (str): Langue à utiliser pour l'OCR (par défaut 'eng').

    Returns:
        str: Texte extrait de l'image.
    """
    # Ouvre l'image à partir du chemin fourni
    img = Image.open(image_path)
    # Applique l'OCR avec pytesseract sur l'image
    text = pytesseract.image_to_string(img, lang=lang)
    # Retourne le texte extrait    return text


def ocr_all_in_folder(folder, lang='eng', crop_box=None):
    """
    Parcourt tous les fichiers image d'un dossier et extrait le texte OCR de chacun.
    Peut appliquer un crop sur chaque image avant OCR si crop_box est défini.

    Args:
        folder (str): Chemin du dossier à parcourir.
        lang (str): Langue pour l'OCR (par défaut 'eng').
        crop_box (tuple ou None): Zone de crop (left, upper, right, lower) ou None pour ne pas croper.

    Returns:
        list: Liste de dictionnaires {'file': nom_fichier, 'text': texte_extrait}.
    """
    results = []  # Liste pour stocker les résultats de chaque image
    # Parcourt tous les fichiers du dossier
    for filename in os.listdir(folder):
        # Vérifie si le fichier est une image supportée (png, jpg, jpeg, bmp)
        if filename.lower().endswith(('.png', '.jpg', '.jpeg', '.bmp')):
            img_path = os.path.join(folder, filename)  # Construit le chemin complet
            img = Image.open(img_path)  # Ouvre l'image
            if crop_box:
                # Si un crop est défini, on applique le crop à l'image
                img = img.crop(crop_box)
            # Applique l'OCR sur l'image (croppée ou non)
            text = pytesseract.image_to_string(img, lang=lang)
            # Ajoute le résultat à la liste
            results.append({'file': filename, 'text': text})
            # Affiche le texte extrait pour debug
            print(f"\n--- {filename} ---\n{text.strip()}\n")
    # Retourne la liste des résultats
    return results


if __name__ == "__main__":
    # Point d'entrée du script si exécuté directement
    import sys  # Import du module sys pour récupérer les arguments de la ligne de commande
    # Récupère le dossier à traiter depuis les arguments, ou './screens' par défaut
    folder = sys.argv[1] if len(sys.argv) > 1 else "./screens"
    # Par défaut, pas de crop (mais tu peux ajouter selon le device ou le contexte)
    # Exemple d'utilisation : crop_box = (left, top, right, bottom)
    crop_box = None
    # Lance l'OCR sur tout le dossier avec les paramètres choisis
    ocr_all_in_folder(folder, lang='eng', crop_box=crop_box)
