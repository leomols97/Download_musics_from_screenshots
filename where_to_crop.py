from PIL import Image
import os

def get_crop_box(img, filename, device_type=None):
    w, h = img.size

    # Si device_type est un dict (nouveau format)
    if isinstance(device_type, dict):
        device = device_type.get("device", "").lower()
        orientation = device_type.get("orientation", "").lower()
        source = device_type.get("source", "").lower()

        # 1. Sélection par device
        if device == "iphone 16 pro max":
            # 2. Sélection par type/source
            if source == "photo":
                # 3. Zone à crop pour Shazam (titre/artiste, éviter zone du bas)
                top = int(0.11 * h)
                bottom = int(0.23 * h)
                left = int(0.08 * w)
                right = int(0.92 * w)
                return (left, top, right, bottom)
            elif source == "shazamnotification":
                # 3. Zone à crop pour notification Shazam (Dynamic Island)
                top = int(0.04 * h)
                bottom = int(0.12 * h)
                left = int(0.20 * w)
                right = int(0.80 * w)
                return (left, top, right, bottom)
            elif source == "youtube":
                # 3. Zone à crop pour YouTube (au-dessus des vues)
                top = int(0.21 * h)
                bottom = int(0.27 * h)
                left = int(0.08 * w)
                right = int(0.92 * w)
                return (left, top, right, bottom)
            # Fallback iPhone 16 Pro Max portrait
            if orientation == "portrait":
                top = int(0.295 * h)
                bottom = int(0.34 * h)
                left = int(0.04 * w)
                right = int(0.96 * w)
                return (left, top, right, bottom)
        elif device.startswith("iphone"):
            # 2. Sélection par type/source pour autres iPhone
            if source == "youtube":
                top = int(0.25 * h)
                bottom = int(0.31 * h)
                left = int(0.08 * w)
                right = int(0.92 * w)
                return (left, top, right, bottom)
            elif source in ["shazam", "photo"]:
                top = int(0.13 * h)
                bottom = int(0.23 * h)
                left = int(0.08 * w)
                right = int(0.92 * w)
                return (left, top, right, bottom)
            elif source == "shazamnotification":
                top = int(0.04 * h)
                bottom = int(0.12 * h)
                left = int(0.20 * w)
                right = int(0.80 * w)
                return (left, top, right, bottom)
            # Fallback générique iPhone portrait
            if orientation == "portrait":
                top = int(0.295 * h)
                bottom = int(0.34 * h)
                left = int(0.04 * w)
                right = int(0.96 * w)
                return (left, top, right, bottom)
        elif device.startswith("ipad"):
            # 2. Sélection par type/source pour iPad
            if source == "youtube":
                if orientation == "landscape":
                    # iPad Pro 12.9 landscape, zone au-dessus des vues
                    top = int(0.15 * h)
                    bottom = int(0.21 * h)
                    left = int(0.13 * w)
                    right = int(0.87 * w)
                    return (left, top, right, bottom)
                else:
                    # iPad portrait YouTube (si jamais)
                    top = int(0.18 * h)
                    bottom = int(0.28 * h)
                    left = int(0.05 * w)
                    right = int(0.95 * w)
                    return (left, top, right, bottom)
            elif source in ["shazam", "photo"]:
                top = int(0.10 * h)
                bottom = int(0.20 * h)
                left = int(0.10 * w)
                right = int(0.90 * w)
                return (left, top, right, bottom)
            elif source == "shazamnotification":
                top = int(0.04 * h)
                bottom = int(0.12 * h)
                left = int(0.20 * w)
                right = int(0.80 * w)
                return (left, top, right, bottom)
            # Fallback générique iPad portrait
            if orientation == "portrait":
                top = int(0.18 * h)
                bottom = int(0.28 * h)
                left = int(0.05 * w)
                right = int(0.95 * w)
                return (left, top, right, bottom)
        # Ajoute ici d'autres familles de devices si besoin
        # Fallback général
        return None

    # Ancien fallback pour compatibilité string
    if device_type and "screenshot" in device_type.lower() and w < h:
        top = int(0.295 * h)
        bottom = int(0.34 * h)
        left = int(0.04 * w)
        right = int(0.96 * w)
        return (left, top, right, bottom)
    if (device_type in ["Screenshot iPhone", "Screenshot mobile/tablette inconnu"] and w < h):
        return (int(0.05 * w), int(0.28 * h), int(0.95 * w), int(0.40 * h))
    if (device_type == "Screenshot iPad" and w < h):
        return (int(0.05 * w), int(0.18 * h), int(0.95 * w), int(0.28 * h))
    return None


def clean_ocr_lines(lines):
    # Liste à ajuster selon les apps !
    ignore_keywords = [
        "vues", "commentaire", "abonné", "s'abonner", "partager", "remixer",
        "clip", "télécharger", "sponsorisé", "apple music", "soundcloud",
        "like", "comment", "notifications", "publicité", "minutes", "heures",
        "stream", "plus", "...", "abonnés", "partage", "remix", "remixer",
        "titres de l’artiste", "voir plus", "ouvrir dans apple music", "s’abonner",
        "commentaires", "s’abonner", "nv", "clip", "commander", "téléchargement", "sponsorisé"
    ]
    cleaned = []
    for line in lines:
        l = line.lower()
        if not line.strip(): continue
        if any(k in l for k in ignore_keywords): continue
        # Ignore lignes très courtes
        if len(line.strip()) < 3: continue
        cleaned.append(line)
    # Ne garder que les 2 premières lignes non polluées (optionnel)
    cleaned = [l for l in cleaned if len(l) > 8][:2]
    return cleaned

def ocr_and_clean(img, lang='eng'):
    import pytesseract
    raw_text = pytesseract.image_to_string(img, lang=lang)
    lines = raw_text.split('\n')
    best = clean_ocr_lines(lines)
    # Retourne une seule ligne (titre + artiste), ou vide si rien trouvé
    return " – ".join(best) if best else ""

def crop_for_ocr(image_path, device_type=None):
    img = Image.open(image_path)
    crop_box = get_crop_box(img, os.path.basename(image_path), device_type=device_type)
    if crop_box:
        return img.crop(crop_box)
    return img

# EXEMPLE D’UTILISATION
if __name__ == "__main__":
    import sys
    if len(sys.argv) < 3:
        print("Usage: python where_to_crop.py FICHIER.png TYPE_DEVICE")
        print("Ex : python where_to_crop.py test.png 'Screenshot iPhone'")
        exit(1)
    imgpath = sys.argv[1]
    device_type = sys.argv[2]
    img = crop_for_ocr(imgpath, device_type)
    img.show()  # Affiche la zone croppée
    titre_artiste = ocr_and_clean(img)
    print(f"Résultat OCR filtré : {titre_artiste}")
