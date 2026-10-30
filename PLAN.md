# Plan del proyecto: imagen a STL con ComfyUI

Estado: primera versión funcional implementada y validada con generación real. Pendientes revisión del usuario y preparación específica de impresión.

## Objetivo

Crear una aplicación local que reciba una imagen, genere una malla 3D mediante ComfyUI, permita revisar y ajustar su tamaño, y guarde un STL junto con la imagen y los parámetros de generación.

Recorrido: imagen → preparación → ComfyUI → malla GLB → revisión y ajustes → STL.

## Equipo y restricciones

Datos comprobados el 28 de octubre de 2026:

- GPU NVIDIA RTX 3050 con 8 GB de VRAM.
- Aproximadamente 64 GB de RAM.
- Aproximadamente 52 GB libres en C:; volver a comprobar antes de descargar.
- Windows.
- Motor inicial propuesto: Hunyuan3D 2.0 para geometría, sujeto a validación real en este equipo.
- Descargar inicialmente una sola variante. Evaluar mini si el flujo estándar no resulta viable.
- Presupuesto provisional de espacio: 25–35 GB; confirmar tamaños antes de instalar.

## Alcance de la primera versión

- Carga de PNG/JPG y revisión del encuadre y fondo.
- Generación de una figura por trabajo con un perfil compatible con la GPU.
- Progreso, mensajes de error e historial de trabajos.
- Visor 3D con giro y zoom.
- Ajuste de orientación y altura en milímetros.
- Análisis de malla e intentos de reparación sencilla, conservando el original.
- Exportación STL y conservación del GLB y de los parámetros.
- Funcionamiento local y conexión a ComfyUI limitada al equipo por defecto.

Fuera del alcance inicial: generación desde texto, múltiples vistas, texturas, lotes, edición escultórica, generación de soportes y publicación en Internet.

## Organización de archivos

| Ruta | Uso |
|---|---|
| `C:\_IA\downloads` | Instaladores y descargas |
| `C:\_IA\ComfyUI` | Motor y entorno Python; adaptar la estructura si el paquete portable incorpora una carpeta contenedora |
| `C:\_IA\models` | Modelos compartidos, referenciados desde ComfyUI |
| `C:\_IA\cache` | Cachés de modelos y descargas |
| `C:\_Github\v_img_to_stl` | Código, documentación, configuración y flujos |
| `C:\_Github\v_img_to_stl\data\projects` | Entradas y resultados por proyecto |

Excluir de Git entornos, modelos, cachés y resultados generados. Versionar el flujo, la configuración de ejemplo y las versiones de dependencias. No modificar `C:\_IA\_llama_models`.

## Arquitectura propuesta

- Interfaz web local con React y Three.js.
- Servicio Python con FastAPI para conexión a ComfyUI y procesamiento de mallas.
- API local de ComfyUI para subir imágenes, enviar trabajos, seguir ejecución y recoger resultados.
- Almacenamiento por proyecto con archivos y metadatos, sin base de datos inicialmente.
- Un trabajo de generación activo a la vez para limitar el consumo de memoria.
- Definir explícitamente la escala al exportar: STL no incorpora una unidad física inequívoca.

## Etapas y lista de tareas

### 1. Preparación

- [x] Revisar las instrucciones del proyecto antes de implementar.
- [x] Inventariar ComfyUI, Python, Git, Blender y laminadores existentes.
- [x] Volver a comprobar espacio y disponibilidad de GPU.
- [x] Seleccionar una distribución de ComfyUI y versiones compatibles.
- [x] Elegir el flujo de geometría y un único modelo inicial.
- [x] Registrar fuentes oficiales, licencia, tamaños y destinos de descarga.
- [x] Configurar las rutas de modelos y caché para mantenerlas en `C:\_IA`.
- [x] Preparar exclusiones de Git antes de añadir archivos grandes.

Criterio de salida: manifiesto de instalación concreto y compatible con el espacio disponible.

### 2. Instalación del motor

- [x] Crear las carpetas necesarias sin alterar instalaciones ajenas.
- [x] Descargar e instalar ComfyUI y su entorno en `C:\_IA`.
- [x] Instalar las dependencias de GPU compatibles con ese entorno.
- [x] Descargar el modelo elegido y el flujo oficial correspondiente.
- [x] Configurar el acceso a modelos compartidos.
- [x] Verificar que ComfyUI detecta y utiliza la RTX 3050.
- [x] Verificar la API local y registrar las versiones efectivas.
- [x] Documentar cómo iniciar y detener el motor.

