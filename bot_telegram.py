from telegram import Update
from telegram.ext import Updater, CommandHandler, CallbackContext
import requests
import locale

TOKEN = "TU_TOKEN_AQUÍ"
API_URL = "https://restaurants-gpt.onrender.com/buscar"

def detectar_idioma(update: Update) -> str:
    idioma_usuario = update.effective_user.language_code
    return idioma_usuario if idioma_usuario in ["es", "en", "fr", "it", "de"] else "es"

def start(update: Update, context: CallbackContext) -> None:
    lang = detectar_idioma(update)
    if lang == "es":
        mensaje = (
            "¡Hola! Soy Alma Gourmet, tu bot de búsqueda del top restaurantes 🍽️ según Google Maps\n"
            "Usa el comando:\n"
            "/buscar <tipo_comida> en <ciudad>\n"
            "Ejemplo: /buscar ramen en Madrid"
        )
    elif lang == "en":
        mensaje = (
            "Hi! I'm Alma Gourmet, your restaurant-finder bot 🍽️ powered by Google Maps reviews\n"
            "Use the command:\n"
            "/buscar <type_of_food> en <city>\n"
            "Example: /buscar ramen en Madrid"
        )
    else:
        mensaje = "¡Hola! Este bot te ayuda a encontrar restaurantes según las mejores reseñas en Google Maps."

    update.message.reply_text(mensaje)

def buscar(update: Update, context: CallbackContext) -> None:
    lang = detectar_idioma(update)
    consulta = ' '.join(context.args)
    if ' en ' not in consulta:
        msg = "Formato incorrecto. Usa: /buscar pizza en Valencia" if lang == "es" else "Wrong format. Use: /buscar pizza en Valencia"
        update.message.reply_text(msg)
        return

    tipo_comida, lugar = consulta.split(' en ')
    params = {
        'lugar': lugar.strip(),
        'tipo_comida': tipo_comida.strip(),
        'min_reviews': 1500,
        'min_puntuacion': 4.0
    }

    response = requests.get(API_URL, params=params)
    if response.status_code == 200:
        data = response.json()
        resultados = sorted(data.get('resultados', []), key=lambda x: x.get('reseñas', 0), reverse=True)

        if resultados:
            mensaje = ""
            for restaurante in resultados[:5]:
                nombre = restaurante.get('nombre')
                direccion = restaurante.get('direccion')
                puntuacion = restaurante.get('puntuacion')
                reseñas = restaurante.get('reseñas')
                tipo = tipo_comida.capitalize()
                maps_url = restaurante.get('google_maps')

                # Usar una bandera genérica (puedes hacer lógica para cambiarla si quieres por país)
                mensaje += (
                    f"🇮🇹 *{nombre}*\n"
                    f"📍 {direccion}\n"
                    f"⭐ ~{puntuacion} | 📝 +{reseñas:,} reseñas\n"
                    f"🍝 Tipo de comida: {tipo}\n"
                    f"🔗 [Enlace a Google Maps]({maps_url})\n\n"
                )
            update.message.reply_text(mensaje, parse_mode='Markdown')
        else:
            msg = "No encontré resultados con esos criterios 😕" if lang == "es" else "No results found with those filters 😕"
            update.message.reply_text(msg)
    else:
        msg = "Error al consultar la API 😔" if lang == "es" else "There was an error contacting the API 😔"
        update.message.reply_text(msg)

def main():
    updater = Updater(TOKEN)
    dp = updater.dispatcher
    dp.add_handler(CommandHandler("start", start))
    dp.add_handler(CommandHandler("buscar", buscar))
    updater.start_polling()
    updater.idle()

if __name__ == '__main__':
    main()
