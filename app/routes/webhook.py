# app/routes/webhook.py
from flask import request, jsonify, current_app, make_response
from . import webhook_bp # Importa el blueprint desde el __init__.py del directorio
from app.services import whatsapp_service, expense_service # Importa los servicios
import logging
import traceback # Para logging de errores detallado

# logger = logging.getLogger(__name__) # Comentado, usaremos el logger de la app Flask
# Es mejor usar el logger de la aplicación Flask para que se integre
# con la configuración de logging de Flask. Se accede vía current_app.logger

@webhook_bp.route('', methods=['GET']) # El prefijo '/webhook' ya está en el Blueprint
def verify_webhook():
    """Verifica el token del webhook de WhatsApp."""
    verify_token = current_app.config.get('WHATSAPP_VERIFY_TOKEN')
    mode = request.args.get("hub.mode")
    token = request.args.get("hub.verify_token")
    challenge = request.args.get("hub.challenge")

    # Usar el logger de Flask
    current_app.logger.info(f"GET /webhook - Mode: {mode}, Token recibido: {token}, Challenge: {challenge}")

    if mode and token:
        if mode == "subscribe" and token == verify_token:
            current_app.logger.info("Webhook verificado exitosamente.")
            # Devolver solo el challenge con status 200
            response = make_response(challenge, 200)
            response.mimetype = "text/plain" # Asegurar el tipo correcto
            return response
        else:
            current_app.logger.warning(f"Verificación fallida: Token no coincide (Esperado: {verify_token}, Recibido: {token})")
            return jsonify({"status": "error", "message": "Verification token mismatch"}), 403
    else:
        current_app.logger.warning("Solicitud GET /webhook inválida: Faltan 'hub.mode' o 'hub.verify_token'.")
        return jsonify({"status": "error", "message": "Missing parameters"}), 400


