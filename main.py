import requests
from flask import Flask, jsonify
from flask import request
import datetime
import sqlite3 as lite

app = Flask(__name__)
app.config["DEBUG"] = True
con = lite.connect('system.db', check_same_thread=False)

with con:
    cur = con.cursor()

# clear db
    # cur.execute("DROP TABLE Users")
    # cur.execute("DROP TABLE posts")
    # cur.execute("DROP TABLE user_votes")


    try:
        cur.execute("CREATE TABLE Users(username TEXT, password TEXT)")
    except:
        print("Table already exists")

    cur.execute("INSERT INTO Users VALUES('guy','hayo')")
    cur.execute("INSERT INTO Users VALUES('admin','admin')")
    cur.execute("INSERT INTO Users VALUES('root','password')")

    try:
        cur.execute("CREATE TABLE posts(id INT , author TEXT, text TEXT, create_date DATETIME, update_date, vote INT)")
    except:
        print("Table already exists")

    try:
        cur.execute(
            "CREATE TABLE user_votes(post_id INT , UserVoted)")
    except:
        print("Table already exists")

@app.route('/')
def index():
    return 'To reed the top posts use get requset: /posts \n\r' \
           'To create post use post request: /posts?text=post text&user=username$password=password \n\r' \
           'To reed post use get request: /posts/post_id \n\r' \
           'To update your post use put request: /posts/post_id?text=post text&user=username$password=password \n\r' \
           'To like post use get requset: /post_like/post_id?user=username$password=password \n\r' \
           'To unlike post use get requset: /post_unlike/post_id?user=username$password=password \n\r'

Id = 0
Top_post = list()

def get_id():
    return Id

def generate_next_post_id():
    global Id
    Id += 1

@app.route('/posts', methods=['POST', 'GET'])
def create_post_or_show_them():
    if request.method == 'POST':
        if not validate_request():
            return "Bad user and password"
        if not 'text' in request.args:
            return "no text provided"
        data = dict()
        data['id'] = get_id()
        data['author'] = request.args['user']
        data['text'] = request.args['text']
        data['create_date'] = datetime.datetime.now()
        data['update_date'] = None
        data['vote'] = 0
        resp = jsonify(data)
        resp.status_code = 200
        cur.execute("INSERT INTO posts VALUES(?,?,?,?,?,?)", (get_id(), request.args['user'],
                                                      request.args['text'], datetime.datetime.now(), 'None', 0))
        generate_next_post_id()
        add_post_to_top_post_list_if_necseray(data)
        return "The post noted"
    else:
        resp = jsonify(Top_post)
        resp.status_code = 200
        return resp

@app.route('/posts/<int:post_id>', methods=['GET', 'PUT'])
def reed_or_update_post(post_id):
    post = find_post(post_id)
    if post is not None:
        data = dict()
        data['id'], data['author'], data['text'], data['create_date'], data['update_date'], data['vote'] = post
        if request.method == 'GET':
            resp = jsonify(data)
            resp.status_code = 200
            return resp
        else:
            if validate_request():
                if not 'text' in request.args:
                    return "no text provided"
                if not request.args['user'] == data['author']:
                    return "You cannot edit post that not yours"
                update_date = datetime.datetime.now()
                cur.execute("UPDATE posts SET text = ?, update_date = ? WHERE id = ?", (request.args['text'],
                                                                                        update_date, post_id))
                index = is_post_in_top_post(post_id)
                if not index == -1:
                    Top_post[index]['text'] = request.args['text']
                    Top_post[index]['update_date'] = update_date
                return "change cpmmited"
    return "post id didn't exist"

@app.route('/post_like/<int:post_id>', methods=['GET'])
def like_post(post_id):
    return like_unlike(post_id, True)

@app.route('/post_unlike/<int:post_id>', methods=['GET'])
def unlike_post(post_id):
    return like_unlike(post_id, False)


def like_unlike(post_id, add_one_to_vote):
    post = find_post(post_id)
    if post is not None:
        data = dict()
        data['id'], data['author'], data['text'], data['create_date'], data['update_date'], data['vote'] = post
        if validate_request():
            if not check_if_already_vote_for_post(post_id, request.args['user']):
                if add_one_to_vote:
                    data['vote'] += 1
                else:
                    data['vote'] -= 1
                cur.execute("UPDATE posts SET vote = ? WHERE id = ?", (data['vote'], post_id))
                index = is_post_in_top_post(data['id'])
                if not index == -1:
                    Top_post[index] = data
                cur.execute("INSERT INTO user_votes VALUES(?,?)", (post_id, request.args['user']))
                add_post_to_top_post_list_if_necseray(data)
                return "your vote noted"
            else:
                return "You already voted"
        return ("bad username or password")
    return "post_id doesn't exists"


def check_if_already_vote_for_post(post_id, user):
    cur.execute("SELECT * FROM user_votes WHERE post_id=%d" % post_id)
    user_vote = cur.fetchall()
    for (id, username) in user_vote:
        if user in username:
            return True
    return False

def validate_request():
    if not 'user' in request.args or not 'password' in request.args:
        print("you are not loged in, please add user and password")
        return False
    if not validate_login(user=request.args['user'], password=request.args['password']):
        print("bad username or password")
        return False
    return True

def validate_login(user, password):
    cur.execute("SELECT * FROM Users WHERE username='%s'" % user)
    fetch = cur.fetchone()
    if fetch is not None:
        user_db, pass_db = fetch
        if password == pass_db:
            return True
    return False


def add_post_to_top_post_list_if_necseray(data):
    index = is_post_in_top_post(data['id'])
    if index == -1:
        if len(Top_post) < 100:
            Top_post.append(data)
        else:
            last_in_top_post = Top_post[-1]
            if last_in_top_post['vote'] <= data['vote']:
                Top_post[-1] = data
    sort_top_post_list()

def find_post(post_id):
    cur.execute("SELECT * FROM posts WHERE id=%d" % post_id)
    post = cur.fetchone()
    return post

def is_post_in_top_post(post_id):
    # return -1 if false
    # return index if exist
    index = 0
    while index < len(Top_post):
        temp = Top_post[index]
        if post_id == temp['id']:
            return index
        index += 1
    return -1

def sort_top_post_list():
    global Top_post
    temp = sorted(Top_post, key=lambda k: (k['vote'], k['create_date']))
    Top_post = list(reversed(temp))

# def test():
#     r = requests.post("http://127.0.0.1:5000/posts?text=FirstPostGuy&user=guy&password=hayo", data="")
#     print(r.text)
#     r = requests.post("http://127.0.0.1:5000/posts?text=SecPostGuy&user=guy&password=hayo", data="")
#     print(r.text)
#     r = requests.post("http://127.0.0.1:5000/posts?text=FirstPostadmin&user=admin&password=admin", data="")
#     print(r.text)
#     r = requests.put("http://127.0.0.1:5000/posts/0?text=FirstPostGuyChanged&user=guy&password=hayo", data="")
#     print(r.text)
#     r = requests.get("http://127.0.0.1:5000/post_like/0?user=Guy&password=hayo", data="")
#     print(r.text)
#     r = requests.get("http://127.0.0.1:5000/post_unlike/1?user=Guy&password=hayo", data="")
#     print(r.text)

if __name__ == '__main__':
    app.run()