Criterio de salida: ComfyUI arranca sin errores relevantes y puede cargar el flujo.

### 3. Primera generación, antes de construir la interfaz

- [x] Usar como primera entrada `Zorro Durmiente en Luna Creciente.png`.
- [x] Evaluar fondo, encuadre y necesidad de recorte o eliminación de fondo.
- [x] Instalar una herramienta de eliminación de fondo solo si la prueba la necesita.
- [x] Ejecutar el flujo con parámetros conservadores.
- [x] Registrar tiempo, consumo máximo de VRAM cuando sea medible y posibles errores.
- [x] Ajustar resolución y gestión de memoria si resulta necesario.
- [ ] Evaluar la variante mini si no se obtiene un resultado viable.
- [x] Guardar el GLB, la imagen utilizada, el flujo y sus parámetros.
- [ ] Revisar visualmente el resultado con el usuario.

Criterio de salida: primera malla obtenida y calidad evaluada antes de ampliar el desarrollo.

### 4. Primer STL y revisión de impresión

- [x] Elegir e instalar las bibliotecas de procesamiento de mallas necesarias.
- [x] Conservar la malla original antes de cualquier reparación.
- [x] Analizar caras degeneradas, normales, bordes abiertos y componentes separados.
- [x] Aplicar reparaciones sencillas y registrar qué se modificó.
- [x] Definir orientación y dimensiones en milímetros.
- [x] Exportar STL y comprobar que puede volver a abrirse.
- [x] Inspeccionar las uniones del zorro con la luna, orejas, flores y elementos delgados.
- [ ] Abrir el STL en un laminador y revisar escala, errores y vista de capas.
- [x] Registrar defectos que requieran edición manual.

Criterio de salida: STL revisado, con limitaciones conocidas. Exportar correctamente no equivale a garantizar una impresión correcta.

### 5. Aplicación local

- [x] Crear la estructura del servicio y de la interfaz.
- [x] Implementar configuración de rutas y dirección local de ComfyUI.
- [x] Implementar comprobación de conexión y disponibilidad del flujo/modelo.
- [x] Implementar carga y validación de imágenes.
- [x] Implementar envío de trabajos e identificación inequívoca de sus resultados.
- [x] Implementar seguimiento de progreso y errores, incluyendo falta de memoria y desconexión.
- [x] Implementar visor de la malla.
- [x] Implementar ajustes de orientación y tamaño.
- [x] Integrar análisis, reparación básica y exportación STL.
- [x] Guardar imagen, original, STL, parámetros y estado por proyecto.
- [x] Implementar historial y repetición de una generación.
- [x] Evitar sobrescribir resultados existentes accidentalmente.

Criterio de salida: completar el recorrido desde la interfaz sin operar manualmente el flujo de ComfyUI.

### 6. Verificación y entrega

- [x] Verificar el recorrido completo con la imagen inicial.
- [x] Verificar recuperación ante motor desconectado, imagen inválida y generación fallida.
- [x] Verificar orientación y escala del STL exportado.
- [x] Comprobar que dependencias, modelos y cachés respetan las rutas acordadas.
- [x] Documentar instalación, arranque, uso, errores habituales y versiones.
- [x] Registrar tiempos observados y perfiles de calidad realmente probados.
- [ ] Revisar con el usuario la primera versión y priorizar mejoras.

## Descargas previstas

| Componente | Condición |
|---|---|
| ComfyUI para Windows y entorno Python | Necesario; seleccionar distribución compatible |
| PyTorch y dependencias NVIDIA | Según el entorno elegido; evitar instalaciones duplicadas |
| Un modelo Hunyuan3D 2.0 de geometría | Necesario; concretar variante y archivo antes de descargar |
| Flujo oficial | Necesario; guardar también su versión para API |
| Eliminación de fondo | Solo si la entrada lo requiere |
| Bibliotecas de mallas | Necesarias para conversión y validación |
| Blender | Si no está disponible y hace falta inspección o corrección manual |
| Laminador | Reutilizar uno instalado o elegirlo según la impresora |
| Dependencias de FastAPI, React y Three.js | Al construir la aplicación |

