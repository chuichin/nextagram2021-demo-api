from app import app
from flask import Flask
from flask_cors import CORS 

cors = CORS(app, resources={r"/api/*": {"origins": "*"}})

## API Routes ##
from nextagram_api.blueprints.users.views import users_api_blueprint
from nextagram_api.blueprints.images.views import images_api_blueprint


app.register_blueprint(users_api_blueprint, url_prefix='/api/v1/users')
app.register_blueprint(images_api_blueprint,  url_prefix='/api/v1/images')
