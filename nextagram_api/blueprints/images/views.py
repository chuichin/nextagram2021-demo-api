from app import app, s3
from models.user import User
from models.image import Image
from flask import Blueprint, Flask, jsonify, request
from flask_jwt_extended import JWTManager, jwt_required, create_access_token, get_jwt_identity
from werkzeug.security import check_password_hash, generate_password_hash


images_api_blueprint = Blueprint('images_api',
                             __name__,
                             template_folder='templates')

jwt = JWTManager(app) 

# GET each user images
@images_api_blueprint.route("/", method=["GET"])
def images():
    userId = request.args.get("userId")
    images = Image.get(Image.user == userId)
    results = [images.image for each in images]
    if results:
        return jsonify(results), 200
    else:
        return jsonify(message="No images for this user")


@images_api_blueprint.route("/upload", method=["POST"])
@jwt_required()
def upload_images():
    user = User.get(User.username == get_jwt_identity())
    if request.content_length == 0:
        return jsonify(message="No images passed", status="failed"), 400
    elif request.files['images']:
        file = request.files.get('images')
        s3.upload_fileobj(
            file,
            "nextagram-api",
            f"users/{user.id}/images/{file.filename}",
            ExtraArgs={
                "ACL": "public-read",
                "ContentType": file.content_type
            }
        )
        new_image = Image.create(image=f"https://nextagram-api.s3-ap-southeast-1.amazonaws.com/users/{user.id}/images/{file.filename}", user=get_jwt_identity())
        if new_image.save():
            return jsonify(message="Successfully updated image")