# Proyecto-Simulacion-Incendio-Forestal

1. El endpoint /api/simulations/{id}/step/ usa POST en lugar de GET, aunque podría parecer que solo “lee” el siguiente estado. Explica por qué POST es la elección  correcta según la semántica HTTP. ¿Qué propiedad de GET se viola si lo  implementaras con ese método?
   
He utilizado POST porque es el método adecuado para operaciones que mutan el estado del servidor. En mi código, cada vez que se llama a este endpoint, la cuadrícula avanza, el contador de pasos aumenta y se actualiza la base de datos. Según el estándar HTTP, el método GET debe ser "seguro" y no tener efectos secundarios. Si hubiera usado GET, la simulación avanzaría accidentalmente con solo refrescar el navegador o por la acción de un bot de búsqueda, violando la semántica del protocolo y la integridad de los datos. Al usar POST, garantizo que cada paso sea una acción intencionada.

2. En este proyecto el estado de la cuadrícula vive en el servidor. Sin embargo, en la 
simulación original de Veritasium corre íntegramente en el navegador. ¿dónde 
debería vivir el estado y por qué? No hay una única respuesta correcta; lo que se 
evalúa es la calidad del razonamiento.
   
No creo que haya una sola respuesta, pero yo he decidido que el estado resida en el servidor principalmente para cumplir con los requisitos de persistencia y trazabilidad del enunciado. Al gestionar el estado mediante un UUID e historiales en la base de datos, permitimos que la sesión no dependa del ciclo de vida del navegador, evitando que los datos se pierdan al cerrar la pestaña. Además, esta arquitectura centralizada facilita la concurrencia, permitiendo que varios clientes consulten la misma simulación en tiempo real. Aunque una implementación en el cliente (como en Veritasium) ofrecería menor latencia y mayor fluidez visual, el enfoque en el servidor es el estándar cuando el objetivo es garantizar la integridad de los datos, el análisis científico y el almacenamiento de resultados a largo plazo.

5. ¿Qué pasa con el tamaño de incendios si varías $p$ y $f$?Al experimentar con los parámetros, he observado un comportamiento de auto-organización crítica. Si aumentamos la probabilidad de crecimiento $p$ manteniendo fija la de ignición $f$, el bosque se vuelve muy denso y los incendios se propagan por clústeres gigantescos. Por otro lado, si mantenemos el cociente $p/f$ constante pero aumentamos ambos valores, la densidad media se mantiene parecida, pero la frecuencia de rayos aumenta; esto hace que los incendios ocurran más a menudo pero sean más pequeños, ya que no le damos tiempo al bosque a regenerar grandes parches de combustible.

6. ¿Dónde valido el parámetro size?
He decidido validarlo en el Serializer. Me parece el lugar más adecuado porque permite capturar errores de rango (como un tamaño menor a 20 o mayor a 200) antes de que la petición llegue siquiera a la lógica de negocio o a la base de datos. Esto garantiza una respuesta 400 Bad Request inmediata y limpia. Hacerlo en la vista ensuciaría el código con condicionales manuales, y hacerlo en el modelo sería demasiado tarde en el flujo de la aplicación, dificultando el envío de mensajes de error claros al usuario.

7. ¿Por qué uv y pyproject.toml en vez de requirements.txt?
He optado por esta herramienta moderna porque pip freeze genera un archivo requirements.txt muy desordenado, donde se mezclan las librerías que yo quiero con todas sus dependencias internas. Con pyproject.toml, el archivo es legible y solo declaro mis dependencias directas (Django, NumPy, etc.). Además, el archivo uv.lock asegura que cualquier persona que descargue el proyecto instale exactamente las mismas versiones que yo, y uv hace todo este proceso de instalación y resolución de conflictos muchísimo más rápido que el pip tradicional.
