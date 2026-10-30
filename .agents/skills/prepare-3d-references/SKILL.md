---
name: prepare-3d-references
description: Preparar o generar imágenes coherentes de frente y dorso para reconstrucción 3D en v_img_to_stl, preservando detalles y oclusiones antes de usar Hunyuan multivista y UltraShape. Usar para nuevas figuras o correcciones de sus referencias, no para imágenes decorativas sin destino 3D.
---

# Preparar referencias para imagen a STL

El objetivo es que las imágenes describan **una misma escultura física**, no
solo dos ilustraciones parecidas. Consultar `AGENTS.md` en la raíz del repositorio
y el preset `config/approved-generation.json` para el flujo vigente.

## Elegir el punto de partida

- Si existen fotografías fiables de frente y espalda, conservarlas como evidencia
  principal. Preparar fondo/encuadre sin inventar detalles salvo petición del usuario.
- Para un diseño nuevo, crear primero el frente y derivar el dorso **de ese
  frente**, usando la imagen como referencia de identidad. No generar dos diseños
  independientes por texto y tratarlos como vistas calibradas.
- En esta sesión se usó el generador integrado de imágenes de ChatGPT. No afirmar
  que esas imágenes salieron de ComfyUI o que el editor está instalado localmente.
  Usar el generador disponible y autorizado; no cambiar a una API de pago ni pedir
  claves si se dispone de la herramienta integrada. Si se utiliza la habilidad
  `imagegen`, seguir su modo y guardar los resultados en el proyecto.
- Antes de editar un archivo de imagen local con el generador, inspeccionarlo.
  Mantener los originales y crear una variante nueva por corrección.

## Frente legible para geometría

Pedir un único objeto, entero y aislado, con una sola vista por archivo:

- Cámara frontal casi ortográfica, perspectiva moderada y la figura sin recortes.
- Fondo transparente limpio o blanco uniforme; sin escenario, letras ni sombras
  proyectadas fuertes. Ocupación aproximada del 85 % y margen alrededor de puntas/base.
- Material mate y luz suave direccional suficiente para distinguir el relieve.
- Anatomía y apoyos claros. Identificar patas, orejas, cola y conexiones.
- Los detalles importantes deben ser **volumen visible**: pétalos separados y
  centros en relieve, no flores pintadas, textura o líneas dibujadas. El contraste
  de color puede ayudar a leerlos; el STL no conservará ese color.
- Para estilo poligonal: caras planas grandes e intencionales en cuerpo y adornos,
  contornos angulares y pétalos geométricos; evitar una rejilla triangular dibujada
  sobre una figura redondeada. Eso sería apariencia, no geometría reconstruible.

Adaptar el diseño al pedido. No imponer flores, una base, colores o una cantidad
fija de adornos a figuras que no los necesitan. En los ejemplos del proyecto se
usaron tres flores porque eran importantes para esa composición.

## Dorso con oclusiones correctas

Usar el frente como guía y pedir una cámara situada 180° detrás del **mismo** objeto.
Mantener postura, proporciones, grosor, base y posición física de los adornos.
La silueta lateral del objeto debe cambiar de lado como corresponde al punto de
vista: por ejemplo, el arco alto de la luna del frente izquierdo aparece a la
derecha al mirar desde atrás.

Describir lo que se ve y lo que queda oculto. El dorso muestra lomo, grupa y
parte posterior de orejas/cabeza; no debe enseñar una segunda cara o patas
delanteras atravesando el cuerpo. Los pétalos frontales pueden asomar por un
borde, pero sus centros no deben trasladarse mágicamente a la cara posterior.

**Precedente que hay que evitar:** el primer dorso del lobito inventó una cola
envolviendo la espalda cuando la única cola ya se veía por delante. La corrección
eliminó la cola trasera inventada, conservó el lomo/grupa y dejó la cola frontal
oculta por el cuerpo y la luna. No espejar la cola frontal sobre la espalda.
Una curva real de la luna tampoco debe confundirse con una cola para eliminarla.

## Revisar antes de gastar GPU

Inspeccionar frente y dorso juntos y comprobar:

1. Misma figura, dimensiones relativas, postura, base y grosor de luna/soportes.
2. Una sola anatomía coherente: sin extremidades, orejas, caras o colas duplicadas.
3. Adornos en la misma posición física, respetando qué caras son visibles.
4. Detalles prioritarios con siluetas y relieve distinguibles.
5. Una imagen por vista, encuadre comparable y fondo realmente limpio.

Si el dorso contradice el frente, corregir solo la vista incorrecta antes de
encolar. Si el usuario lo señala durante el cálculo, detener el intento mediante
la API del proyecto, corregir y crear otro intento. No cambiar imágenes de un
trabajo que ya las consumió ni usar el botón Regenerar esperando que edite su dorso.
La edición generativa no garantiza correspondencia geométrica exacta: no afirmar
que las vistas estén calibradas ni que el resultado final será idéntico.

## Guardar y utilizar

Crear una carpeta versionada con:

```text
front-raw.png / back-raw.png       originales generados, conservar localmente
front.png / back.png               entradas blancas listas para Hunyuan
front-conditioning.png             opcional RGBA para UltraShape
preparation.json                   origen, recortes, encuadre y hashes
```

`app.reference_preparation.prepare_ai_cutout` conserva RGB y suavidad del alfa,
limpia manchas aisladas y reencuadra. Está pensado para **una escultura conectada**:
retiene el componente alfa principal; no aplicarlo a piezas separadas intencionales.
Revisar visualmente el resultado para no perder flores o aberturas reales.
No volver a segmentar con U2Net una referencia ya limpia sin una razón observada.

Guardar los prompts completos y la relación entre imagen objetivo y guía de
identidad. Para publicar, copiar únicamente las referencias seleccionadas a
`assets/references/<nombre>` y mantener pesos/GLB/STL/experimentos en `data/`.

Con motores y pesos preparados, y sin otro trabajo GPU activo:

```powershell
.venv\Scripts\python.exe -u -m scripts.run_hybrid_fidelity --reference-directory RUTA_REFERENCIAS --name "Nombre del diseño"
```

El directorio necesita `front.png` y `back.png`. El ejecutor crea una base
Hunyuan-2mv y luego UltraShape con el preset aceptado. 2.1 no acepta dorso en este
flujo. UltraShape recibe frontal y malla; la espalda entra a través de esa malla.
Los textos usados para crear imágenes no se envían como prompt de geometría.
Verificar un ID de proyecto y progreso real antes de decir que quedó ejecutándose.

## Referencias de la sesión original

Resolver estos enlaces desde esta carpeta de skill:

- [Prompts de la figura aceptada](../../../docs/IMAGE_PREPARATION_PROMPTS.md).
- [Lobito y corrección del dorso](../../../docs/POLYGONAL_WOLF_PROMPTS.md).
- [Parámetros y GPU medidos](../../../docs/MODELS_AND_HARDWARE.md).
- Ejemplos preparados: `assets/references/approved-fox` y
  `assets/references/polygonal-wolf` desde la raíz del repositorio.

La aceptación visual de un ejemplo no sustituye revisar otra figura, ni valida
espesores o capas de impresión. No requiere Blender.
