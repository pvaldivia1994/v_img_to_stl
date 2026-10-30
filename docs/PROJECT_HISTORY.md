# Historia, resultados y límites vigentes

Este resumen distingue lo realizado de las propuestas de los informes originales.
Los IDs citados son de la máquina de trabajo y no se distribuyen como proyectos
completos dentro de Git. Para instalar, seguir INSTALLATION.md.

## 2026-10-28: de una imagen a geometría local

Se instaló ComfyUI portable v0.43.0 con Hunyuan3D 2.0 y se creó la aplicación
FastAPI/React con visor y exportación STL. Se probaron superficies nativas,
CFG y extracción: aparecieron escalones y problemas de conectividad; se añadió
el extractor propio Lewiner con conservación de componentes y borde exterior.
Se incorporaron U2Net completo, perfiles y preparación de referencias.

La espalda y las flores seguían interpretándose mal con una imagen. Se descargó
Hunyuan3D-2mv, se separaron frente/dorso de la lámina conocida y se integraron
entradas de vistas independientes. El recorte automático solo reconoce esa lámina
por identidad; no se aplica a otras imágenes.

Se añadieron progreso real, 50 pasos y extracción 512 por lotes en RAM. Se
investigaron Meshy y otras familias: las capacidades del servicio Meshy no se
confunden con parámetros disponibles en el modelo local. Más resolución o pasos
no resolvieron por sí solos la fidelidad de pétalos y patas.

También se probó Hunyuan3D 2.1, que terminó en la RTX 3050 de 8 GB con offload.
El flujo integrado recibe solo frontal. No fue la ruta elegida para conservar
un dorso observado; no se implementó un condicionamiento textual de malla.

## UltraShape y recuperación de errores

Se instaló UltraShape en un entorno separado, fijando fuente y checkpoint.
Para funcionar en 8 GB se cambió la inicialización a CPU/BF16, se aplicó offload
por bloques, CFG secuencial, consultas de volumen por lotes, atención completa
con caché K/V exacta y coordenadas float32. No se sustituyeron pesos ni se
usaron aproximaciones de selección de tokens para simular mayor detalle.

Las pruebas cortas de 2 pasos/resolución 32 validaron ejecución, no calidad.
Los intentos largos y sus parámetros se conservaron. Un cálculo se interrumpió
por WinError 5 al guardar el avance; se implementaron JSON atómico, temporales
únicos y reintentos. Se añadió reanudación de refinamientos sin repetir las bases.

## 2026-10-29: referencia aceptada y controles

Se prepararon frente/dorso por edición IA, destacando pétalos y relieve, y se
compararon contra las referencias originales. Hunyuan multivista produjo las
bases y UltraShape las refinó. El usuario consideró satisfactoria la última
variante IA: `6dd7d7413b1c4fdbbed159505530d82d`. Se guardaron parámetros y hashes.
Es la aceptación visual explícita que se usa como referencia del proyecto.

Se añadieron **Detener** y **Regenerar**. La detención cierra procesos de cálculo
identificados, cancela trabajos ComfyUI por ID y frena etapas de una comparación.
No se usa una interrupción global. Regenerar crea otro intento conservando datos.
También se verificó carga real de GPU en UltraShape, aun con ComfyUI sin trabajos.

## Lobito poligonal

Se pidió un diseño nuevo del mismo concepto: lobito acostado en una luna con
flores y caras más geométricas. Se generó un frente y una espalda derivados.
El usuario detectó una cola duplicada en la espalda: se canceló el intento,
se corrigió solo el dorso y se reinició conservando el frente.

- Referencias correctas publicadas: `assets/references/polygonal-wolf`.
- Base: `f965df99c83b4a84b3936a978911011d`, 574,7 segundos.
- Refinamiento: `067996cb019e4b1bb083698b841111ba`, 5721,0 segundos.
- Resultado terminado y malla cerrada; **aceptación artística pendiente**.

## 2026-10-30: publicación inicial

Se preparó la instalación transferible, preset versionado, imágenes de ejemplo,
guía de agentes y skill local. Se corrigieron dependencias de carpetas locales
para el ejecutor y el marcador de prueba de UltraShape en equipos nuevos.
Los resultados pesados quedan fuera de Git; la guía de respaldo explica cómo
conservarlos y transferirlos.

## Pendientes reales

- Valoración del lobito poligonal, incluidas flores, patas, dorso y estilo facetado.
- Medida final e impresora/material de destino; validación de espesores y capas.
- Prueba de instalación completa en otra PC/GPU: las pruebas sin GPU y la
  reconstrucción del código no equivalen a esa validación física.
- Parametrizar `C:/_IA` si se desea soportar otras unidades sin editar scripts.

## Informes históricos conservados

[VALIDATION.md](VALIDATION.md), [QUALITY.md](QUALITY.md),
[MULTIVIEW.md](MULTIVIEW.md), [QUALITY_RESEARCH.md](QUALITY_RESEARCH.md),
[MESHY_AND_FIDELITY.md](MESHY_AND_FIDELITY.md), [HUNYUAN21.md](HUNYUAN21.md),
[WORKFLOWS_HUNYUAN21.md](WORKFLOWS_HUNYUAN21.md),
[FLOWER_REFINEMENT.md](FLOWER_REFINEMENT.md),
[DEEP_FIDELITY_RESEARCH.md](DEEP_FIDELITY_RESEARCH.md),
[FILE_LOCK_RECOVERY.md](FILE_LOCK_RECOVERY.md).

Las frases «pendiente», «lote actual» o propuestas antiguas de Blender en esos
informes corresponden a su fecha. El flujo vigente no necesita Blender y el
estado de aceptación está resumido arriba.
