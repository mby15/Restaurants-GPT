import logging
import requests
import os
import re
import spacy
from spacy.matcher import Matcher
from langdetect import detect  # Esta importación podrías eliminarla si no la usas
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

logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    level=logging.INFO
)

# -------------------------------
# Configuración de spaCy para español
# -------------------------------
# Asegúrate de haber ejecutado:
#   python -m spacy download es_core_news_sm
nlp_es = spacy.load("es_core_news_sm")

def parse_query(query: str) -> dict:
    """
    Procesa la consulta y extrae:
      - acción: "comer", "cenar", etc.
      - calificador: "mejores", "populares", "típicos", "recomendados"
      - tipo: la categoría o tipo de comida
      - localizacion: la ciudad, barrio o punto de interés

    Se utiliza una combinación de expresiones regulares y análisis con spaCy.
    """
    resultado = {
        "accion": None,
        "calificador": None,
        "tipo": None,
        "localizacion": None
    }
    
    query_low = query.lower().strip()

    # Patrones para identificar la estructura de la frase
    patrones = [
        # Patrón: "dónde comer/cenar <tipo> en <localizacion>"
        r"(?:dónde\s+)?(?P<accion>comer|cenar)\s+(?P<tipo>.+?)\s+(?:en|cerca de|con vistas a)\s+(?P<localizacion>.+)",
        # Patrón: "<calificador> restaurantes <opcionalmente tipo> en <localizacion>"
        r"(?P<calificador>mejores|populares|típicos|recomendados)\s+restaurantes(?:\s+(?P<tipo>[\w\s]+?))?\s+en\s+(?P<localizacion>.+)",
        # Patrón: "restaurantes <tipo> <localizacion>"
        r"(?:restaurantes|lugares)\s+(?:de\s+)?(?P<tipo>[\w\s]+?)\s+(?:recomendados|para\s+comer)?\s*(?:en|cerca de|con vistas a)\s+(?P<localizacion>.+)",
        # Patrón simple: "<tipo> en <localizacion>"
        r"(?P<tipo>[\w\s]+)\s+(?:en|cerca de|con vistas a)\s+(?P<localizacion>.+)",
        # Patrón sin preposición: "pizza valencia"
        r"^(?P<tipo>[\w\s]+)\s+(?P<localizacion>[\w\s]+)$"
    ]
    
    for patron in patrones:
        match = re.search(patron, query_low)
        if match:
            grupos = match.groupdict()
            # Determina la acción
            if grupos.get("accion"):
                resultado["accion"] = grupos["accion"].strip()
            else:
                if "cenar" in query_low:
                    resultado["accion"] = "cenar"
                elif "comer" in query_low:
                    resultado["accion"] = "comer"
                else:
                    resultado["accion"] = "buscar"
            # Calificador
            if grupos.get("calificador"):
                resultado["calificador"] = grupos["calificador"].strip()
            # Tipo
            if grupos.get("tipo"):
                resultado["tipo"] = grupos["tipo"].strip()
            # Localización
            if grupos.get("localizacion"):
                resultado["localizacion"] = grupos["localizacion"].strip()
            break

    # Si la extracción con regex no fue suficiente, se recurre a spaCy (NER)
    if not resultado["localizacion"] or not resultado["tipo"]:
        doc = nlp_es(query)
        # Buscar entidades que puedan ser localidades
        for ent in doc.ents:
            if ent.label_ in ["LOC", "GPE", "FACILITY"] and not resultado["localizacion"]:
                resultado["localizacion"] = ent.text
        # Extraer sustantivos como posible 'tipo'
        if not resultado["tipo"]:
            candidatos = [token.text for token in doc if token.pos_ == "NOUN"]
            if candidatos:
                resultado["tipo"] = " ".join(candidatos[:2])
    return resultado

# Número de resultados a mostrar por bloque (10 en este caso)
RESULTADOS_POR_BLOQUE = 10

