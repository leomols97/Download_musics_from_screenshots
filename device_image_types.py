# device_image_types.py
"""
Ce module centralise toutes les constantes et fonctions nécessaires à la classification des screenshots d'appareils Apple (iPhone/iPad),
notamment pour la détection par résolution, l'orientation et le type de source (YouTube, Shazam, etc.).
Il sert de référence pour la pipeline de détection et de crop.
"""

# Tolérance globale utilisée lors de la comparaison des résolutions d'écran (pour accepter un léger crop ou coins arrondis)
DEVICE_RESOLUTION_TOLERANCE = 0.015  # Utilisée pour matcher les résolutions d'écran avec une marge d'erreur

IPHONE_MODELS = [
    "iPhone X",
    "iPhone XR",
    "iPhone XS",
    "iPhone XS Max",
    "iPhone 11",
    "iPhone 11 Pro",
    "iPhone 11 Pro Max",
    "iPhone SE (2020)",
    "iPhone 12",
    "iPhone 12 mini",
    "iPhone 12 Pro",
    "iPhone 12 Pro Max",
    "iPhone 13",
    "iPhone 13 mini",
    "iPhone 13 Pro",
    "iPhone 13 Pro Max",
    "iPhone SE (2022)",
    "iPhone 14",
    "iPhone 14 Plus",
    "iPhone 14 Pro",
    "iPhone 14 Pro Max",
    "iPhone 15",
    "iPhone 15 Plus",
    "iPhone 15 Pro",
    "iPhone 15 Pro Max",
    "iPhone 16",
    "iPhone 16 Plus",
    "iPhone 16 Pro",
    "iPhone 16 Pro Max"
]

# iPads Pro, Air et classiques sortis depuis l'iPad Pro 12,9 2018 (inclus)
IPAD_MODELS = [
    "iPad Pro 12.9 2018",   # 3e gen
    "iPad Pro 12.9 2020",   # 4e gen
    "iPad Pro 12.9 2021",   # 5e gen, mini-LED
    "iPad Pro 12.9 2022",   # 6e gen, mini-LED
    "iPad Pro 12.9 2024",   # 7e gen, OLED
]


# Résolutions officielles Apple (pixels, pas points) pour chaque modèle
DEVICE_RESOLUTIONS = {
    # iPhones (mise à jour jusqu'à l'iPhone 16)
    "iPhone X": (1125, 2436),  # 2017
    "iPhone XS": (1125, 2436),  # 2018
    "iPhone XS Max": (1242, 2688),  # 2018
    "iPhone XR": (828, 1792),  # 2018
    "iPhone 11": (828, 1792),  # 2019
    "iPhone 11 Pro": (1125, 2436),  # 2019
    "iPhone 11 Pro Max": (1242, 2688),  # 2019
    "iPhone 12 mini": (1080, 2340),  # 2020
    "iPhone 12": (1170, 2532),  # 2020
    "iPhone 12 Pro": (1170, 2532),  # 2020
    "iPhone 12 Pro Max": (1284, 2778),  # 2020
    "iPhone 13 mini": (1080, 2340),  # 2021
    "iPhone 13": (1170, 2532),  # 2021
    "iPhone 13 Pro": (1170, 2532),  # 2021
    "iPhone 13 Pro Max": (1284, 2778),  # 2021
    "iPhone 14": (1170, 2532),  # 2022
    "iPhone 14 Plus": (1284, 2778),  # 2022
    "iPhone 14 Pro": (1179, 2556),  # 2022
    "iPhone 14 Pro Max": (1290, 2796),  # 2022
    "iPhone 15": (1179, 2556),  # 2023
    "iPhone 15 Plus": (1290, 2796),  # 2023
    "iPhone 15 Pro": (1179, 2556),  # 2023
    "iPhone 15 Pro Max": (1290, 2796),  # 2023
    "iPhone 16": (1179, 2556),         # 6,1" OLED, 460 ppi
    "iPhone 16 Plus": (1290, 2796),    # 6,7" OLED, 460 ppi
    "iPhone 16 Pro": (1206, 2622),     # 6,3" OLED, 460 ppi
    "iPhone 16 Pro Max": (1320, 2868), # 6,9" OLED, 460 ppi
    # iPads Pro 12,9" (depuis 2018)
    "iPad Pro 12.9 2018": (2048, 2732),  # 3e gen
    "iPad Pro 12.9 2020": (2048, 2732),  # 4e gen
    "iPad Pro 12.9 2021": (2048, 2732),  # 5e gen, mini-LED
    "iPad Pro 12.9 2022": (2048, 2732),  # 6e gen, mini-LED
    "iPad Pro 12.9 2024": (2064, 2752),  # 7e gen, OLED
}


def is_model_resolution(width, height, model, tolerance=None):
    """
    Vérifie si (width, height) correspond à la résolution du modèle (avec tolérance pour coins arrondis).
    Retourne True si la résolution de l'image est suffisamment proche de celle du modèle (en tenant compte de l'orientation).
    """
    # Si la tolérance n'est pas fournie, on utilise la valeur globale
    if tolerance is None:
        # On applique la tolérance globale définie en haut du fichier
        tolerance = DEVICE_RESOLUTION_TOLERANCE
    # Récupère la résolution de référence du modèle (largeur, hauteur)
    ref_w, ref_h = DEVICE_RESOLUTIONS[model]
    # Teste les deux orientations
    def close(a, b):
        # Retourne True si la différence relative entre a et b est inférieure à la tolérance
        return abs(a - b) / max(a, b) < tolerance
    # Teste les deux orientations (portrait et paysage)
    # Premier cas : width ~ ref_w et height ~ ref_h
    # Second cas : width ~ ref_h et height ~ ref_w (rotation de 90°)
    return (close(width, ref_w) and close(height, ref_h)) or (close(width, ref_h) and close(height, ref_w))

# Liste des orientations supportées (sert à générer toutes les combinaisons possibles)
ORIENTATIONS = ["portrait", "landscape"]  # "portrait" = vertical, "landscape" = horizontal

# Liste des types de sources supportées (sert à générer toutes les combinaisons possibles)
SOURCES = ["YouTube", "Shazam", "ShazamNotification", "Photo"]  # Nom des apps ou contextes d'où provient le screenshot

# Liste exhaustive de toutes les combinaisons device/orientation/source
# Chaque entrée du tableau est un dictionnaire du type :
#   {"device": <modèle>, "orientation": <portrait|landscape>, "source": <YouTube|Shazam|...>}
# Cela permet de parcourir facilement tous les cas possibles dans la pipeline
DEVICE_IMAGE_TYPES = [
    {"device": model, "orientation": orientation, "source": source}  # Dictionnaire pour chaque combinaison
    for model in IPHONE_MODELS + IPAD_MODELS  # Pour chaque modèle supporté (iPhone et iPad)
    for orientation in ORIENTATIONS           # Pour chaque orientation possible
    for source in SOURCES                    # Pour chaque source possible
]

# Exemple d'utilisation :
# for entry in DEVICE_IMAGE_TYPES:
#     print(entry)
