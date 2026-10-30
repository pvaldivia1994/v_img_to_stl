# Refinamiento de calidad — 28 de octubre de 2026

El usuario pidió seguir afinando la calidad antes de preparar la impresión.

## Cambios

- Se sustituyó U2NetP (modelo auxiliar ligero de aproximadamente 4.6 MB) por U2Net completo (aproximadamente 176 MB) para preparar el fondo. La inspección de la entrada muestra una punta de luna mejor conservada y menos sombra residual.
- Se añadió el perfil «Más detalle»: 40 pasos, CFG 6, resolución de volumen 384, bloques de 8000. «Prueba rápida» conserva 20 pasos, CFG 8 y resolución 256.
- La interfaz selecciona inicialmente «Más detalle». La API mantiene «standard» como valor predeterminado para clientes existentes; ambos perfiles quedan registrados en cada proyecto.
- Se añadió la opción de exportación «Conservar solo la pieza principal». Está desactivada inicialmente y conserva el GLB original. El informe registra componentes y caras retirados.
- Se reconstruyen las normales del STL desde los triángulos finales para evitar inconsistencias de normales importadas al seleccionar una submalla.

## Comparación real

Se usó la misma semilla `4007959359` de la prueba anterior. Se cambiaron conjuntamente preparación de fondo y perfil, por lo que esta comparación evalúa el conjunto de ajustes; no aísla el efecto individual de cada parámetro.

| Dato | Prueba anterior | Nueva prueba |
|---|---|---|
| Preparación del fondo | U2NetP | U2Net |
| Perfil | 20 pasos, CFG 8, volumen 256 | 40 pasos, CFG 6, volumen 384 |
| Tiempo de generación observado | Aproximadamente 79 s | 253.4 s |
| Componentes del resultado original | 8 | 25 |
| Componentes de la copia limpia | Sin limpieza adicional | 1 |

La nueva generación terminó correctamente, aunque tuvo una ralentización temporal durante la conversión del volumen. El máximo de memoria observado por muestreo fue 6709 MiB. No fue necesario interrumpirla ni reducir la resolución o los bloques; el perfil guardado coincide con el que completó la prueba.

## Resultado entregado

- Proyecto: `data/projects/456b874aca38474fadabcc48a11f3214`.
- Nombre en la aplicación: **Zorro - detalle refinado**.
- STL limpio: `zorro-detalle-limpio-100mm.stl`.
- Dimensiones: aproximadamente 111.69 × 77.76 × 100.00 mm.
- 1043452 caras; malla cerrada y orientación consistente según trimesh.
- Se retiraron 24 componentes separados, con 4820 caras en total (aproximadamente el 0.46 % de las caras del original). Se conserva la figura principal completa.
- PrusaSlicer 2.7.4: `manifold = yes`, `number_of_parts = 1`, altura 100 mm. No informó caras invertidas en la inspección final.
- Inspección del laminador: `prusa-final-inspection.txt`.
- Vistas guardadas: `preview-clean.png`, `preview-front.png` y `preview-back.png`, además de sus archivos Blender.

La punta de la luna ya no muestra la prolongación fina de la primera versión. La parte trasera sigue siendo una interpretación a partir de una sola imagen. No se ha certificado el espesor de las flores, orejas y puntas, ni se han preparado soportes o G-code.

## Validación del programa

16 pruebas automatizadas superadas, incluyendo selección y rechazo de perfiles, conservación del original, limpieza opcional por componentes y coherencia de las normales del STL. Interfaz compilada correctamente.

## Archivos auxiliares

U2Net se guarda bajo `C:\_IA\models\background`. Fuente usada por rembg: https://github.com/danielgatis/rembg/releases/download/v0.0.0/u2net.onnx

`scripts/quality_trial.py` permite repetir una comparación por la API de la aplicación y registrar las lecturas de GPU. `scripts/render_model.py` admite vistas frontal, trasera y tres cuartos de GLB o STL.
