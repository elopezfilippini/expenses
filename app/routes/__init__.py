from flask import Blueprint

# Define el blueprint ANTES de importar las rutas
webhook_bp = Blueprint('webhook', __name__, url_prefix='/webhook')

# Importa el archivo con las @webhook_bp.route DESPUÉS
from . import webhook