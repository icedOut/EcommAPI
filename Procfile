release: flask init-db 
web: gunicorn inf5190:app --log-file=-
worker: flask worker inf5190.py