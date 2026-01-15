from flask import Blueprint

depo_bp = Blueprint('depo', __name__, url_prefix='/depo')

from app.modules.depo import routes
