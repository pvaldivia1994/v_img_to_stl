# Investigación: flores y parte trasera

Fecha de revisión: 28 de octubre de 2026.

**Estado posterior:** la prueba multivista ya se completó, seguida por la prueba de máximo detalle a resolución 512. El usuario ha descartado la edición en Blender. La siguiente comparación autorizada es el flujo nativo de Hunyuan3D 2.1; ver [HUNYUAN21.md](HUNYUAN21.md). Los apartados siguientes conservan el análisis inicial y sus propuestas históricas.

## Conclusión

Sí existen opciones razonables para mejorar el resultado. La siguiente prueba recomendada es reconstruir con varias vistas mediante Hunyuan3D-2mv. Para pétalos fieles y con grosor controlado, el camino de mayor control es un flujo híbrido: reconstrucción de la figura y modelado separado de las flores en Blender.

Esta recomendación distingue lo documentado por los proyectos, lo comprobado en esta máquina y las hipótesis pendientes. No se ha probado todavía el modelo multivista ni se han descargado sus pesos durante esta investigación.

## Lo que limita el resultado actual

- La entrada usada en la generación contiene una sola vista. El modelo completa la espalda según lo aprendido; no recibe la referencia trasera que existe en la lámina original. Es una explicación probable de la diferencia visual, no un diagnóstico medido de cada defecto.
- La resolución mayor conserva más detalle de la forma generada, pero no aporta una observación de la espalda ni impone el diseño exacto de cada pétalo. Las pruebas previas ya muestran que una malla cerrada puede seguir siendo poco fiel al diseño.
- Las flores pequeñas y superpuestas son un punto delicado. Separarlas en objetos modelados permite elegir contorno, curvatura, grosor y unión. Esta es una propuesta de trabajo artístico y de preparación física, no una capacidad automática garantizada del modelo.
- Las vistas de la lámina deben revisarse antes de combinarlas. No se ha demostrado que sean proyecciones perfectamente coherentes del mismo objeto; si difieren en flores, ramas, base o perspectiva, podrían introducir conflictos.

## Opciones revisadas

### 1. Hunyuan3D-2mv: primera prueba recomendada

Tencent publica un modelo específico para generación controlada por varias vistas. Su ejemplo admite imágenes etiquetadas como frontal, izquierda y trasera. ComfyUI dispone de un flujo nativo con entradas frontal, izquierda, trasera y derecha; las vistas son opcionales. Por tanto, nuestra aplicación puede ampliarse sin cambiar de motor.

El archivo FP16 publicado ocupa aproximadamente 4.93 GB. La compatibilidad del flujo completo con esta RTX 3050 de 8 GB debe medirse: el tamaño del archivo no equivale al consumo de VRAM. Usar descarga a RAM y bloques de decodificación pequeños es una estrategia a evaluar, no una garantía.

