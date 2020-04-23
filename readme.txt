### 테스트서버 구동 명령어
python manage.py runserver

### Cerery 구동 명령어
celery -A [project_config_derectory_name] worker -l info

### Flower 구동 명령어
celery -A [project_config_derectory_name] flower --port=5555

### Rabbitmq 서버 구동 명령어
PATH=$PATH:/usr/local/sbin
rabbitmq-server

