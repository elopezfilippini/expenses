# app/config.py
import os
from dotenv import load_dotenv

# Carga las variables de .env al entorno (opcional si usas .flaskenv y auto-load)
basedir = os.path.abspath(os.path.dirname(__file__))
load_dotenv(os.path.join(basedir, '..', '.env')) # Carga desde el directorio raíz

class Config:
    """Configuración base."""
    SECRET_KEY = os.getenv('SECRET_KEY', 'una_clave_secreta_por_defecto_insegura')
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    WHATSAPP_TOKEN = os.getenv('WHATSAPP_TOKEN')
    WHATSAPP_VERIFY_TOKEN = os.getenv('WHATSAPP_VERIFY_TOKEN')
    PHONE_NUMBER_ID = os.getenv('PHONE_NUMBER_ID')
    WHATSAPP_API_VERSION = os.getenv('WHATSAPP_API_VERSION', 'v22.0')
    WHATSAPP_API_URL = f"https://graph.facebook.com/{WHATSAPP_API_VERSION}/{PHONE_NUMBER_ID}/messages"
    # Otras configuraciones globales

    @staticmethod
    def init_app(app):
        pass

class DevelopmentConfig(Config):
    """Configuración de desarrollo."""
    DEBUG = True
    SQLALCHEMY_DATABASE_URI = os.getenv('DATABASE_URL', 'sqlite:///' + os.path.join(basedir, '..', 'dev.db'))
    print(f"Development DB URI: {SQLALCHEMY_DATABASE_URI}")
    print(f"WhatsApp Token Loaded (Dev): {'Set' if Config.WHATSAPP_TOKEN else 'Not Set'}")

class ProductionConfig(Config):
    """Configuración de producción."""
    DEBUG = False
    SQLALCHEMY_DATABASE_URI = os.getenv('DATABASE_URL') # Obligatorio en producción
    # Configuraciones adicionales de producción (logging, etc.)
    print(f"Production DB URI: {SQLALCHEMY_DATABASE_URI}")
    print(f"WhatsApp Token Loaded (Prod): {'Set' if Config.WHATSAPP_TOKEN else 'Not Set'}")


# Mapeo para cargar la configuración correcta en create_app
config = {
    'development': DevelopmentConfig,
    'production': ProductionConfig,
    'default': DevelopmentConfig
}