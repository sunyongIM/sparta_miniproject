from flask import Flask, render_template, request, jsonify, redirect, url_for
from pymongo import MongoClient  # pymongo를 임포트 하기
from datetime import datetime
import hashlib
import jwt

SECRET_KEY = 'Eban5joDangStar'

client = MongoClient(
    'mongodb+srv://duck:1234@cluster0.8lepp.mongodb.net/Cluster0?retryWrites=true&w=majority')  # Atlas에서 가져올 접속 정보
db = client.dogstagram

app = Flask(__name__)


# 메인화면
@app.route('/')
def home():
    token_receive = request.cookies.get('mytoken')
    try:
        payload = jwt.decode(token_receive, SECRET_KEY, algorithms=['HS256'])
        return render_template('index.html', isOn="on")
    except jwt.ExpiredSignatureError:
        return render_template('index.html', isOn="off")
    except jwt.exceptions.DecodeError:
        return render_template('index.html', isOn="off")


# 자랑하기
@app.route('/addboard')
def addboard():
    token_receive = request.cookies.get('mytoken')
    try:
        payload = jwt.decode(token_receive, SECRET_KEY, algorithms=['HS256'])
        return render_template('addboard.html')
    except jwt.ExpiredSignatureError:
        return redirect(url_for("login", msg="로그인 시간이 만료되었습니다."))
    except jwt.exceptions.DecodeError:
        return redirect(url_for("login", redirectUrl="addboard"))


# 로그인
@app.route('/login')
def login():
    return render_template('login.html')


# 게시글 올리기 API
@app.route('/api/addboard', methods=['POST'])
def posting():
    title_receive = request.form["title_give"]
    comment_receive = request.form["comment_give"]
    file = request.files["file_give"]
    # static 폴더에 저장될 파일 이름 생성하기
    today = datetime.now()
    mytime = today.strftime('%Y-%m-%d-%H-%M-%S')
    filename = f'file-{mytime}'
    # 확장자 나누기
    extension = file.filename.split('.')[-1]
    # static 폴더에 저장
    save_to = f'static/boardImage/{filename}.{extension}'
    file.save(save_to)

    token_receive = request.cookies.get('mytoken')
    try:
        payload = jwt.decode(token_receive, SECRET_KEY, algorithms=['HS256'])
        userID = payload['id']
    except jwt.ExpiredSignatureError:
        return redirect(url_for("", msg="로그인 시간이 만료되었습니다."))
    except jwt.exceptions.DecodeError:
        return redirect(url_for("", msg="로그인 시간이 만료되었습니다."))

    # DB에 저장
    doc = {
        'title': title_receive,
        'userID': userID,
        'comment': comment_receive,
        'file': f'{filename}.{extension}',
        'good': []
    }
    db.board.insert_one(doc)

    return jsonify({'msg': '업로드 완료!'})


###### 로그인과 회원가입을 위한 API #####

## 아이디 중복확인
@app.route('/sign_up/check_dup', methods=['POST'])
def check_dup():
    userid_receive = request.form['userid_give']
    exists = bool(db.user.find_one({"id": userid_receive}))
    ## 변수명이 잘못되어 테스트함
    # print(f'유저아이디 : {userid_receive}, bool: {exists}')
    return jsonify({'result': 'success', 'exists': exists})


## 회원가입 API
@app.route('/api/register', methods=['POST'])
def api_register():
    id_receive = request.form['id_give']
    pw_receive = request.form['pw_give']
    nickname_receive = request.form['nickname_give']
    ## 해쉬를 이용해 pw를 sha256 방법(=단방향 암호화. 풀어볼 수 없음)으로 암호화해서 저장합니다.
    pw_hash = hashlib.sha256(pw_receive.encode('utf-8')).hexdigest()

    db.user.insert_one({'id': id_receive, 'pw': pw_hash, 'nick': nickname_receive})

    return jsonify({'result': 'success'})


## 로그인 API
@app.route('/api/login', methods=['POST'])
def api_login():
    id_receive = request.form['id_give']
    pw_receive = request.form['pw_give']

    pw_hash = hashlib.sha256(pw_receive.encode('utf-8')).hexdigest()

    result = db.user.find_one({'id': id_receive, 'pw': pw_hash})

    ## 찾으면 JWT 토큰을 만들어 발급합니다.
    if result is not None:
        payload = {
            'id': id_receive,
            'exp': datetime.datetime.utcnow() + datetime.timedelta(minutes=300)
        }
        token = jwt.encode(payload, SECRET_KEY, algorithm='HS256')

        ## token을 줍니다.
        return jsonify({'result': 'success', 'token': token})
    ## 찾지 못하면
    else:
        return jsonify({'result': 'fail', 'msg': '아이디/비밀번호가 일치하지 않습니다.'})


# 보안: 로그인한 사용자만 통과할 수 있는 API
@app.route('/api/isAuth', methods=['GET'])
def api_valid():
    token_receive = request.cookies.get('mytoken')
    try:
        # token을 시크릿키로 디코딩합니다.
        payload = jwt.decode(token_receive, SECRET_KEY, algorithms=['HS256'])
        # payload 안에 id가 들어있습니다. 이 id로 유저정보를 찾습니다.
        userinfo = db.user.find_one({'id': payload['id']}, {'_id': 0})
        return jsonify({'result': 'success', 'nickname': userinfo['nick']})
    except jwt.ExpiredSignatureError:
        # 위를 실행했는데 만료시간이 지났으면 에러가 납니다.
        return jsonify({'result': 'fail', 'msg': '로그인 시간이 만료되었습니다.'})
    except jwt.exceptions.DecodeError:
        # 로그인 정보가 없으면 에러가 납니다!
        return jsonify({'result': 'fail', 'msg': '로그인 정보가 존재하지 않습니다.'})


if __name__ == '__main__':
    app.run('0.0.0.0', port=5000, debug=True)
