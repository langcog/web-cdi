SHELL := /bin/bash
PROJECT = webcdi

githooks:
	git config core.hooksPath .githooks

docker-dev:
	docker-compose up

docker-db-populate:
	docker-compose exec -it web ./manage.py migrate
	docker-compose exec -it web ./manage.py collectstatic --noinput
	docker-compose exec -it web ./manage.py 01_populate_instrument_family
	docker-compose exec -it web ./manage.py 02_populate_instrument
	docker-compose exec -it web ./manage.py 03_populate_scoring
	docker-compose exec -it web ./manage.py 04a_delete_benchmark;
	docker-compose exec -it web ./manage.py 04_populate_benchmark
	docker-compose exec -it web ./manage.py 05_populate_choices
	docker-compose exec -it web ./manage.py 06_populate_items
	
docker-test:
	docker-compose exec web coverage run manage.py test --exclude=selenium

docker-score:
	docker-compose exec web ./manage.py crontab_scoring

docker-create-db:
	docker-compose exec -it db bash 
	psql -U postgres
	CREATE DATABASE <DATABASENAME>;
	CREATE USER "<USERNAME>" WITH PASSWORD '<PASSWORD>';
	ALTER USER "<USERNAME>" WITH SUPERUSER;
	ALTER DATABASE <DATABASENAME> OWNER TO "<USERNAME>";

docker-lint:
	docker-compose exec web flake8 .
	docker-compose exec web black --check .

docker-cleanup:
	docker-compose exec web black .
	docker-compose exec web isort .

populate-docker-db:
	docker-compose exec -T db mysql -uwhite_eagle_lodge -pwhite_eagle_lodge white_eagle_lodge < live-database.sql
	
make sync-dev-db::
	ssh giant-dev mysql:export develop-${PROJECT} > mydump.sql
	cat mydump.sql | docker-compose exec -T db mysql -pgiant ${PROJECT}
	rm mydump.sql

make sync-media::
	rsync -rvz live:/var/lib/dokku/data/storage/live-${PROJECT}/media ./media/

make dev-deploy::
	eb deploy webcdi-dev-django4

make live-deploy::
	eb deploy webcdi-env