async def enviar_siguiente_bloque(update: Update, context: ContextTypes.DEFAULT_TYPE, tipo_comida: str):
    """
    Envía el siguiente bloque de resultados y, si quedan más, informa al usuario
    que puede ampliar la lista usando /continuar.
    """
    resultados = context.user_data.get('resultados', [])
    indice = context.user_data.get('indice', 0)
    mensaje_acumulado = ""
    
    for restaurante in resultados[indice: indice + RESULTADOS_POR_BLOQUE]:
        nombre = restaurante.get('nombre')
        direccion = restaurante.get('direccion')
        puntuacion = restaurante.get('puntuacion')
        reseñas = restaurante.get('reseñas')
        tipo = tipo_comida.capitalize()
        maps_url = restaurante.get('google_maps')
        mensaje_acumulado += (
            f"*{nombre}*\n"
            f"📍 {direccion}\n"
            f"⭐ ~{puntuacion} | 📝 +{reseñas:,} reseñas\n"
            f"🍝 Tipo de comida: {tipo}\n"
            f"🔗 [Enlace a Google Maps]({maps_url})\n\n"
        )
    
    # Actualiza el índice para el próximo bloque
    context.user_data['indice'] = indice + RESULTADOS_POR_BLOQUE
    await update.message.reply_text(mensaje_acumulado, parse_mode='Markdown')

    if context.user_data['indice'] < len(resultados):
        # Notifica al usuario que escriba /continuar para ver más resultados
        await update.message.reply_text("Si deseas ampliar la lista de resultados de esta búsqueda, escribe /continuar.")
    else:
        # Se limpian los datos de paginación cuando ya no quedan resultados
        context.user_data.pop('resultados', None)
        context.user_data.pop('indice', None)

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """
    Envía un mensaje de bienvenida en español.
    """
    logging.info("Comando /start recibido")
    mensaje = (
        "¡Hola! Soy Alma Gourmet, tu bot de búsqueda de los mejores restaurantes 🍽️ según Google Maps\n"
        "Usa el comando:\n"
        "/buscar <tipo_comida> en <ciudad>\n"
        "Ejemplo: /buscar ramen en Madrid\n"
        "Si no incluyes 'en', también intentaré adivinar lo que necesitas.\n"
        "¡Disfruta!"
    )
    await update.message.reply_text(mensaje)

async def buscar(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """
    Procesa el comando /buscar, extrae el tipo de comida y la localización,
    y realiza la búsqueda en la API correspondiente.
    """
    consulta = ' '.join(context.args)
    if not consulta:
        msg = "Por favor, incluye una consulta. Ejemplo: /buscar paella en Valencia"
        await update.message.reply_text(msg)
        return

    datos = parse_query(consulta)
    tipo_comida = datos.get("tipo")
    lugar = datos.get("localizacion")

    if not tipo_comida or not lugar:
        msg = ("No entendí bien tu consulta. Asegúrate de escribir algo como: /buscar pizza en Valencia.\n"
               "También puedes intentar /buscar pizza valencia.")
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
        resultados = sorted(
            data.get('resultados', []),
            key=lambda x: x.get('reseñas', 0),
            reverse=True
        )
        if resultados:
            # Guarda los resultados y el índice en context.user_data para continuar
            context.user_data['resultados'] = resultados
            context.user_data['indice'] = 0
            await enviar_siguiente_bloque(update, context, tipo_comida)
        else:
            msg = "No encontré resultados con esos criterios 😕"
            await update.message.reply_text(msg)
    except Exception as e:
        logging.error(f"Error al consultar la API: {e}")
        msg = "Error al consultar la API 😔"
        await update.message.reply_text(msg)

async def continuar(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """
    Envía el siguiente bloque de resultados, si existe una búsqueda previa.
    """
    if 'resultados' in context.user_data and 'indice' in context.user_data:
        # Se asume que el tipo de comida es consistente en todos los resultados.
        primeros_resultados = context.user_data.get('resultados', [])
        if primeros_resultados:
            # Si has almacenado explícitamente 'tipo_comida' en la búsqueda, úsalo.
            # De lo contrario, se asume que el primer resultado contiene la clave 'tipo_comida'.
            tipo_comida = primeros_resultados[0].get('tipo_comida', "Comida")
        else:
            tipo_comida = ""
        await enviar_siguiente_bloque(update, context, tipo_comida)
    else:
        await update.message.reply_text("No hay búsqueda previa. Usa /buscar para iniciar una búsqueda.")

async def friendly_chat(update: Update, context: ContextTypes.DEFAULT_TYPE):
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
    await update.message.reply_text(mensaje)

async def main():
    app = ApplicationBuilder().token(TOKEN).build()
    # Registra los handlers
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("buscar", buscar))
    app.add_handler(CommandHandler("continuar", continuar))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, friendly_chat))
    # Ejecuta el bot en modo polling
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