Fuentes: [modelo oficial de Tencent](https://huggingface.co/tencent/Hunyuan3D-2mv), [archivo FP16](https://huggingface.co/tencent/Hunyuan3D-2mv/blob/main/hunyuan3d-dit-v2-mv/model.fp16.safetensors), [documentación de ComfyUI](https://docs.comfy.org/tutorials/3d/hunyuan3D-2).

### 2. Flores modeladas por separado

Propuesta: generar zorro, luna y base, y sustituir las flores defectuosas por piezas con pétalos definidos y uniones controladas. Blender permite añadir grosor a superficies mediante Solidify. La colocación y unión con la luna necesitarían revisión visual y comprobaciones geométricas.

Esta opción ofrece control directo sobre los pétalos. Añadir grosor por sí solo no corrige una flor mal dibujada: hay que definir primero su forma.

Fuente técnica: [Solidify, manual de Blender](https://docs.blender.org/manual/id/4.5/modeling/modifiers/generate/solidify.html).

### 3. TripoSG: candidato alternativo para comparar geometría

Su repositorio oficial indica una GPU CUDA con al menos 8 GB de VRAM. Es una alternativa razonable de generación desde una imagen para una comparación independiente. Eso no demuestra que supere a Hunyuan en este zorro ni que las dependencias funcionen sin ajustes en nuestro Windows. Sigue sin aportar por sí mismo la referencia trasera.

Fuente: [TripoSG, repositorio oficial](https://github.com/VAST-AI-Research/TripoSG).

### 4. Hunyuan3D 2.1: alternativa con mayor exigencia de memoria

Tencent indica 10 GB de VRAM para geometría y un modelo de forma de 3.3B parámetros. Nuestra tarjeta queda por debajo de esa referencia. Hay implementaciones comunitarias con descarga a RAM y menor precisión, pero deben validarse en una instalación separada. No asumir que aceptar más tiempo garantiza que el modelo quepa.

Fuente del requisito: [Hunyuan3D 2.1 oficial](https://github.com/Tencent-Hunyuan/Hunyuan3D-2.1). Ejemplo comunitario con alcance diferente a nuestro motor: [implementación de bajo consumo para Modly](https://github.com/Alefk1708/modly-hunyuan3d-21-lowvram).

### 5. TRELLIS.2 y Hi3D: interesantes para un equipo distinto

TRELLIS.2 exige oficialmente Linux y una GPU NVIDIA de al menos 24 GB. Hi3D v1.0, publicado el 23 de octubre de 2026, refina geometría a partir de una malla y una imagen. Su ruta medida usa Linux y una GPU H20 de 96 GB; el proyecto no establece viabilidad ni mínimo para tarjetas pequeñas, incluso con descarga secuencial a CPU.

Son tecnologías a considerar para pruebas en otro equipo. No son una promesa de ejecución local en esta RTX 3050. Tampoco se han usado servicios externos ni se han adquirido créditos.

Fuentes: [TRELLIS.2 oficial](https://github.com/microsoft/TRELLIS.2), [Hi3D v1.0 oficial](https://github.com/hi3d-official/Hi3Dv1.0).

## Experimento local de extracción

Se encontró una diferencia entre el nivel de extracción del código de Tencent y el flujo de ComfyUI. El pipeline Flow Matching de Tencent usa `mc_level=0.0`, mientras el ejemplo de ComfyUI usa un umbral 0.6.

La inspección del código local de ComfyUI mostró que su VAE transforma la salida con `(x + 1) / 2` y la limita al intervalo `[0, 1]`. Por tanto, el cero del campo original corresponde a 0.5 en esta representación; copiar el cero directamente no es equivalente.

Se ejecutaron dos comparaciones con la misma imagen, semilla, muestreo y volumen de la prueba refinada. Los historiales confirman que los nodos de generación y decodificación estaban en caché: solo se cambió la extracción.

- Umbral 0 directo: resultado descartado, con una superficie envolvente ruidosa. Archivos conservados en `data/research/discarded-threshold-zero` y retirados del historial normal de proyectos.
- Umbral 0.5: reconstrucción válida visualmente, con cambios pequeños respecto a 0.6. No solucionó de forma apreciable las flores ni la espalda. Proyecto experimental: `data/projects/92b57ce7a8e64d328d6014a96aba7850`.

No se cambió el perfil predeterminado. Esta prueba evita atribuir una mejora importante a un simple ajuste del umbral.

Fuentes de la comparación: [pipeline de Tencent](https://github.com/Tencent-Hunyuan/Hunyuan3D-2/blob/main/hy3dgen/shapegen/pipelines.py), `C:\_IA\ComfyUI\comfy\sd.py` y los historiales guardados de cada experimento.

## Fase autorizada e implementada

El usuario autorizó proceder. Se instaló Hunyuan3D-2mv, se integraron entradas etiquetadas en la aplicación y se ejecutaron pruebas locales con frente y espalda. Los resultados y sus limitaciones se registran en [MULTIVIEW.md](MULTIVIEW.md). La lista siguiente conserva el orden de evaluación de esta fase.

1. Recortar vistas frontal y trasera con la mejor resolución disponible y revisar su coherencia; añadir laterales solo cuando aporten información compatible.
2. Descargar y verificar el checkpoint Hunyuan3D-2mv en `C:\_IA\models\checkpoints`.
3. Preparar un flujo separado con entradas etiquetadas; conservar el flujo actual como comparación.
4. Medir consumo y tiempo en 8 GB, comenzando con una resolución de diagnóstico antes de subir la calidad.
5. Comparar frente, espalda, flores y silueta, conservando resultados originales. No usar solo número de caras o cierre de malla como criterio de éxito.
6. Si los pétalos siguen deformados, pasar a flores modeladas por separado y revisar una flor antes de sustituir todas.

## Intervención del usuario

La intervención útil será revisar si las vistas representan el mismo diseño y aprobar la forma de una flor de muestra si se adopta el modelado separado. No hace falta decidir todavía parámetros de impresión para evaluar la fidelidad visual.
