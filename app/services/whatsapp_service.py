# app/services/whatsapp_service.py
import requests
from flask import current_app # Accede a la app actual y su config
import logging
from app.utils.helpers import format_phone_number # Importa tu helper
logger = logging.getLogger(__name__)

def send_whatsapp_message(phone_number, message):
    """Envía un mensaje de texto a través de la API de WhatsApp."""
    whatsapp_token = current_app.config.get('WHATSAPP_TOKEN')
    api_url = current_app.config.get('WHATSAPP_API_URL')

    if not whatsapp_token or not api_url:
        logger.error("WHATSAPP_TOKEN o WHATSAPP_API_URL no configurados. No se puede enviar mensaje.")
        return {"error": "Configuración de WhatsApp incompleta en el servidor."}

    formatted_number = format_phone_number(phone_number)#"54111541964489"

    headers = {
        "Authorization": f"Bearer {whatsapp_token}",
        "Content-Type": "application/json"
    }
    payload = {
        "messaging_product": "whatsapp",
        "to": formatted_number,
        "type": "text",
        "text": {"body": message}
    }
    logger.info(f"Enviando mensaje a {formatted_number}. Payload: {payload}")

    try:
        response = requests.post(api_url, json=payload, headers=headers)
        response.raise_for_status() # Lanza excepción para errores HTTP (4xx o 5xx)
        logger.info(f"Respuesta de WhatsApp API: {response.status_code} - {response.text}")
        return response.json()
    except requests.exceptions.RequestException as e:
        error_message = f"Error de red/HTTP al enviar mensaje a WhatsApp: {e}"
        status_code = e.response.status_code if e.response is not None else 'N/A'
        error_text = e.response.text if e.response is not None else 'N/A'
        logger.error(error_message)
        logger.error(f"Código de estado: {status_code}, Texto de error: {error_text}")
        return {"error": error_message, "status_code": status_code, "details": error_text}
    except Exception as e:
        logger.exception(f"Error desconocido al enviar mensaje de WhatsApp: {e}")
        return {"error": f"Error desconocido en el servidor: {str(e)}"}