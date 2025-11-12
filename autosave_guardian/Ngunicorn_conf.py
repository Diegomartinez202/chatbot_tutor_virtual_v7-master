# autosave_guardian/gunicorn_conf.py
workers = 2
worker_class = "gthread"
threads = 8
bind = "0.0.0.0:8080"
timeout = 30
accesslog = "-"
