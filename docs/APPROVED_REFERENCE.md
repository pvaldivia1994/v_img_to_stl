# Referencia aceptada por el usuario

El 2026-10-29 el usuario indicó: «La última generación con el retoque de las
imágenes con IA fue satisfactoria». Se registra como aceptación de calidad
visual de la variante `6dd7d7413b1c4fdbbed159505530d82d`, terminada y denominada
«Flores y dorso · Referencia IA · UltraShape».

El flujo que produjo este resultado fue:

1. Preparar el frente y el dorso con el generador de imágenes integrado de
   ChatGPT y conservarlos en `data/ai-prepared-fox`, junto con sus prompts.
2. Generar la malla base con Hunyuan3D-2mv utilizando ambas vistas. Proyecto
   base: `1ce11c63c41940c68c20d063ceb873f0`.
3. Refinar con UltraShape: 50 pasos, 32768 latentes, CFG 5 con ramas secuenciales,
   resolución de extracción 512, lotes de 1024 y semilla 42. El refinador recibe
   directamente la imagen frontal; el dorso queda incorporado en la malla base.

Las imágenes, la malla inicial y el GLB final se conservan en el proyecto
aceptado. `data/approved-reference.json` guarda sus hashes SHA256, los ajustes
exactos de ambas etapas y la aceptación del usuario. Este archivo sirve de
referencia para futuros cambios; no modifica automáticamente los ajustes de
nuevas generaciones ni garantiza el mismo resultado con otras figuras.

El usuario ya exportó el STL a 100 mm de altura. La última exportación es
`model-4efb589f38.stl`: el reporte indica malla cerrada y dos componentes, sin
retirar fragmentos. La aceptación visual no sustituye la comprobación de
espesores y capas para la impresora que se vaya a utilizar.
