# run.py
import os
import sys
from app import create_app, db # Importa db desde app/__init__.py o extensions.py

# Configura la codificación de salida si es necesario (puede ir en create_app también)
sys.stdout.reconfigure(encoding='utf-8')

# Carga la configuración desde variables de entorno (ej: 'development' o 'production')
config_name = os.getenv('FLASK_ENV', 'development')
app = create_app(config_name)

# Crear tablas si no existen (Mejor usar Flask-Migrate para producción)
with app.app_context():
    print("Creando tablas si no existen...")
    db.create_all()
    print("Tablas listas.")

if __name__ == '__main__':
    # El puerto y debug se pueden configurar en config.py o aquí
    port = int(os.getenv('PORT', 5000))
    debug_mode = app.config.get('DEBUG', False)
    print(f"Iniciando servidor en puerto {port} con debug={debug_mode}")
    app.run(debug=debug_mode, port=port, host='0.0.0.0') # host='0.0.0.0' para accesibilidad en red