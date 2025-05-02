# app/models.py
import logging
# Obtener el logger de Flask si está disponible, o uno básico si no
try:
    from flask import current_app
    logger = current_app.logger
except RuntimeError: # Fuera de un contexto de aplicación
    logger = logging.getLogger(__name__)
    if not logger.hasHandlers():
        logging.basicConfig(level=logging.INFO, format='%(asctime)s %(levelname)s: %(message)s [in %(pathname)s:%(lineno)d]')

logger.info("--- Cargando app/models.py ---")

try:
    from .extensions import db
    logger.info("Importado 'db' desde .extensions exitosamente.")
except ImportError as e:
    logger.error(f"ERROR al importar 'db' desde .extensions: {e}", exc_info=True)
    db = None # Definir db como None para evitar errores posteriores si la importación falla

from datetime import datetime, date
logger.info("Importados datetime y date.")

if db:
    logger.info("Definiendo la clase Expense...")
    class Expense(db.Model):
        __tablename__ = 'expenses'
        id = db.Column(db.Integer, primary_key=True)
        amount = db.Column(db.Float, nullable=False)
        description = db.Column(db.String(200), nullable=False)
        category = db.Column(db.String(50), nullable=False, default="otros")
        created_at = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)
        expense_date = db.Column(db.Date, nullable=False, default=date.today)

        def __repr__(self):
            return f"<Expense {self.id}: {self.amount} en {self.category} el {self.expense_date.strftime('%Y-%m-%d')}>"

        def to_dict(self):
            return {
                'id': self.id,
                'amount': self.amount,
                'description': self.description,
                'category': self.category,
                'created_at': self.created_at.isoformat(),
                'expense_date': self.expense_date.isoformat()
            }
    logger.info("Clase Expense definida.")

    # Verificar si Expense existe en el módulo actual justo después de definirla
    if 'Expense' in locals() or 'Expense' in globals():
         logger.info("VERIFICACIÓN: 'Expense' SÍ existe en el scope local/global de models.py ahora.")
    else:
         logger.warning("VERIFICACIÓN: 'Expense' NO existe en el scope local/global de models.py ahora. ¡Muy extraño!")

else:
    logger.error("No se pudo definir la clase Expense porque 'db' no se importó correctamente.")


logger.info("--- Fin de la carga de app/models.py ---")

# Puedes añadir otras clases de modelos aquí si las tienes...