@webhook_bp.route('', methods=['POST'])
def handle_webhook():
    """Maneja los mensajes entrantes de WhatsApp."""
    data = request.json
    # Usar el logger de Flask para consistencia
    current_app.logger.debug(f"POST /webhook - Datos recibidos (completo): {data}") # Log completo en DEBUG

    # Estructura esperada de la API de WhatsApp Business Cloud
    if data and data.get("object") == "whatsapp_business_account":
        try:
            # --- Bloque para procesar la estructura del webhook ---
            entry = data.get("entry", [])[0]
            changes = entry.get("changes", [])
            if not changes:
                 current_app.logger.info("No hay 'changes' en la entrada, ignorando.")
                 return jsonify({"status": "success", "message": "No changes found"}), 200

            change = changes[0]
            value = change.get("value", {})
            messages = value.get("messages", [])
            
            if not messages:
                 # Podría ser una actualización de estado, etc.
                 current_app.logger.info("No hay 'messages' en el payload, ignorando.")
                 return jsonify({"status": "success", "message": "Not a user message"}), 200

            message_data = messages[0] # Tomamos el primer mensaje

            if message_data and message_data.get("type") == "text":
                phone_number_from = message_data.get("from") # Número del remitente
                message_body = message_data.get("text", {}).get("body", "").strip()
                current_app.logger.info(f"Mensaje de texto recibido de {phone_number_from}: '{message_body}'")

                if not message_body:
                    current_app.logger.info("Mensaje vacío recibido, ignorando.")
                    # No es necesario enviar respuesta a WhatsApp por mensaje vacío
                    return jsonify({"status": "success", "message": "Empty message ignored"}), 200

                # --- Bloque para procesar el comando del usuario ---
                try:
                    parsed_command = expense_service.parse_expense_message(message_body)
                    action = parsed_command['action']
                    action_data = parsed_command['data']
                    response_message = "" # Inicializar mensaje de respuesta

                    current_app.logger.info(f"Ejecutando acción: {action} para {phone_number_from} con datos: {action_data}")

                    # Ejecutar la acción correspondiente usando los servicios
                    if action == 'report':
                        # Asume que generate_expense_report puede manejar None para fechas
                        # Si necesitaras pasar fechas, las parsearías aquí o ajustarías el parser
                        report = expense_service.generate_expense_report(detailed=action_data['detailed'])
                        response_message = report

                    elif action == 'delete_last':
                        deleted_info = expense_service.delete_last_expense()
                        if deleted_info:
                            response_message = (
                                f"🗑️ Último registro eliminado:\n"
                                f"  ID: {deleted_info['id']}\n"
                                f"  Fecha: {deleted_info['expense_date'].strftime('%d/%m/%Y')}\n"
                                f"  Monto: ${deleted_info['amount']:.2f}\n"
                                f"  Desc: '{deleted_info['description']}' ({deleted_info['category']})"
                            )
                        else:
                            response_message = "ℹ️ No hay registros para borrar."

                    elif action == 'add_installments':
                        created_expenses = expense_service.record_installments(**action_data)
                        # Es más seguro verificar si la lista no está vacía antes de acceder a [0]
                        if created_expenses:
                            first_expense = created_expenses[0]
                            response_message = (
                                f"✅ Registradas {action_data['num_installments']} cuotas de ${first_expense.amount:.2f} cada una.\n"
                                f"  Total: ${action_data['total_amount']:.2f}\n"
                                f"  Desc: '{action_data['description']}'\n"
                                f"  Cat: {action_data['category']}\n"
                                f"  1er Venc: {first_expense.expense_date.strftime('%d/%m/%Y')}"
                            )
                        else:
                             # Esto no debería pasar si record_installments funciona bien, pero por si acaso
                             current_app.logger.error("record_installments devolvió una lista vacía inesperadamente.")
                             response_message = "❌ Error inesperado al registrar cuotas (lista vacía)."


                    elif action == 'add_single':
                        new_expense = expense_service.record_single_expense(**action_data)
                        response_message = (
                            f"✅ Gasto registrado:\n"
                            f"  Monto: ${new_expense.amount:.2f}\n"
                            f"  Desc: '{new_expense.description}'\n"
                            f"  Cat: {new_expense.category}\n"
                            f"  Fecha: {new_expense.expense_date.strftime('%d/%m/%Y')}"
                        )

                    # Enviar respuesta a WhatsApp SÓLO si se generó un mensaje
                    if response_message:
                        whatsapp_service.send_whatsapp_message(phone_number_from, response_message)
                    else:
                        # Si una acción válida no produjo respuesta (raro, pero posible)
                         current_app.logger.warning(f"No se generó mensaje de respuesta para la acción '{action}' de {phone_number_from}.")


                # *** MANEJO DE ERRORES ESPECÍFICOS DEL PROCESAMIENTO DEL COMANDO ***
                except ValueError as ve: # Error de parseo o validación de datos (ej. formato número/fecha incorrecto)
                    # Log como warning porque es un error del usuario, no del sistema
                    current_app.logger.warning(f"Error de formato/valor en mensaje de {phone_number_from}: '{message_body}'. Error: {ve}")
                    # Enviar mensaje útil al usuario
                    error_response = (
                        f"⚠️ ¡Ups! Hubo un problema con tu mensaje: *{str(ve)}*\n\n"
                        "Formatos comunes:\n"
                        "• `[monto] [descripción] [con categoría]`\n"
                        "  _(Ej: `150.50 Café con amigos con Salidas`)_\n"
                        "• `cuotas [N] [total] [descripción] [con categoría]`\n"
                        "  _(Ej: `cuotas 3 6000 Curso online con Educación`)_\n"
                        "• `reporte` o `reporte detallado`\n"
                        "• `borrar`"
                    )
                    try:
                        whatsapp_service.send_whatsapp_message(phone_number_from, error_response)
                    except Exception as send_error:
                        current_app.logger.error(f"¡Fallo al enviar mensaje de error (ValueError) a {phone_number_from}! Error de envío: {send_error}")

                except Exception as e: # Otros errores inesperados durante la ejecución (DB, lógica interna, etc.)
                    # Log como EXCEPTION para incluir el traceback completo
                    current_app.logger.exception(f"Error INESPERADO procesando el comando '{message_body}' de {phone_number_from}. Error: {e}")
                    # traceback.print_exc() # logger.exception ya incluye el traceback si está configurado correctamente

                    # Enviar mensaje genérico al usuario
                    error_response = f"❌ Ocurrió un error inesperado ({type(e).__name__}) al procesar tu solicitud. El administrador ha sido notificado."
                    try:
                        whatsapp_service.send_whatsapp_message(phone_number_from, error_response)
                    except Exception as send_error:
                        current_app.logger.error(f"¡Fallo al enviar mensaje de error (Exception) a {phone_number_from}! Error de envío: {send_error}")

            else:
                # Manejar otros tipos de mensajes si es necesario (imágenes, audio, etc.)
                msg_type = message_data.get('type', 'desconocido') if message_data else 'desconocido'
                current_app.logger.info(f"Mensaje recibido de {phone_number_from} no es de tipo 'text', ignorando. Tipo: {msg_type}")

        # *** MANEJO DE ERRORES EN LA ESTRUCTURA DEL WEBHOOK (fuera del procesamiento del comando) ***
        except IndexError:
             current_app.logger.warning("Estructura de datos inesperada en el webhook (IndexError). ¿Cambió el formato de la API?", exc_info=True) # Log con traceback
        except KeyError as ke:
             current_app.logger.warning(f"Estructura de datos inesperada en el webhook (KeyError: {ke}). ¿Cambió el formato de la API?", exc_info=True) # Log con traceback
        except Exception as e:
             # Error muy general, probablemente al intentar acceder a datos del webhook
             current_app.logger.exception(f"Error general al procesar la estructura del webhook POST: {e}")
             # No enviar mensaje de error a WhatsApp aquí, ya que podría no haber un 'from' o ser un problema de la plataforma

    # Siempre devolver 200 OK a la API de WhatsApp para evitar reintentos
    # independientemente de si pudimos procesar el mensaje o no.
    return jsonify({"status": "success"}), 200