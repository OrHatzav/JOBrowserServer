import hashlib
from itertools import groupby
from flask import Flask, json, request
import pymongo
from bson import ObjectId
import ast
import json
from collections import Counter

from Crypto.Cipher import AES
from Crypto import Random

MAX_MSG_LENGTH = 1024
SERVER_PORT = 5000
SERVER_IP = '0.0.0.0'

HASH_LENGTH = 32


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
            i['Business ID'] = str(
                i['Business ID'])
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
    post = {"Business ID": business_id}

    post.update(subjects)

    id = my_post_col.insert_one(post)
    id = id.inserted_id

    mydb.Businesses.update_one({'_id': ObjectId(business_id)}, {"$set": {'posts': [id]}})


# Create Profile
def create_profile(email, password, subjects, profile_type):

    msg = hashlib.md5(str(password).zfill(HASH_LENGTH).encode()).hexdigest()

    profile = {"_email": email,
               "_password": str(msg)}

    profile.update(subjects)

    print(profile_type)
    print(type(profile_type))
    if profile_type == "1":
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
                unique_num_dict[value[i]] = unique_num_dict[parent] + str(i + 1)
            else:
                unique_num_dict[value[i]] = str(i + 1)
        return

    elif type(value) != dict:
        unique_num_dict[value] = unique_num_dict[parent] + "1"
        return

    for i in range(len(value)):
        keys = []
        for key in value.keys():
            keys.append(key)

        if parent != "":
            unique_num_dict[keys[i]] = unique_num_dict[parent] + str(i + 1)
        else:
            unique_num_dict[keys[i]] = str(i + 1)

        unique_num(keys[i], value[keys[i]])


# ///////////
def is_email_exist(email):
    # if len(list(mydb.Businesses.find({"_login": {"$in": [email]}}))) > 0:
    #     return True
    # if len(list(mydb.Workers.find({"_login": {"$in": [email]}}))) > 0:
    #     return True
    if len(list(mydb.Businesses.find({"_email": email}))) > 0:
        return True

    if len(list(mydb.Workers.find({"_email": email}))) > 0:
        return True

    return False


def is_account_exist(email, password):
    print(email)
    print(password)

    msg = hashlib.md5(str(password).zfill(HASH_LENGTH).encode()).hexdigest()

    profile = mydb.Businesses.find_one({"_email": email, "_password": msg})
    if not profile is None:
        profile['_id'] = str(profile['_id'])
        del profile['_email']
        del profile['_password']

        print(profile)
        return profile

    profile = mydb.Workers.find_one({"_email": email, "_password": password})
    if not profile is None:
        profile['_id'] = str(profile['_id'])
        del profile['_email']
        del profile['_password']

        print(profile)
        return profile

    return False


def get_profile_page(id):
    try:
        if id[0] == "0":
            doc = mydb.Businesses.find_one({'_id': ObjectId(id[1:])})
        else:
            doc = mydb.Workers.find_one({'_id': ObjectId(id[1:])})

        print(doc)
        del doc['_id']
        del doc['_email']
        del doc['_password']

        print(doc)
        return doc

    except():
        pass


# ##########################
myclient = pymongo.MongoClient("mongodb+srv://Server1:1server@jobrowser.g2p5a.mongodb.net/")
mydb = myclient["JOBrowserDB"]
my_post_col = mydb["Posts"]
my_businesses_col = mydb["Businesses"]
my_workers_col = mydb["Workers"]

 #TODO: organize the variables that are related to the db


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

    upload_post(data[0], data[1])  # subjects, business_id


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


@api.route('/CreateProfile', methods=['POST'])
def create_pro():
    body = request.data.decode()
    print(body)
    data = json.loads(body)
    return json.dumps(
        str(create_profile(data["NewProfile"][0], data["NewProfile"][1], data["NewProfile"][2], data["NewProfile"][3])))


@api.route('/EmailExists', methods=['POST'])
def email_exists():
    body = request.data.decode()
    return json.dumps(is_email_exist(body))


@api.route('/SignIn', methods=['POST'])
def sign_in():
    body = request.data.decode()
    data = json.loads(body)
    return json.dumps(is_account_exist(data["email"], data["password"]))


@api.route('/GetProfile', methods=['POST'])
def get_pro():
    body = request.data.decode()
    data = json.loads(body)
    return json.dumps(get_profile_page(data))


if __name__ == '__main__':
    api.run(host='0.0.0.0')

# TODO: organize the code into classes
