import requests
from flask import Flask, jsonify
from flask import request
import datetime
app = Flask(__name__)


@app.route('/')
def index():
    return 'To reed the top posts use get requset: /posts \n' \
           'To reed all the posts use get requset: /all_posts \n' \
           'To create post use post request: /posts?text=post text&user=username$password=password \n' \
           'To reed post use get request: /posts/post_id \n' \
           'To update your post use put request: /posts/post_id?text=post text&user=username$password=password \n' \
           'To like post use get requset: /post_like/post_id?user=username$password=password \n' \
           'To unlike post use get requset: /post_unlike/post_id?user=username$password=password \n'

Id = 0
All_posts = dict()
Registart_users = {'Guy': 'hayo', 'admin': 'admin'}
Top_post = list()

def get_id():
    return Id

def generate_next_post_id():
    global Id
    Id += 1

@app.route('/all_posts', methods=['GET'])
def reed_all_posts():
    resp = jsonify(All_posts)
    resp.status_code = 200
    return resp


@app.route('/posts', methods=['POST', 'GET'])
def create_post_or_show_them():
    if request.method == 'POST':
        if not validate_request():
            return "Bad user and password"
        if not 'text' in request.args:
            return "no text provided"
        data = dict()
        data['id'] = get_id()
        generate_next_post_id()
        data['author'] = request.args['user']
        data['vote'] = 0
        data['text'] = request.args['text']
        data['listOfUserVoted'] = list()
        data['create_date'] = datetime.datetime.now()
        data['update_date'] = None
        resp = jsonify(data)
        resp.status_code = 200
        All_posts[data['id']] = data
        add_post_to_top_post_list_if_nessery(data)
        return resp
    else:
        resp = jsonify(Top_post)
        resp.status_code = 200
        return resp

@app.route('/posts/<int:post_id>', methods=['GET', 'PUT'])
def reed_or_update_post(post_id):
    if post_id in All_posts.keys():
        if request.method == 'GET':
            resp = jsonify(All_posts[post_id])
            resp.status_code = 200
            return resp
        else:
            if validate_request():
                if not 'text' in request.args:
                    return "no text provided"
                data = All_posts[post_id]
                if not request.args['user'] == data['author']:
                    return "You cannot edit post that not yours"
                data = All_posts[post_id]
                data['text'] = request.args['text']
                data['update_date'] = datetime.datetime.now()
                resp = jsonify(data)
                resp.status_code = 200
                return resp
    else:
        return "post_id dosent exist"

@app.route('/post_like/<int:post_id>', methods=['GET'])
def like_post(post_id):
    if post_id in All_posts.keys():
        if validate_request():
            data = All_posts[post_id]
            if not check_if_already_vote_for_post(data, request.args['user']):
                data['vote'] += 1
                data['listOfUserVoted'].append(request.args['user'])
                add_post_to_top_post_list_if_nessery(data)
            else:
                return "You already voted"
    return "your vote noted"

@app.route('/post_unlike/<int:post_id>', methods=['GET'])
def unlike_post(post_id):
    if post_id in All_posts.keys():
        if validate_request():
            data = All_posts[post_id]
            if not check_if_already_vote_for_post(data, request.args['user']):
                data['vote'] -= 1
                data['listOfUserVoted'].append(request.args['user'])
                add_post_to_top_post_list_if_nessery(data)
            else:
                return "You already voted"
    return "your vote noted"

def check_if_already_vote_for_post(data, user):
    return user in data['listOfUserVoted']

def validate_request():
    if not 'user' in request.args or not 'password' in request.args:
        print("you are not loged in"
              "please add user and password")
        return False
    if not validate_login(user=request.args['user'], password=request.args['password']):
        print("bad username or password")
        return False
    return True

def validate_login(user, password):
    if user in Registart_users.keys():
        if password == Registart_users[user]:
            return True
    return False


def add_post_to_top_post_list_if_nessery(data):
    if Top_post.count() < 2:
        Top_post.append(data)
    else:
        last_in_top_post = Top_post[-1]
        if last_in_top_post['vote'] <= data['vote']:
            Top_post[-1] = data
    sort_top_post_list()

def sort_top_post_list():
    global Top_post
    temp = sorted(Top_post, key=lambda k: (k['vote'], k['create_date']))
    Top_post = list(reversed(temp))

def test():
    r = requests.post("http://127.0.0.1:5000/posts?text=FirstPostGuy&user=Guy&password=hayo", data="")
    print(r.text)
    r = requests.post("http://127.0.0.1:5000/posts?text=SecPostGuy&user=Guy&password=hayo", data="")
    print(r.text)
    r = requests.post("http://127.0.0.1:5000/posts?text=FirstPostadmin&user=admin&password=admin", data="")
    print(r.text)
    r = requests.put("http://127.0.0.1:5000/posts/0?text=FirstPostGuyChanged&user=Guy&password=hayo", data="")
    print(r.text)
    r = requests.get("http://127.0.0.1:5000/post_like/2?user=Guy&password=hayo", data="")
    print(r.text)
    r = requests.get("http://127.0.0.1:5000/post_unlike/1?user=Guy&password=hayo", data="")
    print(r.text)

if __name__ == '__main__':
    app.run()