No descargar modelos de texturas para el alcance inicial. No instalar un CUDA Toolkit separado salvo que una dependencia concreta lo exija.

## Cuándo se necesita intervención del usuario

Se avisará en el chat al llegar a cada punto necesario; las tareas independientes podrán continuar.

- **Acceso o intervención del sistema:** si aparece un inicio de sesión, aceptación personal de términos, reinicio o acción que solo el usuario pueda completar.
- **Calidad del primer modelo:** decidir si la semejanza y la interpretación de la parte trasera son aceptables.
- **Datos de impresión:** indicar tipo de impresora, material, laminador y altura deseada antes de evaluar espesores y preparación para impresión.
- **Cambios artísticos o estructurales:** elegir ante modificaciones visibles como engrosar flores, unir piezas o agregar una base.
- **Bloqueo de recursos:** decidir si falta espacio, si hay que borrar archivos ajenos al proyecto o si la solución exige una compra o servicio externo. No borrar esos archivos automáticamente.
- **Prueba física:** realizar la impresión, si se quiere validar resistencia y resultado real; no es requisito para completar la aplicación.

## Límites y riesgos conocidos

- Una sola imagen no determina la geometría oculta; el modelo la interpreta.
- Los requisitos publicados de VRAM son orientativos; validar el flujo completo en esta GPU.
- La RAM del sistema no garantiza que un modelo que exceda la VRAM pueda ejecutarse satisfactoriamente.
- La reparación automática no resuelve toda geometría defectuosa ni garantiza espesores imprimibles.
- La licencia del software y la de los pesos deben revisarse para el uso previsto.
- Mantener la primera generación como hito previo a invertir en la interfaz completa.

## Referencias

- ComfyUI, flujos Hunyuan3D: https://docs.comfy.org/tutorials/3d/hunyuan3D-2
- Hunyuan3D 2.0, proyecto oficial: https://github.com/Tencent-Hunyuan/Hunyuan3D-2
- ComfyUI, ejemplo de API y seguimiento: https://github.com/Comfy-Org/ComfyUI/blob/master/script_examples/websockets_api_example.py

## Registro de avances

### Refinamiento de calidad solicitado por el usuario

- [x] Sustituir la eliminación de fondo ligera por U2Net completo y revisar el contorno de la luna.
- [x] Añadir opciones «Prueba rápida» y «Más detalle», conservando el perfil en cada proyecto.
- [x] Comparar una generación de mayor resolución con la prueba anterior usando la misma semilla.
- [x] Comprobar cierre de malla, detalles y fragmentos del nuevo resultado.
- [x] Presentar la nueva versión al usuario para revisión.


- 2026-10-28: plan y lista de tareas creados. Hardware y espacio inicial revisados. Pendientes la selección exacta del flujo y todas las instalaciones.


- 2026-10-28: ComfyUI portable v0.43.0 y Hunyuan3D 2.0 instalados y verificados. Aplicación local implementada. Se corrigieron CFG y extracción de superficie; PrusaSlicer confirmó un STL cerrado de 100 mm. 14 pruebas automatizadas superadas. Ver docs/VALIDATION.md. Pendientes valoración visual del usuario, decisión sobre detalles finos/componentes pequeños y datos de impresión.
- La variante mini no fue necesaria: el modelo estándar funcionó en esta GPU. La revisión de capas permanece pendiente; se realizó inspección del STL por la consola de PrusaSlicer.



- 2026-10-28: refinamiento de calidad completado con U2Net y perfil de mayor detalle. Nueva generación en 253.4 s; STL limpio con una pieza cerrada, verificado por PrusaSlicer. Se conservan los originales y vistas de comparación. 16 pruebas superadas. Ver docs/QUALITY.md. La validación artística por el usuario y la preparación de impresión siguen pendientes.


- 2026-10-28: investigación de alternativas para flores y espalda completada. Se recomienda una prueba separada con Hunyuan3D-2mv y, si hace falta, flores modeladas en Blender. Se revisaron también TripoSG, Hunyuan3D 2.1, TRELLIS.2 y Hi3D. La comparación local de umbrales no resolvió el problema visual; se conserva el perfil vigente. Fuentes y siguientes tareas en docs/QUALITY_RESEARCH.md.

### Próxima fase: fidelidad de varias vistas

