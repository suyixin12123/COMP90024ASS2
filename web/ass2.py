from flask import Flask, render_template, url_for, jsonify, abort, request, make_response
import couchdb
import requests
import json
import matplotlib.pyplot as plt
from flask_httpauth import HTTPBasicAuth
app = Flask(__name__)
auth = HTTPBasicAuth()
user = 'admin'
passwd = 'admin'

def getDataFromCouchDB(data):
    # this function will convert a list of dictionaries obtained from couchDB into a dictionary
    # which contains all required information for analysis
    dic = {}

    # iterate all documents
    for i in data:
        try:
            if i['city'] == 'brisbane':
                continue
            temp={}
            temp["total_twitter"] = i['food_100']['total_twitter']
            dic[i['city']] = temp
        except:
            continue
    return dic

try:
    couch = couchdb.Server('http://%s:%s@45.113.235.228:5984/'%(user,passwd))
except:
    print("Cannot find CouchDB Server ... Exiting")
    print("----_Stack Trace_-----")
    raise
    
# couchdb username and password
couch.resource.credentials = ('admin', 'admin')

# locate to certain database
db = couch['data_analysis']

# all docs including views
rows = db.view('_all_docs', include_docs=True)

# transfer couchdb object to a list, each list contains a dictionary
raw_data = [row['doc'] for row in rows]

# collect all required data into one dictionary
data = getDataFromCouchDB(raw_data)

# so can access home page though two paths
@app.route("/")
@app.route("/login")
def login():
    return render_template('login.html')

@app.route("/home")
def home():
    return render_template('home.html')

@app.route("/twitter")
def twitter():
    return render_template('twitter.html', data = json.dumps(data))

@app.route("/about")
def about():
    return render_template('about.html', title = "About")

# --------------------- Restful API ------------------------
@auth.get_password
def get_password(username):
    if username == 'admin':
        return 'admin'
    return None

@auth.error_handler
def unauthorized():
    return make_response(jsonify({'error': 'Unauthorized access'}), 403)
    # return 403 instead of 401 to prevent browsers from displaying the default auth dialog

@app.errorhandler(400)
def bad_request(error):
    return make_response(jsonify({'error': 'Bad request'}), 400)

@app.errorhandler(404)
def not_found(error):
    return make_response(jsonify({'error': 'Not found'}), 404)

def make_tasks(data):
    # turn a dictionary into a list of dictionaries so that is can be shown as a json object
    # and can be obtained by 'curl' command
    new_tasks = []
    for key in data:
        task = {}
        task['city'] = key
        task['url'] = "http://127.0.0.1:5984/twitter/api/tasks/" + key
        task['total_twitter'] = data[key]['total_twitter']
        new_tasks.append(task)
    return new_tasks

tasks = make_tasks(data)

# get all twitters
@app.route('/twitter/api/tasks', methods=['GET'])
@auth.login_required
def get_tasks():
    return jsonify({'tasks': tasks})


@app.route('/twitter/api/tasks/<string:task_id>', methods=['GET'])
@auth.login_required
def get_task(task_id):
    task = -1
    for i in range(len(tasks)):
        if task_id == tasks[i]['city']:
            task = i
            break
    if task == -1:
        abort(404)
    return jsonify({'task': tasks[task]})


@app.route('/twitter/api/tasks', methods=['POST'])
@auth.login_required
def create_task():
    if not request.json or not 'city' in request.json:
        abort(400)
    task = {
        'city': request.json['city'],
        'url': "http://127.0.0.1:5984/twitter/api/tasks/" + request.json['city'],
        'total_twitter': request.json.get('total_twitter', ""),
    }
    tasks.append(task)
    # db.save(task)
    return jsonify({'task': tasks}), 201


@app.route('/twitter/api/tasks/<string:task_id>', methods=['PUT'])
@auth.login_required
def update_task(task_id):
    task = -1
    for i in range(len(tasks)):
        if task_id == tasks[i]['city']:
            task = i
            break
    if task == -1:
        abort(404)
    if not request.json:
        abort(400)
    if 'city' in request.json and type(request.json['city']) != str:
        abort(400)
    if 'total_twitter' in request.json and type(request.json['total_twitter']) != int:
        abort(400)
    tasks[task]['city'] = request.json.get('city', tasks[task]['city'])
    tasks[task]['total_twitter'] = request.json.get(
        'total_twitter', tasks[task]['total_twitter'])
    return jsonify({'task': tasks[task]})


