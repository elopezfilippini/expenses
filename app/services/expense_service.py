# app/services/expense_service.py
from ..extensions import db
# No importamos models ni Expense globalmente
from datetime import date, datetime
from dateutil.relativedelta import relativedelta
from sqlalchemy import desc
import logging

logger = logging.getLogger(__name__)

def generate_expense_report(start_date=None, end_date=None, detailed=False):
    """Genera un string con el reporte de gastos."""
    # Importación local del módulo models
    from .. import models
    try:
        # Acceder a Expense a través del módulo models
        query = models.Expense.query

        # Ajuste: Usar expense_date para filtrar por fecha del gasto
        if start_date and end_date:
            # Asegurarse que son objetos date
            if isinstance(start_date, str): start_date = date.fromisoformat(start_date)
            if isinstance(end_date, str): end_date = date.fromisoformat(end_date)
            logger.info(f"Filtrando reporte entre {start_date} y {end_date}")
            query = query.filter(models.Expense.expense_date >= start_date, models.Expense.expense_date <= end_date)
        elif start_date: # Solo fecha de inicio
             if isinstance(start_date, str): start_date = date.fromisoformat(start_date)
             logger.info(f"Filtrando reporte desde {start_date}")
             query = query.filter(models.Expense.expense_date >= start_date)
        elif end_date: # Solo fecha de fin
            if isinstance(end_date, str): end_date = date.fromisoformat(end_date)
            logger.info(f"Filtrando reporte hasta {end_date}")
            query = query.filter(models.Expense.expense_date <= end_date)
        else: # Reporte completo si no hay fechas
             logger.info("Generando reporte completo (sin filtro de fecha)")


        # Ordenar por fecha para el reporte detallado
        expenses = query.order_by(models.Expense.expense_date).all()

        report_summary = {}
        for expense in expenses:
            report_summary[expense.category] = report_summary.get(expense.category, 0) + expense.amount

        message_body = "📊 *Reporte de Gastos*\n"
        if start_date or end_date:
             period_str = ""
             if start_date: period_str += f"Desde: {start_date.strftime('%d/%m/%Y')} "
             if end_date: period_str += f"Hasta: {end_date.strftime('%d/%m/%Y')}"
             message_body += f"*{period_str.strip()}*\n"


        if detailed:
            message_body += "\n📝 *Detalles:*\n"
            if expenses:
                for expense in expenses:
                    # Usar expense_date
                    message_body += f"• {expense.expense_date.strftime('%d/%m/%Y')}: ${expense.amount:.2f} - {expense.description} ({expense.category})\n"
            else:
                message_body += "_No hay gastos registrados_"
                if start_date or end_date: message_body += " en este período."
                message_body += "_\n"


        message_body += "\n📌 *Resumen por categoría:*\n"
        if report_summary:
             for category, total in sorted(report_summary.items()): # Ordenado alfabéticamente
                 message_body += f"• {category.title()}: ${total:.2f}\n"
        else:
            message_body += "_No hay gastos para resumir_"
            if start_date or end_date: message_body += " en este período."
            message_body += "_\n"


        total_gastos = sum(report_summary.values())
        message_body += f"\n💰 *Total General*: ${total_gastos:.2f}"

        return message_body

    except Exception as e:
        logger.exception("Error generando reporte de gastos")
        return "❌ Error al generar el reporte."


def record_single_expense(amount: float, description: str, category: str, expense_date: date = None):
    """Registra un único gasto en la base de datos."""
    # Importación local del módulo models
    from .. import models
    try:
        if expense_date is None:
            expense_date = date.today()
        elif isinstance(expense_date, str):
             try:
                 expense_date = date.fromisoformat(expense_date)
             except ValueError:
                 logger.error(f"Formato de fecha inválido para gasto único: {expense_date}")
                 raise ValueError("La fecha proporcionada para el gasto tiene un formato inválido (se espera YYYY-MM-DD).")

        # Acceder a Expense a través del módulo models
        new_expense = models.Expense(
            amount=amount,
            description=description,
            category=category,
            expense_date=expense_date
        )
        db.session.add(new_expense)
        db.session.commit()
        logger.info(f"Gasto único registrado: ID={new_expense.id}, Monto={amount}, Desc={description}, Cat={category}, Fecha={expense_date}")
        return new_expense
    except Exception as e:
        db.session.rollback()
        logger.exception("Error al registrar gasto único")
        raise


