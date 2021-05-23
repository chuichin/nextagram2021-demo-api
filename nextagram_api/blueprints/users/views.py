from app import app, s3
from models.user import User
from flask import Blueprint, Flask, jsonify, request
from flask_jwt_extended import JWTManager, jwt_required, create_access_token, get_jwt_identity
from werkzeug.security import check_password_hash, generate_password_hash


# /api/v1/users
users_api_blueprint = Blueprint('users_api',
                             __name__,
                             template_folder='templates')

jwt = JWTManager(app) 

# GET all users
@users_api_blueprint.route('/', methods=['GET'])
def index():
    users = User.select(User.id, User.username, User.profileImage)
    all_users = [{
        "id":user.id,
        "username":user.username,
        "profileImage":user.profileImage
    } for user in users]
    return jsonify(all_users)

# GET /users/<id>
@users_api_blueprint.route('/<id>', methods=['GET'])
def one_user(id):
    user = User.select(User.id, User.username, User.profileImage).where(User.id == id)
    one_user = [{
        "id":user.id,
        "username":user.username,
        "profileImage":user.profileImage
    } for user in user]
    return jsonify(one_user)

# GET /users/me
@users_api_blueprint.route('/me', methods = ["GET"])
@jwt_required()
def my_profile():
    current_user = get_jwt_identity()
    user = User.select(User.id, User.username, User.profileImage).where(User.username == current_user)
    response = [{
        "id":user.id,
        "username":user.username,
        "profileImage":user.profileImage
    } for user in user]
    return jsonify(response)

# GET/users/check_name
@users_api_blueprint.route('/check_name', methods=["GET"])
def check_name():
    username = request.args.get('username')
    existing_user = User.get_or_none(User.username == username)
    if existing_user:
        return jsonify({
            "exists": True,
            "valid": False
        }), 200
    else:
        return jsonify({
            "exists": False,
            "valid": True
        }), 200

# PUT /users/profileImage
@users_api_blueprint.route('/profileImage', methods=["PUT"])
@jwt_required()
def upload_profile_image():
    user = User.get_or_none(User.username == get_jwt_identity())
    if request.content_length == 0:
        return jsonify(message="No images passed", status="failed"), 400
    elif request.files['user_image']:
        file = request.files.get('user_image')
        s3.upload_fileobj(
            file,
            "nextagram-api",
            f"users/{user.id}/profile_image/{file.filename}",
            ExtraArgs={
                "ACL": "public-read",
                "ContentType": file.content_type
            }
        )
        update = User.update({User.profileImage:f"https://nextagram-api.s3-ap-southeast-1.amazonaws.com/users/{user.id}/profile_image/{file.filename}"}).where(User.username == get_jwt_identity()).execute()
        updated_user = User.get(User.username == get_jwt_identity())
    return jsonify({
        "message": "Successfully updated user",
        "user_id": updated_user.id,
        "image": updated_user.profileImage
    }), 200

# POST requests --------------------------------------

# POST /users
# Create new users
@users_api_blueprint.route('/new', methods=["POST"])
def sign_up():
    username = request.json.get("username", None)
    password = request.json.get("password", None)
    email = request.json.get("email", None)

    messages = []
    if User.get_or_none(User.username == username) or User.get_or_none(User.email == email):
        return jsonify(message=[
            "Email is already in use",
            "Username is already in use"
        ], status="failed"), 400
    else:
        newUser = User(username=username, email=email, password=generate_password_hash(password))
        if newUser.save():
            newUser = User.get(User.username == username, User.email == email)
            access_token = create_access_token(identity=newUser.username)
            success_response = [{
                "message" : "Successfully created a user and signed in",
                "status" : "success",
                "auth_token": access_token,
                "user": {
                        "id": newUser.id,
                        "username": newUser.username,
                        "profile_picture": newUser.profileImage
                }
            }]
        return jsonify(success_response)

# POST /users/login
@users_api_blueprint.route("/login", methods=["POST"])
def login():
    if request.content_length == 0:
        return jsonify(message="Nothing is passed to log in", status="Failed"), 400
    else: 
        username = request.json.get("username", None)
        password = request.json.get("password", None)
        user = User.get_or_none(User.username == username)
        if user:
            result=check_password_hash(user.password, password)
            access_token = create_access_token(identity=user.username)
            if result:
                return jsonify({
                    "auth_token": access_token,
                    "message": "Successfully signed in",
                    "status": "success", 
                    "user": {
                        "id": user.id,
                        "profileImage": user.profileImage,
                        "username": user.username
                    }
                }), 200
            else: 
                return jsonify({
                    "message": "Wrong password",
                    "status": "failed"
                }), 400
        else:
            return jsonify({
                "message": "This account doesn't exist",
                "status": "failed"
            }), 400
