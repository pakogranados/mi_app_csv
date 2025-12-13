from flask import Blueprint

api = Blueprint("api_mobile", __name__)  # nombre único garantizado

from . import auth_api
from . import caja_api