- [x] Revisar las vistas de la lámina y preparar frente/espalda; reservar los laterales de menor resolución.
- [x] Preparar y verificar el modelo Hunyuan3D-2mv en C:\_IA.
- [x] Crear un flujo separado y comparar la reconstrucción de la espalda.
- [x] Añadir entradas de varias vistas, conservación y repetición a la aplicación.
- [ ] Revisar con el usuario la versión multivista de mayor detalle.
- [x] Descartar la propuesta de modelar flores en Blender: el usuario prefiere mejorar la generación automática.

### Fidelidad sin edición manual (petición vigente)

- [x] Investigar las opciones documentadas de Meshy y distinguir geometría de textura.
- [x] Añadir un perfil de máximo detalle sin reducir polígonos.
- [x] Añadir avance real por etapas, pasos/lotes y tiempo transcurrido a la interfaz.
- [x] Preparar referencias con menos margen y conservar la imagen y proporciones.
- [x] Iniciar la nueva generación y comprobar que el seguimiento funciona en el trabajo real.
- [ ] Revisar el parecido de las flores cuando el usuario indique que terminó.
- La propuesta anterior de usar Blender queda descartada por preferencia expresa del usuario. Esta fase no utiliza Blender.

### Comparación de mayor capacidad: flores y patitas

- [x] Revisar requisitos oficiales y compatibilidad nativa de Hunyuan3D 2.1.
- [x] Integrar selector de modelo, restricciones de vistas y conservación del modelo al repetir.
- [x] Verificar configuración nativa, entradas y compilación (31 pruebas superadas).
- [x] Descargar y verificar el checkpoint 2.1 en C:\_IA.
- [x] Completar la generación 2.1 en la GPU de 8 GB: 675.3 s sin errores, hasta 7307 MiB observados por muestreo.
- [ ] Revisar flores, patitas y espalda frente a la versión multivista anterior.
- [x] Investigar grafos nativos, VisualBruno, Kijai y Hunyuan3D + UltraShape. Hallazgos y secuencia propuesta en docs/WORKFLOWS_HUNYUAN21.md.
- [x] Comparar el nivel de extracción y el encuadre de entrada antes de aumentar resolución.
- [x] Instalar y validar la ejecución de UltraShape en un entorno separado y en la GPU de 8 GB; prueba corta completa, sin valoración artística.
- [x] Implementar la comparación de semillas, 75 pasos y refinamiento posterior con volumen 768, sin reducir caras ni fragmentos.
- [ ] Completar el lote largo y revisar las flores, las patitas y la espalda con el usuario.
- [x] Dejar el lote largo ejecutándose y comprobar el avance del primer trabajo: `3342ae7c46184f73b3168a05a57b7779`. Las demás variantes y UltraShape se ejecutan después en secuencia.
- [ ] Preparar el STL de la variante elegida y comprobar sus espesores para la impresora indicada por el usuario.
- DMC: sin wheel compatible ni compilador C++ configurado; se conserva Lewiner. FlashVDM aproximado no sustituye el refinamiento aprendido. Estado y pruebas en docs/FLOWER_REFINEMENT.md.

### Preparación por IA y dorso en la malla base

### Nueva figura: lobito poligonal, luna y flores

- [x] Crear una referencia frontal nueva y una vista posterior con el generador integrado de imágenes, conservando imágenes y prompts.
- [x] Corregir el dorso tras la observación del usuario: la cola está delante y no debe aparecer duplicada por detrás. Frente conservado sin cambios en `data/polygonal-wolf-v2`.
- [x] Detener realmente el intento con el dorso incorrecto y reiniciar con las referencias corregidas: proyecto `f965df99c83b4a84b3936a978911011d`, experimento `cd009267570e4444896fe5e5e81b9e7e`. Avance comprobado: 7/50 pasos de generación base.
- [x] Preparar la ejecución de una única variante nueva con refinamiento automático y los ajustes aprobados; 56 pruebas superadas. Prompts en docs/POLYGONAL_WOLF_PROMPTS.md.
- [x] Completar Hunyuan multivista (574,7 s) y UltraShape (5721,0 s); salida final `067996cb019e4b1bb083698b841111ba`.
- [ ] Recibir la valoración visual del lobito: estilo poligonal, flores y coherencia del dorso.

### Registro de la figura anterior

