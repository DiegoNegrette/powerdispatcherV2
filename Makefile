PG_USER=$(USERNAME)
PG_DB=$(DATABASE)
BASE=docker-compose -f docker-compose.yml
KUBE=kubectl
K8S_NAMESPACE=
PROJECT_NAME=ragatex

build:
	call .\set_env.bat && $(BASE) build --build-arg ENVIRONMENT_FLAVOR=dev $(c)

start:
	call .\set_env.bat && $(BASE) up $(c)

start-dontuse:
	call .\set_env.bat && $(BASE) up $(c) --scale chrome=%NUMBER_OF_WEBDRIVER_NODES%

down:
	call .\set_env.bat && $(BASE) down $(c)

db_connect:
	call .\set_dev_env.bat && $(BASE) exec django bash -c "cd $(PROJECT_NAME) && python manage.py dbshell"

shell_django:
	call .\set_env.bat && $(BASE) exec django bash -c "cd $(PROJECT_NAME) && python manage.py shell"

ssh:
	call .\set_env.bat && $(BASE) exec $(c) bash || $(BASE) exec $(c) sh || $(BASE) run $(c) bash
