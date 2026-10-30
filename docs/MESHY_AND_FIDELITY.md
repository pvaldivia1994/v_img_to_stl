# Investigación de Meshy y nueva prueba de fidelidad

Fecha: 28 de octubre de 2026. Prioridad indicada por el usuario: parecido con la referencia, especialmente las flores. No usar Blender como parte de la solución ni exigir edición manual. El usuario acepta tiempos largos y pidió iniciar la generación para revisarla cuando termine.

## Qué documenta Meshy

La API oficial consultada identifica Meshy 7.1 como modelo actual. Distingue geometría de texturas y ofrece pasadas geométricas Ultra de 2048³/4096³ para una imagen; la entrada de varias imágenes admite 2048³. Recomienda desactivar remesh para conservar la máxima calidad y permite desactivar el procesamiento de estilo de la imagen. `texture_prompt` guía la textura; no es una instrucción directa sobre los pétalos de la malla.

Fuentes: [Image to 3D API](https://docs.meshy.ai/en/api/image-to-3d), [Multi-Image to 3D API](https://docs.meshy.ai/en/api/multi-image-to-3d).

Su guía recomienda referencias limpias y coherentes, con escala y encuadre similares. Se debe revisar la malla sin color para juzgar geometría destinada a impresión. Los modos de pocos polígonos se orientan a otros usos.

Fuente: [guía oficial de Image to 3D](https://help.meshy.ai/en/articles/9996860-how-to-use-meshy-image-to-3d).

Estas fuentes describen el servicio y sus parámetros. No permiten reproducir su entrenamiento, pesos o pasada Ultra usando Hunyuan3D. No se presenta nuestro modo local como equivalente a Meshy ni se contrataron servicios o créditos externos.

## Qué cambiamos localmente

1. Perfil «Máximo detalle · experimental»: 50 pasos, CFG 7.5, volumen 512 y consultas por lotes de 4000. Los perfiles anteriores quedan disponibles.
2. Se conservan los 3072 latentes del flujo validado. Aumentar ese número sin un modelo entrenado para ello no garantiza mayor fidelidad.
3. Nuevo nodo `FormaVAEDecodeHunyuan3D`: evalúa el mismo campo denso, enviando consultas por lotes a la GPU y conservando resultados en RAM. Evita mantener toda la cuadrícula y sus resultados intermedios simultáneamente en VRAM. No cambia los pesos ni inventa detalle.
4. El nodo informa el número real de lotes completados. También se reciben los pasos reales del muestreo y los cambios de etapa del motor.
5. Referencias frontal/trasera con márgenes reducidos al 3% por lado, sin repintar pétalos ni deformar proporciones. Preparación y hashes en `data/fidelity-fox/preparation.json`. Se conserva la referencia anterior.
6. Se conserva toda la malla; no se aplica reducción de polígonos ni eliminación automática de componentes pequeños. La revisión posterior decidirá qué hacer con fragmentos.

El volumen 512 tiene aproximadamente 2.37 veces tantos puntos como el volumen 384. Esto mejora la capacidad de extracción, pero puede definir con más precisión una flor incorrectamente interpretada. El límite también depende del codificador visual y del modelo de forma; más tiempo no garantiza semejanza exacta.

## Seguimiento visible

La página muestra seis etapas: preparación, carga/lectura de vistas, forma, detalle de superficie, construcción de malla y guardado. El porcentaje corresponde exclusivamente a la etapa activa; no se muestra como porcentaje del tiempo total. Una etapa sin medición usa barra indeterminada.

El tiempo transcurrido continúa al volver a abrir el proyecto. Cerrar el navegador no cancela el trabajo. La aplicación reconecta el seguimiento si el canal de eventos se corta; los resultados se comprueban por el historial del motor. No hay una hora de finalización garantizada.

## Validación antes de generar

- 27 pruebas automatizadas superadas, incluidas separación de trabajos, progreso por etapas, eventos tardíos y configuración del perfil máximo.
- Verificación numérica independiente del decodificador por lotes en float16/float32: orden de coordenadas, ejes, varios elementos de lote y conteo de avance.
- Compilación de la interfaz correcta.

La calidad artística de esta nueva prueba queda pendiente de su ejecución y revisión. No marcar las flores como resueltas antes de comparar la malla resultante con la imagen.

## Generación iniciada

- Proyecto: `599857e4d066414392c1461eba532eda`, nombre «Zorro-flores-maximo-detalle».
- Frente y espalda preparados en `data/fidelity-fox`, sin volver a eliminar el fondo.
- Semilla 4007959359; perfil `maximum`. El flujo completo se conserva en `project.json`.
- Identificador del motor: `c94279fc-9394-41b9-b34e-96bd32ae9f70`.
- Página local: http://127.0.0.1:8000/?project=599857e4d066414392c1461eba532eda
- En la red actual: http://10.0.0.83:8000/?project=599857e4d066414392c1461eba532eda

Se verificó el avance real del muestreo en la API y en la interfaz. El trabajo queda ejecutándose; el usuario indicará cuándo terminó para revisar flores y parecido. No se programa un aviso externo ni se requiere mantener este chat activo para que la aplicación continúe.
