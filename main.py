from fastapi import FastAPI, Query
from typing import Optional
import requests
import os
from dotenv import load_dotenv

# Carga las variables de entorno del archivo .env
load_dotenv(dotenv_path=".env")

# Ahora, la clave se carga desde la variable de entorno "GOOGLE_API_KEY"
API_KEY = os.getenv("GOOGLE_API_KEY")

app = FastAPI()

@app.get("/buscar")
def buscar_restaurantes(
    lugar: str = "Valencia",
    tipo_comida: Optional[str] = None,
    abierto_ahora: Optional[bool] = False,
    precio: Optional[str] = None,
    min_puntuacion: float = 4.0,
    min_reviews: int = 1550
):
    url = "https://maps.googleapis.com/maps/api/place/textsearch/json"

    query = "restaurante"
    if tipo_comida:
        query = f"{tipo_comida} {query}"
    query = f"{query} en {lugar}"

    params = {
        "query": query,
        "type": "restaurant",
        "key": API_KEY
    }

    if abierto_ahora:
        params["opennow"] = "true"
    if precio:
        precios = {"$": 0, "$$": 1, "$$$": 2, "$$$$": 3}
        if precio in precios:
            params["minprice"] = precios[precio]
            params["maxprice"] = precios[precio]

    response = requests.get(url, params=params)
    data = response.json()

    resultados_filtrados = []

    for lugar in data.get("results", []):
        nombre = lugar.get("name")
        direccion = lugar.get("formatted_address")
        rating = lugar.get("rating")
        reseñas = lugar.get("user_ratings_total")
        maps_url = f"https://www.google.com/maps/place/?q=place_id:{lugar.get('place_id')}"

        if rating and reseñas and float(rating) >= min_puntuacion and int(reseñas) >= min_reviews:
            resultados_filtrados.append({
                "nombre": nombre,
                "direccion": direccion,
                "puntuacion": rating,
                "reseñas": reseñas,
                "google_maps": maps_url
            })

    return {"resultados": resultados_filtrados}
