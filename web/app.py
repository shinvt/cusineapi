from flask import Flask,jsonify,request
from flask_restful import Api, Resource
from pymongo import MongoClient
import bcrypt
import pickle

app = Flask(__name__)
api = Api(app)

client = MongoClient("mongodb://db:27017")
db = client.RecipeDB
users = db["Users"]

def UserExist(username):
    if users.find({
        "Username":username
    }).count() == 0:
        return False
    else:
        return True

class Register(Resource):
    def post(self):
        postedData = request.get_json()

        username = postedData["username"]
        password = postedData["password"]

        if UserExist(username):
            retJson = {
                "status" : 301,
                "msg" : "Invalid Username"
            }
            return jsonify(retJson)

        hashed_pw = bcrypt.hashpw(password.encode('utf8'),bcrypt.gensalt())

        users.insert({
            "Username": username,
            "Password": hashed_pw,
            "Tokens": 10
        })

        retJson = {
            "status": 200,
            "msg":"You're successfully signed up to the API"
        }

        return jsonify(retJson)

def verifyPw(username,password):
    if not UserExist(username):
        return False

    hashed_pw = users.find({
        "Username":username
    })[0]["Password"]

    if bcrypt.hashpw(password.encode('utf8'),hashed_pw)== hashed_pw:
        return True
    else:
        return False

def countTokens(username):
    tokens = users.find({
        "Username": username
    })[0]["Tokens"]

    return tokens


class Recommend(Resource):
    def post(self):
        postedData = request.get_json()

        username = postedData["username"]
        password = postedData["password"]
        ingredients = postedData["ingredients"]

        if not UserExist(username):
            retJson = {
                "status": "301",
                "msg": "Invalid username"
            }
            return jsonify(retJson)

        correct_pw = verifyPw(username,password)

        if not correct_pw:
            retJson = {
                "status": "302",
                "msg": "Invalid password"
            }
            return jsonify(retJson)

        num_tokens = countTokens(username)

        if num_tokens <= 0:
            retJson = {
                "status": 303,
                "msg": "You're out of tokens, please refill"
            }
            return jsonify(retJson)

        loaded_model = pickle.load(open("recipemodel.sav","rb"))
        loaded_vec = pickle.load(open("vector.sav","rb"))

        ingredients_vec = loaded_vec.transform(ingredients).toarray()

        recipe =  loaded_model.predict(ingredients_vec).tolist()

        print("Recipe : /n")
        print(recipe)

        retJson = {
            "status": 200,
            "recipe": recipe,
            "msg": "This is the type of cuisine recommedation for you"
        }

        current_tokens = countTokens(username)

        users.update({
            "Username": username,
        },{
            "$set": {
                "Tokens": current_tokens -1
            }
        })

        return jsonify(retJson)

class Refill(Resource):
    def post(self):
        postedData = request.get_json()

        username = postedData["username"]
        password = postedData["admin_pw"]
        refill_amount = postedData["refill"]

        if not UserExist(username):
            retJson = {
                "status": 301,
                "msg": "Invalid username"
            }
            return jsonify(retJson)

        correct_pw = "abc123"

        if not password == correct_pw:
            retJson = {
                "status": 304,
                "msg": "Invalid Admin Password"
            }
            return jsonify(retJson)

        current_tokens = countTokens(username)

        users.update({
            "Username": username
        },{
            "$set": {
                "Tokens": refill_amount + current_tokens
            }
        })

        retJson = {
            "status": 200,
            "msg": "Refilled successfully"
        }

        return jsonify(retJson)



api.add_resource(Register,'/register')
api.add_resource(Recommend,'/recommend')
api.add_resource(Refill,'/refill')

if __name__ == "__main__":
    app.run(host='0.0.0.0')
