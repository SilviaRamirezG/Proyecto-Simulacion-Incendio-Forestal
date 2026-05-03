# Proyecto-Simulacion-Incendio-Forestal

 <~~~ Preguntas de reflexión ~~~>

Pregunta 1.-

El endpoint /api/simulations/{id}/step/ usa POST en lugar de GET, aunque podría parecer que solo “lee” el siguiente estado. Explica por qué POST es la elección  correcta según la semántica HTTP. ¿Qué propiedad de GET se viola si lo  implementaras con ese método?

Respuesta 1.-
   
He utilizado POST porque es el método adecuado para operaciones que mutan el estado del servidor. En mi código, cada vez que se llama a este endpoint, la cuadrícula avanza, el contador de pasos aumenta y se actualiza la base de datos. Según el estándar HTTP, el método GET debe ser "seguro" y no tener efectos secundarios.

Si hubiera usado GET, la simulación avanzaría accidentalmente con solo refrescar el navegador o por la acción de un bot de búsqueda, violando la semántica del protocolo y la integridad de los datos. Al usar POST, garantizo que cada paso sea una acción intencionada.

Pregunta 2.-

En este proyecto el estado de la cuadrícula vive en el servidor. Sin embargo, en la 
simulación original de Veritasium corre íntegramente en el navegador. ¿dónde 
debería vivir el estado y por qué? No hay una única respuesta correcta; lo que se 
evalúa es la calidad del razonamiento.

Respuesta 2.-

No existe una única respuesta correcta, pero he optado por mantener el estado en el servidor por una cuestión de persistencia y coherencia de los datos. Mientras que la simulación de Veritasium prioriza la fluidez y baja latencia ejecutándose en el cliente, nuestro proyecto requiere el uso de UUID e historiales, lo que obliga a que el estado sea persistente.

Al residir en el servidor, permitimos que la simulación sea compartible entre distintos dispositivos y que los datos no se pierdan al cerrar el navegador. En definitiva, si buscamos una herramienta de análisis científico y almacenamiento a largo plazo, el servidor es el lugar adecuado; si buscamos una experiencia visual interactiva a 60 FPS, el cliente sería superior.

Pregunta 3.-

¿Qué ocurre con el tamaño medio de los incendios si aumentas p manteniendo f 
constante? ¿Y si mantienes constante el cociente p/f pero aumentas ambos valores 
proporcionalmente? Ejecuta la simulación con distintos valores y razona tu respuesta
con los datos observados

Respuesta 3.-

Al experimentar con la simulación, he observado que el tamaño de los incendios depende de la densidad de "combustible" acumulado.
Si aumentamos p con f constante, los incendios son mucho más grandes.

Al crecer árboles más rápido, se forman parches densos y conectados (clústeres); cuando cae un rayo, el fuego se propaga sin interrupciones por áreas gigantescas. Por el contrario, si aumentamos p y f proporcionalmente, el tamaño medio disminuye. Aunque el bosque crece igual, la mayor frecuencia de rayos "limpia" el combustible constantemente, impidiendo que los árboles se conecten en grandes masas. El resultado son incendios frecuentes pero pequeños y fragmentados.

Pregunta 4.-

El parámetro size que se pasa al crear la simulación debe ser un entero entre 20 y 
200. ¿Dónde validaste este valor en tu implementación y por qué elegiste ese lugar?
Describe al menos dos lugares alternativos donde podrías haberlo validado y qué 
implicaciones tendría cada opción.

Respuesta 4.-

He validado el parámetro size en el Serializer, ya que en la arquitectura de Django REST Framework es el lugar óptimo para gestionar la integridad de la entrada. Hacerlo aquí permite interceptar errores de rango antes de que la petición llegue a la lógica de negocio, devolviendo automáticamente un 400 Bad Request limpio y estandarizado.

Como alternativas, podría haberlo validado en la Vista, lo cual permitiría un control más dinámico pero ensuciaría el código con condicionales manuales, o en el Modelo, que garantiza la integridad a nivel de base de datos pero lanza el error demasiado tarde (en el .save()), complicando la gestión de la respuesta y empeorando la experiencia del usuario. Por ello, el Serializer ofrece el equilibrio perfecto entre seguridad y limpieza.

Pregunta 5.-

El proyecto se gestiona con uv y pyproject.toml. ¿Qué ventaja tiene este enfoque 
frente a un requirements.txt generado con pip freeze? Explica la diferencia entre 
dependencias directas y transitivas y cómo las trata cada herramienta.

Respuesta 5.-

He optado por uv y pyproject.toml porque ofrecen una gestión más limpia y profesional que pip freeze. La ventaja principal es la distinción entre tipos de dependencias: en el pyproject.toml solo declaro las dependencias directas (como Django o NumPy), manteniendo el archivo legible y fácil de mantener.

A diferencia de pip freeze, que genera un requirements.txt plano con todas las librerías mezcladas, uv gestiona las dependencias transitivas (las que necesitan mis librerías para funcionar) de forma aislada en el archivo uv.lock. Esto garantiza que cualquier usuario instale exactamente las mismas versiones, asegurando una reproducibilidad total y una resolución de conflictos mucho más rápida y eficiente.
