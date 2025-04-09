import logging
import requests
from telegram import Update
from telegram.ext import ApplicationBuilder, CommandHandler, ContextTypes
import os
from dotenv import load_dotenv

load_dotenv(dotenv_path=".env")
  # Esto carga las variables definidas en el archivo .env

TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")
API_URL = "https://restaurants-gpt.onrender.com/buscar"

logging.basicConfig(format="%(asctime)s - %(name)s - %(levelname)s - %(message)s", level=logging.INFO)

def detectar_idioma(update: Update) -> str:
    idioma_usuario = update.effective_user.language_code
    return idioma_usuario if idioma_usuario in ["es", "en", "fr", "it", "de"] else "es"

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
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

    await update.message.reply_text(mensaje)

async def buscar(update: Update, context: ContextTypes.DEFAULT_TYPE):
    lang = detectar_idioma(update)
    consulta = ' '.join(context.args)

    if ' en ' not in consulta:
        msg = "Formato incorrecto. Usa: /buscar pizza en Valencia" if lang == "es" else "Wrong format. Use: /buscar pizza en Valencia"
        await update.message.reply_text(msg)
        return

    tipo_comida, lugar = consulta.split(' en ')
    params = {
        'lugar': lugar.strip(),
        'tipo_comida': tipo_comida.strip(),
        'min_reviews': 1500,
        'min_puntuacion': 4.0
    }

    try:
        response = requests.get(API_URL, params=params)
        response.raise_for_status()
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

                mensaje += (
                    f"🇮🇹 *{nombre}*\n"
                    f"📍 {direccion}\n"
                    f"⭐ ~{puntuacion} | 📝 +{reseñas:,} reseñas\n"
                    f"🍝 Tipo de comida: {tipo}\n"
                    f"🔗 [Enlace a Google Maps]({maps_url})\n\n"
                )
            await update.message.reply_text(mensaje, parse_mode='Markdown')
        else:
            msg = "No encontré resultados con esos criterios 😕" if lang == "es" else "No results found with those filters 😕"
            await update.message.reply_text(msg)

    except Exception as e:
        logging.error(f"Error al consultar la API: {e}")
        msg = "Error al consultar la API 😔" if lang == "es" else "There was an error contacting the API 😔"
        await update.message.reply_text(msg)

async def main():
    app = ApplicationBuilder().token(TOKEN).build()
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("buscar", buscar))
    await app.run_polling()

if __name__ == '__main__':
    import asyncio

    try:
        loop = asyncio.get_running_loop()
    except RuntimeError:
        loop = None

    if loop and loop.is_running():
        print("⚠️ Ya hay un bucle corriendo. Ejecuta `await main()` si estás en un notebook o cambia de entorno.")
    else:
        asyncio.run(main())
