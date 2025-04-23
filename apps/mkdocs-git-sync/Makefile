.PHONY: build run

build:
	docker build . -t buvis/mkdocs-git-sync
	docker-compose down --rmi=local
	docker volume rm mkdocs-git-sync_site

run:
	docker compose up
