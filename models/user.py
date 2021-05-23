from models.base_model import BaseModel
import peewee as pw


class User(BaseModel):
    username = pw.CharField(unique=True)
    email = pw.CharField(unique=True)
    password= pw.CharField(null=False)
    profileImage = pw.CharField(default="http://next-curriculum-instagram.s3.amazonaws.com/profile-placeholder.jpg")
