# app/__init__.py
import os
from flask import Flask
from .config import config
from .extensions import db
import logging
# Importar SQLAlchemyError para capturar posibles errores de DB al crear tablas
from sqlalchemy.exc import SQLAlchemyError

def create_app(config_name=None):
    """Application Factory."""
    if config_name is None:
        config_name = os.getenv('FLASK_ENV', 'default')

    app = Flask(__name__)
    app.config.from_object(config[config_name])
    config[config_name].init_app(app) # Métodos init_app de la config si los hay

    # Configurar logging básico
    # Mover la configuración del logger aquí para que esté disponible antes
    log_level = app.config.get('LOG_LEVEL', 'INFO').upper()
    logging.basicConfig(level=getattr(logging, log_level, logging.INFO),
                        format='%(asctime)s %(levelname)s: %(message)s [in %(pathname)s:%(lineno)d]')

    # Usar el logger de la app a partir de ahora
    app.logger.info(f"Aplicación creada con configuración: {config_name}")
    app.logger.info(f"Database URI: {app.config.get('SQLALCHEMY_DATABASE_URI')}") # Log DB URI
    app.logger.info(f"WhatsApp API URL: {app.config.get('WHATSAPP_API_URL')}")
    if not app.config.get('WHATSAPP_TOKEN'):
         app.logger.warning("WHATSAPP_TOKEN no está configurado!")
    if not app.config.get('WHATSAPP_VERIFY_TOKEN'):
         app.logger.warning("WHATSAPP_VERIFY_TOKEN no está configurado!")


    # Inicializar extensiones
    db.init_app(app)
    # Aquí inicializarías otras extensiones: migrate.init_app(app, db), etc.

    # --- Crear tablas si no existen ---
    # Es importante hacerlo dentro del contexto de la aplicación
    with app.app_context():
        app.logger.info("Verificando y creando tablas de base de datos si no existen...")
        try:
            # Importar modelos aquí para que db.create_all los vea
            # Es una forma de asegurar que se carguen antes de create_all
            from . import models
            db.create_all()
            app.logger.info("db.create_all() ejecutado exitosamente.")
        except SQLAlchemyError as e:
            app.logger.error(f"Error al ejecutar db.create_all(): {e}", exc_info=True)
        except Exception as e:
            # Capturar otros posibles errores durante la importación o creación
            app.logger.error(f"Error inesperado durante la creación inicial de tablas: {e}", exc_info=True)
    # --- Fin de crear tablas ---

    # Registrar Blueprints
    # Mover la importación aquí para evitar posibles ciclos si los blueprints
    # necesitaran algo inicializado antes (aunque en este caso no parece)
    from .routes import webhook_bp
    app.register_blueprint(webhook_bp)

    # (Opcional) Rutas simples directamente aquí si son muy pocas
    @app.route('/health')
    def health_check():
        # Podríamos añadir un chequeo de DB aquí si quisiéramos
        # try:
        #     db.session.execute('SELECT 1')
        #     db_status = "OK"
        # except Exception as e:
        #     app.logger.error(f"Health check DB error: {e}")
        #     db_status = "Error"
        # return f"App: OK, DB: {db_status}", 200 if db_status == "OK" else 500
        return "OK", 200

    app.logger.info("Aplicación configurada y lista.")
    return app

