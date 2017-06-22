import os
import random
import time
from flask import Flask, request, render_template, session, flash, redirect, url_for, jsonify

from celery import Celery

app = Flask(__name__)

# Celery configuration
app.config['CELERY_BROKER_URL'] = 'redis://localhost:6379/0'
app.config['CELERY_RESULT_BACKEND'] = 'redis://localhost:6379/0'


celery = Celery(app.name, broker=app.config['CELERY_BROKER_URL'])
celery.conf.update(app.config)


@app.route('/test', methods=['GET'])
def test():
    return "test"


@app.route('/', methods=['GET', 'POST'])
def index():
    return "home"


@celery.task(bind=True)
def my_nap(self):
    print("mydebug")
    time.sleep(10)
    self.update_state(state='PROGRESS',
                      meta={'current': 40, 'total': 100,
                            'status': "sleeping"})
    time.sleep(10)
    print("slept for 10 sec")
    return {'current': 100, 'total': 100, 'status': 'Task completed!',
            'result': 42}

@app.route('/longtask', methods=['GET'])
def longtask():
    task = my_nap.apply_async()
    return jsonify({"task_id": task.id})


@app.route('/status/<task_id>')
def taskstatus(task_id):
    task = my_nap.AsyncResult(task_id)
    if task.state == 'PENDING':
        response = {
            'state': task.state,
            'current': 0,
            'total': 1,
            'status': 'Pending...'
        }
    elif task.state != 'FAILURE':
        response = {
            'state': task.state,
            'current': task.info.get('current', 0),
            'total': task.info.get('total', 1),
            'status': task.info.get('status', '')
        }
        if 'result' in task.info:
            response['result'] = task.info['result']
    else:
        # something went wrong in the background job
        response = {
            'state': task.state,
            'current': 1,
            'total': 1,
            'status': str(task.info),  # this is the exception raised
        }
    return jsonify(response)


if __name__ == '__main__':
    app.run(debug=True)