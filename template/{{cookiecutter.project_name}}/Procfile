web: gunicorn bk_plugin_runtime.wsgi --timeout 120 -k gthread --threads 16 -w 8 --max-requests=1000
schedule: celery worker -A blueapps.core.celery -P threads -n schedule_worker@%h -c 500 -Q plugin_schedule,plugin_callback,schedule_delete -l INFO
beat: celery beat -A blueapps.core.celery -l INFO
