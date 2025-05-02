# app/utils/helpers.py
import logging

logger = logging.getLogger(__name__)

def format_phone_number(phone):
    """
    Formatea el número de teléfono para la API de WhatsApp.
    ¡¡¡IMPORTANTE: Esta lógica necesita ser revisada para un caso real!!!
    Actualmente devuelve un número fijo para pruebas.
    Debería validar y limpiar el número (ej: quitar '+', asegurar código país).
    """
    logger.warning(f"Formateando número {phone}. La lógica actual devuelve un valor fijo.")
    # Lógica real de formateo aquí. Ejemplo muy básico:
    # if phone and phone.startswith('+'):
    #     return phone[1:] # Quita el '+' inicial si existe
    # elif phone and len(phone) == 13 and phone.startswith('549'): # Ejemplo Argentina Móvil
    #     return '54' + phone[3:] # Quita el 9 después del código de país
    # return phone # Devuelve original si no coincide

    # --- LÓGICA TEMPORAL DE PRUEBA ---
    fixed_test_number = "54111541964489" # Reemplaza con tu número de prueba si es necesario
    logger.info(f"Devolviendo número de prueba fijo: {fixed_test_number}")
    return fixed_test_number
    # --- FIN LÓGICA TEMPORAL ---