def record_installments(num_installments: int, total_amount: float, description: str, category: str, start_date: date = None):
    """Registra múltiples gastos correspondientes a cuotas."""
    # Importación local del módulo models
    from .. import models
    if num_installments <= 0:
        raise ValueError("El número de cuotas debe ser mayor a 0.")
    if total_amount < 0:
         raise ValueError("El monto total no puede ser negativo.")

    installment_amount = round(total_amount / num_installments, 2)

    if start_date is None:
        start_date = date.today()
    elif isinstance(start_date, str):
        try:
            start_date = date.fromisoformat(start_date)
        except ValueError:
            logger.error(f"Formato de fecha inválido para inicio de cuotas: {start_date}")
            raise ValueError("La fecha de inicio proporcionada para las cuotas tiene un formato inválido (se espera YYYY-MM-DD).")


    logger.info(f"Registrando {num_installments} cuotas de ${installment_amount:.2f} para '{description}' ({category}). Total: ${total_amount:.2f}. Inicio: {start_date}")

    created_expenses = []
    try:
        for i in range(num_installments):
            current_installment_date = start_date + relativedelta(months=i)
            installment_description = f"{description} (Cuota {i+1}/{num_installments})"

            # Acceder a Expense a través del módulo models
            new_expense = models.Expense(
                amount=installment_amount,
                description=installment_description,
                category=category,
                expense_date=current_installment_date
            )
            db.session.add(new_expense)
            logger.info(f"   Preparando Cuota {i+1}: Fecha={current_installment_date.strftime('%Y-%m-%d')}, Monto={installment_amount:.2f}")
            created_expenses.append(new_expense)

        db.session.commit()
        logger.info(f"Se han registrado {len(created_expenses)} cuotas en la BD.")
        return created_expenses
    except Exception as e:
        db.session.rollback()
        logger.exception("Error al registrar cuotas")
        raise


def delete_last_expense():
    """Elimina el último gasto registrado (por ID)."""
    # Importación local del módulo models
    from .. import models
    try:
        # Acceder a Expense a través del módulo models
        last_expense = models.Expense.query.order_by(desc(models.Expense.id)).first()
        if last_expense:
            deleted_info = {
                'id': last_expense.id,
                'amount': last_expense.amount,
                'description': last_expense.description,
                'category': last_expense.category,
                'expense_date': last_expense.expense_date
            }
            db.session.delete(last_expense)
            db.session.commit()
            logger.info(f"Último gasto eliminado: ID={deleted_info['id']}")
            return deleted_info
        else:
            logger.info("No se encontraron gastos para borrar.")
            return None
    except Exception as e:
        db.session.rollback()
        logger.exception("Error al eliminar el último gasto")
        raise


def parse_expense_message(message_body: str):
    """
    Analiza el cuerpo del mensaje para determinar la acción y extraer datos.
    Devuelve un diccionario con 'action' y 'data'.
    Lanza ValueError si el formato es inválido.
    """
    # Esta función NO necesita importar models, así que no se añade aquí.
    message_body = message_body.strip().lower()
    logger.debug(f"Parseando mensaje: '{message_body}'")

    # (El resto del código de parse_expense_message permanece igual que antes)
    # ... (código omitido por brevedad, es idéntico al de la versión anterior) ...

    # Comandos específicos
    if message_body.startswith('reporte'):
        detailed = 'detallado' in message_body
        return {'action': 'report', 'data': {'detailed': detailed}}

    if message_body == 'borrar':
        return {'action': 'delete_last', 'data': {}}

    if message_body.startswith('cuotas '):
        parts = message_body.split(' ', 3) # cuotas N Monto Descripcion [con Categoria]
        if len(parts) < 4:
            raise ValueError("Formato 'cuotas' inválido. Faltan argumentos. Uso: cuotas N MontoTotal Descripcion [con Categoria]")

        try:
            num_installments = int(parts[1])
            total_amount_str = parts[2].replace(',', '.')
            total_amount = float(total_amount_str)
        except ValueError:
            raise ValueError("Formato 'cuotas' inválido. Número de cuotas o monto total no son números válidos.")

        remaining_text = parts[3].strip()
        description = "Indefinido"
        category = "Otros" # Nota: Capitalización consistente
        separator = " con "

        if separator in remaining_text:
            desc_part, _, cat_part = remaining_text.partition(separator)
            cleaned_desc = desc_part.strip()
            cleaned_cat = cat_part.strip().title() # Capitalizar categoría
            if cleaned_desc: description = cleaned_desc
            if cleaned_cat: category = cleaned_cat
        else:
             cleaned_desc = remaining_text.strip()
             if cleaned_desc: description = cleaned_desc


        return {'action': 'add_installments', 'data': {
            'num_installments': num_installments,
            'total_amount': total_amount,
            'description': description,
            'category': category
        }}

    # Si no es un comando, intentar parsear como gasto único
    try:
        first_space_index = message_body.find(' ')
        if first_space_index == -1:
            amount_str = message_body.replace(',', '.')
            remaining_text = ""
        else:
            amount_str = message_body[:first_space_index].replace(',', '.')
            remaining_text = message_body[first_space_index:].strip()

        amount = float(amount_str)

        description = "Indefinido"
        category = "Otros"
        separator = " con "

        if remaining_text:
            if separator in remaining_text:
                desc_part, _, cat_part = remaining_text.partition(separator)
                cleaned_desc = desc_part.strip()
                cleaned_cat = cat_part.strip().title()
                if cleaned_desc: description = cleaned_desc
                if cleaned_cat: category = cleaned_cat
            else:
                 cleaned_desc = remaining_text.strip()
                 if cleaned_desc: description = cleaned_desc

        return {'action': 'add_single', 'data': {
            'amount': amount,
            'description': description,
            'category': category
        }}

    except ValueError:
        raise ValueError("Formato de mensaje inválido. No es un comando reconocido ni un gasto válido (Ej: 150.50 Descripción [con Categoria]). Asegúrate que el monto esté al inicio y sea un número.")
    except IndexError:
         raise ValueError("Formato de mensaje inválido. Posiblemente falte el monto.")
