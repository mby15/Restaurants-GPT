# Restaurants-GPT

**Restaurants-GPT** es un proyecto que permite a los usuarios buscar restaurantes en diferentes ubicaciones, basándose en sus preferencias de tipo de comida, puntuación, número de reseñas y rango de precios. El proyecto está basado en un asistente GPT que interactúa con la **API de Google Maps** para proporcionar recomendaciones precisas y relevantes, además de incluir enlaces a Google Maps para facilitar la localización de los restaurantes.

## Objetivo

El objetivo de **Restaurants-GPT** es ofrecer una forma sencilla y eficiente de encontrar restaurantes en cualquier lugar, permitiendo a los usuarios aplicar varios filtros a sus búsquedas. Estos filtros incluyen el tipo de comida, el rango de precios, la puntuación mínima y la cantidad de reseñas. La aplicación proporciona recomendaciones detalladas junto con enlaces directos a Google Maps, lo que facilita la localización de los restaurantes recomendados.

Este sistema puede ser útil para cualquier persona que desee encontrar restaurantes cercanos según sus preferencias, ya sea para explorar nuevas opciones de comida o para tomar decisiones informadas basadas en la calidad y popularidad de los lugares.

## Funcionalidades

- **Búsqueda de restaurantes:**  
  Los usuarios pueden buscar restaurantes por tipo de comida y ubicación. Esto les permite realizar búsquedas personalizadas según sus gustos y necesidades. Ejemplo: "pizzerías en Valencia" o "restaurantes mexicanos en Madrid".

- **Filtros avanzados:**  
  La aplicación permite aplicar filtros como:
  - **Puntuación mínima:** Los usuarios pueden seleccionar restaurantes que tengan al menos una cierta puntuación (por ejemplo, 4.0 estrellas).
  - **Número de reseñas:** Es posible filtrar restaurantes con un mínimo de reseñas, lo que ayuda a asegurar que los lugares sean populares y de calidad.
  - **Rango de precios:** Los usuarios también pueden filtrar restaurantes por rango de precios utilizando el sistema estándar de Google Maps (`$`, `$$`, `$$$`, `$$$$`).

- **Enlaces a Google Maps:**  
  Cada restaurante recomendado viene con un enlace directo a su ubicación en **Google Maps**, lo que permite a los usuarios abrir el mapa interactivo para obtener más detalles sobre cómo llegar, horarios de apertura y otros datos importantes.

## Pasos Seguidos

1. **Creación del repositorio y configuración inicial:**  
   Se creó un repositorio en **GitHub** llamado `Restaurants-GPT`, donde se subieron todos los archivos necesarios para el proyecto. Este repositorio se configuró para interactuar con **Render**, una plataforma para alojar aplicaciones web.

2. **Despliegue en Render:**  
   La aplicación fue desplegada en **Render**, lo que permite ejecutar el servidor de manera remota. Render está configurado para escuchar el repositorio de GitHub y actualizar automáticamente el servicio cuando se detectan cambios.

3. **Uso de la API de Google Maps:**  
   Se integró la **Google Places API** para realizar las búsquedas de restaurantes. Los parámetros de búsqueda se construyen de manera dinámica según los filtros proporcionados por el usuario (tipo de comida, ubicación, puntuación, etc.).

4. **Desarrollo del GPT:**  
   Un **GPT** fue configurado para interactuar con la API de Google y realizar las búsquedas. Este asistente se encarga de recibir las solicitudes del usuario, realizar la consulta a la API de restaurantes y devolver los resultados relevantes de forma estructurada. El GPT fue configurado con instrucciones claras para que pudiera gestionar las solicitudes adecuadamente.

5. **Integración con Google Maps y Render:**  
   Se configuró una acción dentro del GPT que interactúa con la API para obtener los resultados de los restaurantes. Además, se aseguraron de que los resultados incluyan los enlaces de Google Maps para cada restaurante, facilitando así la localización directa del lugar.

