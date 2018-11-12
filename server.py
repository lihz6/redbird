from datetime import timedelta
from flask import request
from flask import session
from flask import Flask
from json import dumps
import worker

app = Flask(__name__)

app.secret_key = b'\xc9\xaa\xc8\n3Gr|\x1b\x11o\x04\xc7.\x04l'
app.permanent_session_lifetime = timedelta(days=365)


@app.before_request
def ensure_session():
    from ranstr import random
    if 'uuid' not in session:
        session['uuid'] = random()
        session['flag'] = '0'


@app.after_request
def add_headers(res):
    origin = request.headers.get('origin', '*')
    res.headers['Access-Control-Allow-Origin'] = origin
    res.headers['Access-Control-Allow-Credentials'] = 'true'
    res.headers['Access-Control-Allow-Headers'] = 'Content-Type'
    # res.headers['Content-Type'] = 'application/json'
    session.permanent = True
    return res


# 模糊搜索
@app.route('/app/v1/search/<lang>/<text>')
def search(lang, text):
    if len(text) > 32 or "'" in text:
        return '[]'
    uuid = session['uuid']
    if lang == 'en':
        return dumps(worker.search_en(text, uuid), ensure_ascii=False)
    elif lang == 'zh':
        return dumps(worker.search_zh(text, uuid), ensure_ascii=False)
    return '[]'


# 编辑释义
@app.route('/app/v1/define/<word>', methods=['POST'])
def define(word):
    if session['flag'] == '0':
        return '-2'
    uuid = session['uuid']
    data = request.get_json()
    if type(data) is not dict:
        return '-1'
    return worker.define(word, data, uuid)


@app.route('/app/v1/hintme/<username>')
def hintme(username):
    return dumps(worker.hintme(username), ensure_ascii=False)


@app.route('/app/v1/signin', methods=['POST'])
def signin():
    try:
        data = request.get_json()
        name = data['username']
        word = data['password']
        uuid = session['uuid']
        uuid = worker.signin(name, word, uuid)
        if uuid:
            session['uuid'] = uuid
            session['flag'] = '1'
            return '1'
        else:
            return '0'
    except:
        return '-1'


@app.route('/app/v1/signup', methods=['POST'])
def signup():
    try:
        data = request.get_json()
        name = data['username']
        word = data['password']
        hint = data['passhint']
        gender = data.get('gender', 1)
        birday = data.get('birday', 0)
        uuid = session['uuid']
        worker.signup(name, word, hint, uuid, gender, birday)
        session['flag'] = 1
        return '1'
    except:
        return '-1'


@app.route('/app/v1/logout')
def logout():
    from ranstr import random
    session['uuid'] = random()
    session['flag'] = '0'
    return '1'


@app.route('/app/see/you')
def see_you():
    from flask import render_template
    uuid = session['uuid']
    return render_template('see_you.html', name=uuid)


@app.route('/app/v1/mynote', methods=['POST'])
def mynote():
    if request.method != 'POST':
        return ''
    try:
        data = request.get_json()
        print(data)
        note = data['note']
        furl = data['furl']
        uuid = session['uuid']
        worker.mynote(uuid, note, furl)
        return '1'
    except:
        return '-1'


if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=False)