@app.route('/twitter/api/tasks/<string:task_id>', methods=['DELETE'])
@auth.login_required
def delete_task(task_id):
    task = -1
    for i in range(len(tasks)):
        if task_id == tasks[i]['city']:
            task = i
            break
    if task == -1:
        abort(404)
    tasks.remove(tasks[task])
    # db.delete(tasks[task])
    return jsonify({'result': True})

#  ------------------- API for grabing aurin data ------------------
def make_analysis_tasks(data):
    # turn a dictionary into a list of dictionaries so that is can be shown as a json object
    # and can be obtained by 'curl' command
    for doc in data:
        doc.pop('_rev')
        doc['_id'] = doc['_id'].replace(' ', '_')
        doc['url'] = "http://127.0.0.1:5984/twitter/api/aurin_tasks/" + doc['_id']
    return data

# locate to certain database
db_aurin = couch['aurin']

# all docs including views
rows_aurin = db_aurin.view('_all_docs', include_docs=True)

# transfer couchdb object to a list, each list contains a dictionary
raw_data_aurin = [row['doc'] for row in rows_aurin]
tasks_aurin = make_analysis_tasks(raw_data_aurin)

# get all aurin data
@app.route('/twitter/api/aurin_tasks', methods=['GET'])
@auth.login_required
def get_aurin_tasks():
    return jsonify({'tasks': tasks_aurin})

@app.route('/twitter/api/aurin_tasks/<string:task_id>', methods=['GET'])
@auth.login_required
def get_aurin_task(task_id):
    task = -1
    for i in range(len(tasks_aurin)):
        if task_id == tasks_aurin[i]['_id']:
            task = i
            break
    if task == -1:
        abort(404)
    return jsonify({'task': tasks_aurin[task]})


@app.route('/twitter/api/aurin_tasks', methods=['POST'])
@auth.login_required
def create_aurin_task():
    if not request.json or not '_id' in request.json:
        abort(400)
    task = {
        '_id': request.json['_id'].replace(' ', '_'),
        'url': "http://127.0.0.1:5984/twitter/api/aurin_tasks/" + request.json['_id'].replace(' ', '_'),
        'Sydney': request.json.get('Sydney', ""),
        'Melbourne': request.json.get('Melbourne', ""),
        'Brisbane': request.json.get('Brisbane', ""),
        'Adelaide': request.json.get('Adelaide', ""),
    }
    tasks_aurin.append(task)
    # db.save(task)
    return jsonify({'task': tasks_aurin}), 201


@app.route('/twitter/api/aurin_tasks/<string:task_id>', methods=['PUT'])
@auth.login_required
def update_aurin_task(task_id):
    task = -1
    for i in range(len(tasks_aurin)):
        if task_id == tasks_aurin[i]['_id']:
            task = i
            break
    if task == -1:
        abort(404)
    if not request.json:
        abort(400)
    if '_id' in request.json and type(request.json['_id']) != str:
        abort(400)
    if 'Sydney' in request.json and type(request.json['Sydney']) != float:
        abort(400)
    if 'Melbourne' in request.json and type(request.json['Melbourne']) != float:
        abort(400)
    if 'Brisbane' in request.json and type(request.json['Brisbane']) != float:
        abort(400)
    if 'Adelaide' in request.json and type(request.json['Adelaide']) != float:
        abort(400)                
    tasks_aurin[task]['_id'] = request.json.get('_id', tasks_aurin[task]['_id']).replace(' ', '_')
    tasks_aurin[task]['Sydney'] = request.json.get('Sydney', tasks_aurin[task]['Sydney'])
    tasks_aurin[task]['Melbourne'] = request.json.get('Melbourne', tasks_aurin[task]['Melbourne'])   
    tasks_aurin[task]['Brisbane'] = request.json.get('Brisbane', tasks_aurin[task]['Brisbane'])
    tasks_aurin[task]['Adelaide'] = request.json.get('Adelaide', tasks_aurin[task]['Adelaide'])                    
    return jsonify({'task': tasks_aurin[task]})


@app.route('/twitter/api/aurin_tasks/<string:task_id>', methods=['DELETE'])
@auth.login_required
def delete_aurin_task(task_id):
    task = -1
    for i in range(len(tasks_aurin)):
        if task_id == tasks_aurin[i]['_id']:
            task = i
            break
    if task == -1:
        abort(404)
    tasks_aurin.remove(tasks_aurin[task])
    # db.delete(tasks[task])
    return jsonify({'result': True})

