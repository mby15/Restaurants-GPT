import requests

# Función para consultar la API de restaurantes
def buscar_restaurantes(lugar="Valencia", tipo_comida=None, abierto_ahora=False, precio=None, min_puntuacion=4.0, min_reviews=1500):
    # La URL de tu API en Render
    url = f"https://restaurants-gpt.onrender.com/buscar?lugar={lugar}&tipo_comida={tipo_comida}&abierto_ahora={abierto_ahora}&precio={precio}&min_puntuacion={min_puntuacion}&min_reviews={min_reviews}"
    
    print(f"Consultando la URL: {url}")  # Verifica la URL
    
    # Realiza la solicitud GET a la API
    response = requests.get(url)
    
    print(f"Estado de la respuesta: {response.status_code}")  # Muestra el estado de la respuesta
    
    # Si la solicitud es exitosa, devuelve los datos en formato JSON
    if response.status_code == 200:
        print("Datos obtenidos con éxito")
        return response.json()
    else:
        print("Error al obtener los datos")
        return {"error": "No se pudieron obtener los datos"}

#Ejemplo consulta
#resultados = buscar_restaurantes(
    lugar="Valencia", 
    tipo_comida="pizza", 
    abierto_ahora=False,  # Puedes omitir esto o ponerlo como False
    precio="$$",  # Rango de precio intermedio
    min_puntuacion=4.0, 
    min_reviews=100  # Bajando un poco el número de reseñas requeridas
#)
#print(resultados)
