from flask import Flask, render_template, request, jsonify, redirect, url_for
from pymongo import MongoClient  # pymongo를 임포트 하기
import datetime
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


# 게시물 등록하기
@app.route('/addboard')
def addboard():
    token_receive = request.cookies.get('mytoken')
    try:
        payload = jwt.decode(token_receive, SECRET_KEY, algorithms=['HS256'])
        return render_template('addboard.html')
    except jwt.ExpiredSignatureError:
        return redirect(url_for("login", redirectUrl="myboardlist"))
    except jwt.exceptions.DecodeError:
        # 로그인 후 원래 페이지로 돌아가기 위해 redirectUrl을 뿌려줌
        # 아래처럼 리다이렉트하면 브라우저 url이 /login?redirectUrl=addboard처럼 변경되고 login()
        # 함수가 호출되어 render_template('login.html') 로 login.html 화면이 나타난다.
        # 로그인 페이지를 렌더하는 login()함수에서 redirectUrl 쿼리 파라미터를 받아 사용하지 않고
        # 클라이언트에서 브라우저의 url을 파싱해서 로그인 요청이 완료되면 해당 페이지로 이동시킴!
        return redirect(url_for("login", redirectUrl="addboard"))


# 로그인
@app.route('/login')
def login():
    return render_template('login.html')


# 게시물 전체보기
# jinja2 템플릿을 이용하기 위해 게시물의 제목, 사진, 작성자등을
# render_templates의 인자로 넘겨준다
@app.route('/boardlist')
def boardlist():
    token_receive = request.cookies.get('mytoken')
    # board의 데이터를 가공 후 boardlist 페이지로 넘겨줍니다!
    boards_ = list(db.board.find())
    print(boards_, 1)
    boards = []

    for board in boards_:
        boards.append({
            'board_id': board['board_id'],
            'title': board['title'],
            'user_id': board['user_id'],
            'nick': board['nick'],
            'file': '../static/boardImage/' + board['file'],
            'date': board['file'][5:15],
            'good': len(board['good'])
        })
    # print해서 확인해봐용!
    print(boards)

    try:
        payload = jwt.decode(token_receive, SECRET_KEY, algorithms=['HS256'])
        return render_template('boardlist.html', isOn="on", boards=boards)
    except jwt.ExpiredSignatureError:
        return render_template('boardlist.html', isOn="off", boards=boards)
    except jwt.exceptions.DecodeError:
        return render_template('boardlist.html', isOn="off", boards=boards)


# 내자랑 전체보기
@app.route('/myboardlist')
def myboardlist():
    token_receive = request.cookies.get('mytoken')
    try:
        payload = jwt.decode(token_receive, SECRET_KEY, algorithms=['HS256'])
        # token에서 회원 아이디를 빼서 게시글 조회
        boards_ = list(db.board.find({'user_id': payload['id']}))
        boards = []
        for board in boards_:
            boards.append({
                'board_id': board['board_id'],
                'title': board['title'],
                'user_id': board['user_id'],
                'nick': board['nick'],
                'file': '../static/boardImage/' + board['file'],
                'date': board['file'][5:15],
                'good': len(board['good'])
            })
        print(boards)
        return render_template('myboardlist.html', isOn="on", boards=boards)
    except jwt.ExpiredSignatureError:
        return redirect(url_for("login", redirectUrl="myboardlist"))
    except jwt.exceptions.DecodeError:
        return redirect(url_for("login", redirectUrl="myboardlist"))


# 내 자랑 하나보기
# @app.route('/myboard', methods=['GET'])
# def myboard():


# 게시글 올리기 API
@app.route('/api/addboard', methods=['POST'])
def posting():
    title_receive = request.form["title_give"]
    comment_receive = request.form["comment_give"]
    file = request.files["file_give"]
    # static 폴더에 저장될 파일 이름 생성하기
    today = datetime.datetime.now()
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
        id = payload['id']
        nick = payload['nick']
    except jwt.ExpiredSignatureError:
        return redirect(url_for("", msg="로그인 시간이 만료되었습니다."))
    except jwt.exceptions.DecodeError:
        return redirect(url_for("", msg="로그인 시간이 만료되었습니다."))

    # DB에 저장
    doc = {
        'board_id': filename,
        'title': title_receive,
        'user_id': id,
        'comment': comment_receive,
        'file': f'{filename}.{extension}',
        'nick': nick,
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
            'nick': result['nick'],
            'exp': datetime.datetime.utcnow() + datetime.timedelta(minutes=300)
        }
        token = jwt.encode(payload, SECRET_KEY, algorithm='HS256')

        ## token과 redirectURL을 -> 클라이언트에서 로그인 후 이 정보로 리다이이렉트
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
