import logging
import requests
import os
import re
import spacy
from spacy.matcher import Matcher
from langdetect import detect
from telegram import Update
from telegram.ext import (
    ApplicationBuilder,
    CommandHandler,
    MessageHandler,
    ContextTypes,
    filters
)
from dotenv import load_dotenv

# Cargar el archivo .env
load_dotenv(dotenv_path=".env")

TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")
API_URL = "https://restaurants-gpt.onrender.com/buscar"

logging.basicConfig(format="%(asctime)s - %(name)s - %(levelname)s - %(message)s", level=logging.INFO)

# -------------------------------
# Funciones NLP para extraer la consulta
# -------------------------------

# Cargar modelos de spaCy
# Es importante haber descargado previamente los modelos:
#  python -m spacy download es_core_news_sm
#  python -m spacy download en_core_web_sm
nlp_es = spacy.load("es_core_news_sm")
nlp_en = spacy.load("en_core_web_sm")

def get_nlp_model(text: str):
    """
    Detecta el idioma del texto y retorna el modelo correspondiente.
    Por defecto, en caso de error, se asume español.
    """
    try:
        idioma = detect(text)
    except Exception as e:
        idioma = "es"
    if idioma.startswith("en"):
        return nlp_en, idioma
    else:
        return nlp_es, idioma

def parse_query(query: str) -> dict:
    """
    Procesa la consulta y extrae de ella:
      - acción: "comer", "cenar", etc.
      - calificador: "mejores", "populares", "típicos", "recomendados"
      - tipo: la categoría o tipo de comida
      - localizacion: la ciudad, barrio o punto de interés

    Se usa una combinación de expresiones regulares y análisis con spaCy.
    """
    resultado = {
        "accion": None,
        "calificador": None,
        "tipo": None,
        "localizacion": None
    }
    
    # Convertir a minúsculas para facilitar patrones
    query_low = query.lower().strip()

    # Primer paso: intento con expresiones regulares para patrones conocidos
    patrones = [
        # Patrón: "dónde comer/cenar <tipo> en <localizacion>" o "dónde cenar <tipo> en <lugar>"
        r"(?:dónde\s+)?(?P<accion>comer|cenar)\s+(?P<tipo>.+?)\s+(?:en|cerca de|con vistas a)\s+(?P<localizacion>.+)",
        # Patrón: "<calificador> restaurantes <opcionalmente tipo> en <localizacion>"
        r"(?P<calificador>mejores|populares|típicos|recomendados)\s+restaurantes(?:\s+(?P<tipo>[\w\s]+?))?\s+en\s+(?P<localizacion>.+)",
        # Patrón: "restaurantes (de)? <tipo> (recomendados) en/cerca de <localizacion>"
        r"(?:restaurantes|lugares)\s+(?:de\s+)?(?P<tipo>[\w\s]+?)\s+(?:recomendados|para\s+comer)?\s*(?:en|cerca de|con vistas a)\s+(?P<localizacion>.+)",
        # Patrón simple: "<tipo> en <localizacion>"
        r"(?P<tipo>[\w\s]+)\s+(?:en|cerca de|con vistas a)\s+(?P<localizacion>.+)"
    ]
    
    for patron in patrones:
        match = re.search(patron, query_low)
        if match:
            grupos = match.groupdict()
            if grupos.get("accion"):
                resultado["accion"] = grupos["accion"].strip()
            else:
                # Intenta inferir la acción a partir de palabras clave
                if "cenar" in query_low:
                    resultado["accion"] = "cenar"
                elif "comer" in query_low:
                    resultado["accion"] = "comer"
                else:
                    resultado["accion"] = "buscar"
            if grupos.get("calificador"):
                resultado["calificador"] = grupos["calificador"].strip()
            if grupos.get("tipo"):
                resultado["tipo"] = grupos["tipo"].strip()
            if grupos.get("localizacion"):
                resultado["localizacion"] = grupos["localizacion"].strip()
            break  # Si se encuentra un patrón coincidente, se sale del bucle.

    # Si la extracción con regex no fue suficiente, se recurre a spaCy (NER)
    if not resultado["localizacion"] or not resultado["tipo"]:
        nlp_model, _ = get_nlp_model(query)
        doc = nlp_model(query)
        for ent in doc.ents:
            if ent.label_ in ["LOC", "GPE", "FACILITY"]:
                if not resultado["localizacion"]:
                    resultado["localizacion"] = ent.text
        # Si aún falta el tipo, se pueden extraer sustantivos relevantes
        if not resultado["tipo"]:
            candidatos = [token.text for token in doc if token.pos_ == "NOUN"]
            if candidatos:
                resultado["tipo"] = " ".join(candidatos[:2])  # Se toma una combinación simple
    return resultado