#  ------------------- API for grabing correlation results------------------
# locate to certain database
db_analysis = couch['analysis_result']

# all docs including views
rows_analysis = db_analysis.view('_all_docs', include_docs=True)

# transfer couchdb object to a list, each list contains a dictionary
raw_data_analysis = [row['doc'] for row in rows_analysis]
tasks_analysis = make_analysis_tasks(raw_data_analysis)

# get all aurin data
@app.route('/twitter/api/analysis_tasks', methods=['GET'])
@auth.login_required
def get_analysis_tasks():
    return jsonify({'tasks': tasks_analysis})

@app.route('/twitter/api/analysis_tasks/<string:task_id>', methods=['GET'])
@auth.login_required
def get_analysis_task(task_id):
    task = -1
    for i in range(len(tasks_analysis)):
        if task_id == tasks_analysis[i]['_id']:
            task = i
            break
    if task == -1:
        abort(404)
    return jsonify({'task': tasks_analysis[task]})


@app.route('/twitter/api/analysis_tasks', methods=['POST'])
@auth.login_required
def create_analysis_task():
    if not request.json or not '_id' in request.json:
        abort(400)
    task = {
        '_id': request.json['_id'].replace(' ', '_'),
        'url': "http://127.0.0.1:5984/twitter/api/analysis_tasks/" + request.json['_id'].replace(' ', '_'),
        'chronic disease risk': request.json.get('chronic disease risk', ""),
        'high blood pressure risk': request.json.get('high blood pressure risk', ""),
        'low exerise': request.json.get('low exerise', ""),
        'mental depression': request.json.get('mental depression', ""),
        'obesity': request.json.get('obesity', ""),
        'overweight': request.json.get('overweight', ""),
    }
    tasks_analysis.append(task)
    # db.save(task)
    return jsonify({'task': tasks_analysis}), 201


@app.route('/twitter/api/analysis_tasks/<string:task_id>', methods=['PUT'])
@auth.login_required
def update_analysis_task(task_id):
    task = -1
    for i in range(len(tasks_analysis)):
        if task_id == tasks_analysis[i]['_id']:
            task = i
            break
    if task == -1:
        abort(404)
    if not request.json:
        abort(400)
    if '_id' in request.json and type(request.json['_id']) != str:
        abort(400)
    if 'chronic disease risk' in request.json and type(request.json['chronic disease risk']) != float:
        abort(400)
    if 'high blood pressure risk' in request.json and type(request.json['high blood pressure risk']) != float:
        abort(400)
    if 'low exerise' in request.json and type(request.json['low exerise']) != float:
        abort(400)
    if 'mental depression' in request.json and type(request.json['mental depression']) != float:
        abort(400)  
    if 'obesity' in request.json and type(request.json['obesity']) != float:
        abort(400)  
    if 'overweight' in request.json and type(request.json['overweight']) != float:
        abort(400)                                
    tasks_analysis[task]['_id'] = request.json.get('_id', tasks_analysis[task]['_id']).replace(' ', '_')
    tasks_analysis[task]['chronic disease risk'] = request.json.get('chronic disease risk', tasks_analysis[task]['chronic disease risk'])
    tasks_analysis[task]['high blood pressure risk'] = request.json.get('high blood pressure risk', tasks_analysis[task]['high blood pressure risk'])   
    tasks_analysis[task]['low exerise'] = request.json.get('low exerise', tasks_analysis[task]['low exerise'])
    tasks_analysis[task]['mental depression'] = request.json.get('mental depression', tasks_analysis[task]['mental depression'])  
    tasks_analysis[task]['obesity'] = request.json.get('obesity', tasks_analysis[task]['obesity'])    
    tasks_analysis[task]['overweight'] = request.json.get('overweight', tasks_analysis[task]['overweight'])                              
    return jsonify({'task': tasks_analysis[task]})


@app.route('/twitter/api/analysis_tasks/<string:task_id>', methods=['DELETE'])
@auth.login_required
def delete_analysis_task(task_id):
    task = -1
    for i in range(len(tasks_analysis)):
        if task_id == tasks_analysis[i]['_id']:
            task = i
            break
    if task == -1:
        abort(404)
    tasks_analysis.remove(tasks_analysis[task])
    # db.delete(tasks[task])
    return jsonify({'result': True})

if __name__ == '__main__':
	app.run(debug=True)
