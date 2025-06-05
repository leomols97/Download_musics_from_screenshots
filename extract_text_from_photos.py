"""
Module extract_text_from_photos.py
Ce module gère l'extraction de texte OCR à partir de photos ou de screenshots Apple.
Il utilise pytesseract pour l'OCR, PIL pour la gestion d'image, et permet d'appliquer un crop adapté selon le device ou le contexte.
"""

# Import du module os pour la gestion des chemins, dossiers et fichiers
import os
# Import de pytesseract pour effectuer l'OCR sur les images
import pytesseract
# Import de PIL (Pillow) pour ouvrir et manipuler les images
from PIL import Image


def extract_text(image_path, lang='eng'):
    """
    Extrait le texte d'une image via OCR.

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
    # Retourne le texte extrait
    return text


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
