import imghdr
from flask import Flask, request, jsonify, render_template, send_from_directory, make_response
from werkzeug.datastructures import FileStorage
from celery_tasks import remove_bg, celery_app
from celery.result import AsyncResult
import io

app = Flask(__name__)
def valid_file(file):
    return imghdr.what(file) in {'jpeg', 'png'}

@app.route('/', methods=['POST', 'GET'])
def index():
    return "hello"

@app.route('/remove', methods=['POST', 'GET'])
def remove_background():
    if request.method=='GET':
        task_id = request.cookies.get('task_id')
        if task_id:
            result = AsyncResult(task_id, app=celery_app)
            if result.successful():
                return render_template('upload.html', url=f'http://localhost:8000/removed/{task_id}.png')
            return render_template('upload.html', status = result.state)
        return render_template('upload.html')
    
    file: FileStorage = request.files.get('image')
    if not file:
        return jsonify({'success': False, 'status_code': 400, 'msg': 'image field is required but not given.'}), 400
    if not valid_file(file):
        return jsonify({'success': False, 'status_code': 400, 'msg': 'file is not a valid jpeg or png image.'}), 400
    
    task: AsyncResult = remove_bg.delay(file.stream.read())
    response = make_response(render_template('upload.html', task_id=task.id))
    response.set_cookie('task_id', task.id)
    return response
    # return jsonify({'success': True, 'status_code': 202, 'msg': 'Image is processing...', 'data': {'task_id':task.id, 'url':f'http://localhost:8000/result/{task.id}'}}), 202

@app.route('/result/<id>')
def get_status(id):
    result = AsyncResult(id, app=celery_app)
    
    if result.state=='PENDING':
        status_code = 202
    elif result.state=='FAILURE':
        status_code = 500
    elif result.state=='STARTED':
        status_code = 202
    elif result.state=='SUCCESS':
        status_code = 200
    
    return jsonify({'status': result.state, 'success': False if not result.successful() else result.result, 'file': None if not result.successful() else f'http://localhost:8000/removed/{result.id}.png'}), status_code

@app.route('/removed/<filename>')
def download_file(filename):
    return send_from_directory('removed', filename)
