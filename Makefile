APP_NAME=musicsearch
TAG=latest
CONTAINER_NAME=musicsearch_container

SCREENDIR=$(PWD)/screenshots

# 1. Build (juste l'image, jamais le code)
build:
	docker build -t $(APP_NAME):$(TAG) .

# À définir avant le run : export YT_API_KEY=ta_clef
run:
	docker run --rm -it \
		--name $(CONTAINER_NAME) \
		-v "$(PWD)":/app \
		-e YT_API_KEY=$$YT_API_KEY \
		$(APP_NAME):$(TAG) \
		python /app/main.py

ocr:
	docker run --rm -it \
		-v "$(PWD)":/app \
		$(APP_NAME):$(TAG) \
		python /app/extract_text_from_photos.py /app/screens

# Pour un accès shell/debug (optionnel)
shell:
	docker run --rm -it \
		-v "$(PWD)":/app \
		-e YT_API_KEY=$$YT_API_KEY \
		$(APP_NAME):$(TAG) /bin/bash


# 3. Nettoyage complet : containers, images, cache, volumes
clean:
	# Supprime les containers existants (s'ils traînent)
	-docker rm -f $(CONTAINER_NAME)
	# Supprime les images
	-docker rmi -f $(APP_NAME):$(TAG)
	# Supprime tout le cache build
	-docker builder prune -f
	# Supprime les volumes orphelins (optionnel, ajoute si besoin)
	-docker volume prune -f
