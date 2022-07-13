from pymongo import MongoClient

client = MongoClient('mongodb+srv://test:sparta@cluster0.0wupi.mongodb.net/Cluster0?retryWrites=true&w=majority')
db = client.eattogether

from flask import Flask, render_template, request, jsonify, redirect, url_for

app = Flask(__name__)

from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
import time

import jwt
import datetime
import hashlib
from werkzeug.utils import secure_filename
from datetime import datetime, timedelta

app.config["TEMPLATES_AUTO_RELOAD"] = True
app.config['UPLOAD_FOLDER'] = "./static/profile_pics"

SECRET_KEY = 'SPARTA'


@app.route('/')
def home():
    token_receive = request.cookies.get('mytoken')
    try:
        payload = jwt.decode(token_receive, SECRET_KEY, algorithms=['HS256'])
        return render_template('index.html')
    except jwt.ExpiredSignatureError:
        return redirect(url_for("login", msg="로그인 시간이 만료되었습니다."))
    except jwt.exceptions.DecodeError:
        return redirect(url_for("login", msg="로그인 정보가 존재하지 않습니다."))


@app.route('/login')
def login():
    msg = request.args.get("msg")
    return render_template('login.html', msg=msg)


@app.route('/sign_in', methods=['POST'])
def sign_in():
    # 로그인
    id_receive = request.form['id_give']
    pw_receive = request.form['pw_give']

    pw_hash = hashlib.sha256(pw_receive.encode('utf-8')).hexdigest()
    result = db.users.find_one({'id': id_receive, 'pw': pw_hash})

    if result is not None:
        payload = {
            'id': id_receive,
            # 'exp': datetime.utcnow() + timedelta(seconds=60 * 60 * 24)  # 로그인 24시간 유지
        }
        token = jwt.encode(payload, SECRET_KEY, algorithm='HS256')

        return jsonify({'result': 'success', 'token': token})
    # 찾지 못하면
    else:
        return jsonify({'result': 'fail', 'msg': '아이디/비밀번호가 일치하지 않습니다.'})

@app.route("/join", methods=["POST"])
def people_join():
    number_receive = request.form['number']
    token_receive = request.cookies.get('mytoken')
    payload = jwt.decode(token_receive, SECRET_KEY, algorithms=['HS256'])

    doc = {
        'number': number_receive,
        'id': payload['id']
    }
    db.join.insert_one(doc)

    return jsonify({'msg': '신청 완료!'})


@app.route("/posts", methods=["get"])
def render_cards():
    card_list = list(db.cards.find({}, {'_id': False}))
    return jsonify({'cards': card_list})


@app.route("/DataSend", methods=["get"])
def view_cards():
    index_receice = request.args.get("index_give")
    card_info = db.cards.find_one({'index': int(index_receice)}, {'_id': False})
    return jsonify({'cards': card_info})


@app.route("/posts", methods=["POST"])
def card_post():
    title_receive = request.form['title_give']
    place_receive = request.form['place_give']
    people_receive = request.form['people_give']
    time_receive = request.form['time_give']
    cardList_length = len(list(db.cards.find({}, {'_id': False})))
    card_index = cardList_length + 1

    options = webdriver.ChromeOptions()
    options.add_argument('headless')
    options.add_argument('window-size=1920x1080')
    options.add_argument("--disable-gpu")
    options.add_argument(
        "user-agent=Mozilla/5.0 (Macintosh; Intel Mac OS X 10_12_6) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/61.0.3163.100 Safari/537.36")
    driver = webdriver.Chrome('chromedriver', options=options)

    driver.get("https://www.google.co.kr/imghp?hl=ko&tab=wi&authuser=0&ogbl")
    elem = driver.find_element(By.NAME, "q")  # 구글 검색창 선택
    elem.send_keys(place_receive)  # 검색창에 검색할 내용(name)넣기
    elem.send_keys(Keys.RETURN)  # 검색할 내용을 넣고 enter를 치는것!
    driver.implicitly_wait(2)
    driver.find_element(By.XPATH,
                        '/html/body/div[2]/c-wiz/div[3]/div[1]/div/div/div/div[1]/div[1]/span/div[1]/div[1]/div[1]/a[1]/div[1]/img').click()
    time.sleep(1)
    imgUrl = driver.find_element(By.XPATH,
                                 '/html/body/div[2]/c-wiz/div[3]/div[2]/div[3]/div/div/div[3]/div[2]/c-wiz/div/div[1]/div[1]/div[3]/div/a/img').get_attribute(
        "src")
    driver.quit()

    obj = {
        'title': title_receive,
        'img': imgUrl,
        'place': place_receive,
        'people': people_receive,
        'time': time_receive,
        'index': card_index
    }
    db.cards.insert_one(obj);

    return jsonify({'msg': 'sucess'})


if __name__ == '__main__':
    app.run('0.0.0.0', port=5000, debug=True)