# -------------------------------
# Funciones del bot de Telegram
# -------------------------------

def detectar_idioma(update: Update) -> str:
    idioma_usuario = update.effective_user.language_code
    return idioma_usuario if idioma_usuario in ["es", "en", "fr", "it", "de"] else "es"

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    logging.info("Comando /start recibido")
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
            "/buscar <type_of_food> in <city>\n"
            "Example: /buscar ramen in Madrid"
        )
    else:
        mensaje = "¡Hola! Este bot te ayuda a encontrar restaurantes según las mejores reseñas en Google Maps."
    await update.message.reply_text(mensaje)

async def buscar(update: Update, context: ContextTypes.DEFAULT_TYPE):
    lang = detectar_idioma(update)
    # Obtiene la consulta completa a partir de los argumentos
    consulta = ' '.join(context.args)
    if not consulta:
        msg = "Por favor, incluye una consulta. Ejemplo: /buscar paella en Valencia" if lang == "es" else "Please include a query. E.g., /buscar paella in Valencia"
        await update.message.reply_text(msg)
        return

    # Se procesa la consulta usando el modelo NLP
    datos = parse_query(consulta)
    tipo_comida = datos.get("tipo")
    lugar = datos.get("localizacion")
    if not tipo_comida or not lugar:
        msg = "No entendí bien tu consulta. Asegúrate de escribir algo como: /buscar pizza en Valencia" if lang == "es" else "I didn't understand your query. Please try /buscar pizza in Valencia"
        await update.message.reply_text(msg)
        return

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
                # Se utiliza el tipo de comida detectado, capitalizado.
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

# Handler para mensajes de texto sin comando (conversación amistosa)
async def friendly_chat(update: Update, context: ContextTypes.DEFAULT_TYPE):
    lang = detectar_idioma(update)
    if lang == "es":
        mensaje = (
            "¡Hola! Soy Alma, tu asistente personal para encontrar el restaurante perfecto. 😊\n"
            "¿Te ha pasado alguna vez que no sabes dónde ir a comer y te gustaría que alguien te diera las mejores opciones?\n"
            "Generalmente, comienzo buscando restaurantes en tu zona con una excelente reputación: al menos 1500 reseñas y una puntuación mínima de 4.0.\n\n"
            "Cuéntame:\n"
            "- ¿En qué ciudad o zona te gustaría buscar?\n"
            "- ¿Qué tipo de comida prefieres? (por ejemplo, pizza, sushi, comida vegana)\n"
            "- ¿Qué rango de precio buscas? ($: Económico, $$: Medio, $$$: Alto, $$$$: Gama alta)\n"
            "Si lo deseas, también puedo consultar si están abiertos en este momento.\n"
            "¡Estoy aquí para ayudarte a descubrir el mejor lugar para comer!"
        )
    elif lang == "en":
        mensaje = (
            "Hello! I'm Alma, your personal assistant for finding the perfect restaurant. 😊\n"
            "Have you ever found yourself not knowing where to eat and wished someone could provide you with the best options?\n"
            "Usually, I start by searching for restaurants in your area with an excellent reputation: at least 1500 reviews and a minimum rating of 4.0.\n\n"
            "Tell me:\n"
            "- Which city or area would you like to search in?\n"
            "- What type of food do you prefer? (for example, pizza, sushi, vegan food)\n"
            "- What price range suits you? ($: Budget, $$: Moderate, $$$: Expensive, $$$$: High-end)\n"
            "I can also check if they're currently open, if you'd like.\n"
            "I'm here to help you discover the best place to dine!"
        )
    else:
        mensaje = "Hi! I'm Alma, your restaurant assistant."
    await update.message.reply_text(mensaje)

async def main():
    app = ApplicationBuilder().token(TOKEN).build()
    # Handlers de comandos
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("buscar", buscar))
    # Handler para mensajes de texto (sin comando)
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, friendly_chat))
    # Ejecuta el polling; evita cerrar el event loop automáticamente
    await app.run_polling(close_loop=False)

if __name__ == '__main__':
    import asyncio
    try:
        loop = asyncio.get_running_loop()
    except RuntimeError:
        loop = None
    if loop and loop.is_running():
        print("⚠️ Ya hay un bucle corriendo. Ejecuta 'await main()' si estás en un notebook o cambia de entorno.")
    else:
        asyncio.run(main())