from itertools import groupby
from flask import Flask, json, request
import pymongo
from bson import ObjectId
import ast
import json
from collections import Counter

MAX_MSG_LENGTH = 1024
SERVER_PORT = 5000
SERVER_IP = '0.0.0.0'

# Find post
def split_data(data):
    list = []
    for i in data:
        print(data)
        print(data.get(i))
        subjects = data.get(i).split("/")
        # TODO: make sure no name of objects (languages, technologies...) has the symbols that split (including the _ of id and login)
        value = subjects[-1]
        key = ""
        for j in range(len(subjects) - 1):
            key += subjects[j]
            if j < len(subjects) - 2:
                key += "."

        if " : " in value:
            value = {value.split(" : ")[0]: value.split(" : ")[1]}

        list.append({key: value})
    return list


def receive_posts(list):
    ret_list = []
    for value in list:
        for doc in my_post_col.find(value):
            doc['_id'] = str(doc['_id'])
            ret_list.append(doc)

    return ret_list


def order_posts(list):
    id_list = []
    for i in list:
        id_list.append(str(i.get('_id')))

    counts = Counter(id_list)
    result = sorted(counts, key=counts.get, reverse=True)

    posts = []
    index = 0
    for i in list:
        if index == len(result):
            break
        if i.get('_id') == str(ObjectId(result[index])):
            del i['_id']
            i['Business ID'] = str(i['Business ID']) #TODO: make sure the other side understands that ObjectID is now a string
            posts.append(i)
            index += 1

    print(posts)
    return posts


def convert_posts_to_unique_nums(posts):
    global unique_num_dict
    for i in range(len(posts)):
        unique_num_dict = {}
        unique_num("", posts[i])

        posts[i] = unique_num_dict
        unique_num_dict = {}

    print(posts)
    return posts
# #################

# send subjects to choose form
def get_subjects(subject):
    subjects = mydb.Subjects.find_one({"Subject": subject})
    del subjects['_id']
    del subjects['Subject']

    print(subjects)

    unique_num("", subjects)
    return unique_num_dict  # subjects


# Create post
def upload_post(subjects, business_id):
    post = {"Business ID": ObjectId(business_id)}

    post.update(subjects)

    id = my_post_col.insert_one(post)
    id = id.inserted_id

    mydb.Businesses.update_one({'_id': ObjectId(business_id)}, {"$set": {'posts': [id]}})


# Create Profile
def create_profile(username, password, subjects, profile_type):
    profile = {"_login": [username, password]} #TODO: encrypt and make sure users do not get this piece of info at all

    profile.update(subjects)

    if profile_type == 1:
        id = mydb.Businesses.insert_one(profile)
    else:
        id = mydb.Workers.insert_one(profile)

    return id.inserted_id

# /////////////////
global unique_num_dict
unique_num_dict = {}


# TODO: when the amount of digits run over, move to letters (lower case and then upper case)
def unique_num(parent, value):
    if type(value) == list:
        for i in range(len(value)):
            if parent != "":
                unique_num_dict[value[i]] = unique_num_dict[parent] + str(i+1)
            else:
                unique_num_dict[value[i]] = str(i+1)
        return
    elif type(value) != dict:
        unique_num_dict[value] = unique_num_dict[parent] + "1"
        return

    for i in range(len(value)):
        keys = []
        for key in value.keys():
            keys.append(key)

        if parent != "":
            unique_num_dict[keys[i]] = unique_num_dict[parent] + str(i+1)
        else:
            unique_num_dict[keys[i]] = str(i+1)

        unique_num(keys[i], value[keys[i]])


# ///////////
def is_email_exist(email):
    if len(list(mydb.Workers.find({"_login": {"$in": [email]}}))) > 0:
        print(True)
        return True

    if len(list(mydb.Businesses.find({"_login": {"$in": [email]}}))) > 0:
        print(True)
        return True

    print(False)
    return False


# ##########################
myclient = pymongo.MongoClient("mongodb+srv://Server1:1server@jobrowser.g2p5a.mongodb.net/")
mydb = myclient["JOBrowserDB"]
my_post_col = mydb["Posts"]
# mydb_business = mydb["Business"]
# mydb_workers = mydb["Workers"] #TODO: organize the variables that are related to the db



api = Flask(__name__)


@api.route('/GetPosts', methods=['POST'])
def get_posts():
    body = request.data.decode()
    print(body)
    data = json.loads(body)

    posts = order_posts(receive_posts(split_data(data)))
    convert_posts_to_unique_nums(posts)
    return json.dumps(posts)


@api.route('/CreatePost', methods=['POST'])
def create_post():
    body = request.data.decode()
    print(body)
    data = json.loads(body)

    #TODO: DELETE "620e6b4e91499fc9160a8339"  WHEN YOU ADD PROFILES, SO THE ID IS THE PROFILE'S
    upload_post(data, "620e6b4e91499fc9160a8339")  # subjects, business_id



@api.route('/GetSubjects', methods=['POST'])
def send_subjects_of_browser():
    body = request.data.decode()
    data = json.loads(body)

    if data == 1:
        subject = "Business"
    else:
        subject = "Workers"

    subjects = get_subjects(subject)
    print(subjects)
    return json.dumps(subjects)


@api.route('/InitialSignUp', methods=['POST'])
def initial_sign_up():
    body = request.data.decode()
    data = json.loads(body)

    if data == 1:
        subject = "Business Sign Up"
    else:
        subject = "Workers Sign Up"

    subjects = get_subjects(subject)
    return json.dumps(subjects)


@api.route('/InfoSignUp', methods=['POST'])
def info_sign_up():
    body = request.data.decode()
    data = json.loads(body)
    return json.dumps(str(create_profile(data[0], data[1], data[2], data[3])))



@api.route('/EmailExists', methods=['POST'])
def email_exists():
    body = request.data.decode()
    return json.dumps(is_email_exist(body))


if __name__ == '__main__':
    api.run(host='0.0.0.0')


# TODO: upgrade the functions that find dicts
# TODO: organize the code into classes