- [x] Añadir botones Detener y Regenerar para Hunyuan y UltraShape, con cancelación del cálculo real y de pasos pendientes, historial conservado y 55 pruebas superadas. Ver docs/GENERATION_CONTROLS.md.

- [x] Corregir el bloqueo de escritura de avance en Windows y añadir reanudación sin repetir mallas base; 45 pruebas superadas. Ver docs/FILE_LOCK_RECOVERY.md.
- [x] Completar las variantes refinadas original/IA. La variante IA regenerada `6dd7d7413b1c4fdbbed159505530d82d` fue aceptada visualmente por el usuario el 2026-10-29; el intento previo se conservó cancelado.

- [x] Revisar el estado real: UltraShape largo seguía trabajando; las variantes Hunyuan ya estaban terminadas.
- [x] Identificar la lámina completa en el proyecto manual y añadir separación de esta referencia conocida en navegador/API, protegiendo imágenes desconocidas.
- [x] Investigar límites del encoder, UltraShape, Hunyuan multivista, TripoSG, TRELLIS y Omni con fuentes oficiales.
- [x] Preparar frente y dorso de prueba con edición IA, conservar originales, prompts y alfa limpio.
- [x] Conservar el dorso en refinamientos y distinguir imagen directa del refinador de las vistas usadas en su malla base.
- [x] Implementar CFG secuencial y corrección de semilla del muestreador; 40 pruebas y comprobación numérica superadas.
- [x] Programar la comparación original/IA con frente y dorso tras el trabajo activo: experimento `2b9670edb19547deac01fe9b46b720a0`.
- [x] Validar 32768 latentes en GPU y completar las variantes refinadas original/IA a 50 pasos y resolución 512.
- [x] Recibir la aceptación visual de la variante con referencias IA por parte del usuario. Configuración conservada en docs/APPROVED_REFERENCE.md; la validación de espesores de impresión permanece pendiente.
- 2026-10-28: checkpoint de 7,365,943,290 bytes verificado por SHA256. Comparación 2.1 iniciada en `9cdb7cf5b3a54d93b5f13ca5456b0cfc` sin reiniciar servicios, mediante el ejecutor de experimentos. El motor confirmó la carga dinámica de Hunyuan3Dv2_1 y comenzó el muestreo sin error de memoria. El selector de la API actualizada requiere el próximo arranque normal; la página actual ya muestra este experimento y su avance.
- 2026-10-28: investigación de Meshy documentada en docs/MESHY_AND_FIDELITY.md. Perfil máximo y seguimiento real implementados; 27 pruebas y validación numérica del decodificador superadas. Trabajo `599857e4d066414392c1461eba532eda` iniciado como «Zorro-flores-maximo-detalle», con las dos vistas, semilla 4007959359 y volumen 512. Se deja ejecutando para que el usuario avise al terminar; el resultado artístico sigue pendiente.

- 2026-10-28: modelo multivista descargado y verificado; frente y espalda separados y preparados. Primera prueba real completada en 88.6 s sin error de memoria, con una espalda más próxima a la referencia y pétalos más reconocibles. Aplicación ampliada y 23 pruebas superadas. Resultados y límites en docs/MULTIVIEW.md. La revisión artística sigue pendiente.
- 2026-10-28: versión multivista de mayor detalle completada en 232.7 s, con hasta 6549 MiB observados por muestreo. STL limpio a 100 mm: una pieza cerrada, confirmado por PrusaSlicer. La espalda mejoró claramente; las flores aún requieren valoración artística. Se conservaron entradas, originales y vistas frontal/trasera para revisión.


### Preparación para GitHub — 2026-10-30

- [x] Crear AGENTS.md, README vigente y skill local de referencias 3D.
- [x] Documentar descargas, hashes, tres entornos Python, GPU/RAM, instalación en otra PC, historia y respaldo.
- [x] Publicar en el árbol de código referencias seleccionadas y preset transferible; conservar pesos y resultados completos fuera de Git.
- [x] Corregir dependencias de data local para la ejecución con preset y el registro de compatibilidad UltraShape en equipos nuevos; 59 pruebas superadas y frontend compilado.
- Destino solicitado: https://github.com/pvaldivia1994/v_img_to_stl.git, rama main.
- [ ] Comprobar la instalación GPU completa físicamente en otra PC; la validación del código no sustituye esa prueba.
