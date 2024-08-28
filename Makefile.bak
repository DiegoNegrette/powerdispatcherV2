PG_USER=$${USERNAME}
PG_DB=$${DATABASE}
BASE=docker-compose -f docker-compose.yml
KUBE=kubectl
K8S_NAMESPACE=facebook
PROJECT_NAME=powerdispatcher

build:
	(. ./set_env.sh && ${BASE} build --build-arg ENVIRONMENT_FLAVOR=dev ${c})

start:
	(. ./set_env.sh && ${BASE} up ${c})

start-dontuse:
	(. ./set_env.sh && ${BASE} up ${c} --scale node-chrome=$$NUMBER_OF_WEBDRIVER_NODES --scale node-chrome-login=$$LOGIN_NUMBER_OF_WEBDRIVER_NODES)

down:
	(. ./set_env.sh && ${BASE} down ${c})

db_connect:
	# connect to the database.
	(. ./set_dev_env.sh && ${BASE} exec django bash -c 'cd ${PROJECT_NAME} && python manage.py dbshell')

shell_django:
	# i.e: `make shell_django`
	(. ./set_env.sh && ${BASE} exec django bash -c 'cd ${PROJECT_NAME} && python manage.py shell')

ssh:
	# c == container's name inside of the `docker-compose` file.
	# i.e: `make ssh c=django`
	(. ./set_env.sh && ${BASE} exec ${c} bash || ${BASE} exec ${c} sh || ${BASE} run ${c} bash)
