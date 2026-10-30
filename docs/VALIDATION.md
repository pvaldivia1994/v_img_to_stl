# Validación local — 28 de octubre de 2026

## Resultado funcional

Se completó el recorrido real imagen → API de ComfyUI → GLB → visor → exportación STL con la RTX 3050 de 8 GB. La aplicación está disponible en http://127.0.0.1:8000 mientras los servicios estén activos.

## Pruebas de generación

| Prueba | Configuración | Resultado |
|---|---|---|
| Inicial | Vista principal recortada, flujo antiguo CFG 1, extractor básico | Aproximadamente 60 s; forma reconocible, superficie escalonada y defectos de malla |
| Superficie suave | CFG 1, extractor nativo surface net | Aproximadamente 75 s; mejora visual, pero numerosos defectos de conectividad |
| Fidelidad corregida | Fondo blanco, CFG 8 y surface net | Aproximadamente 92 s; mejor semejanza. PrusaSlicer detectó 25310 bordes abiertos |
| Extracción corregida | Misma entrada y semilla de la prueba anterior, CFG 8, nodo propio marching cubes | Aproximadamente 79 s; STL cerrado confirmado por trimesh y PrusaSlicer |

El nodo propio no elimina componentes pequeños ni cambia el diseño mediante esculturas o remallado volumétrico. Las pruebas anteriores se conservan para comparar.

## STL final de prueba

- Proyecto: `data/projects/c76b9d3feee6455ba27ff5d2f3df376c`.
- Archivo: `model-c588efaab8.stl`.
- Dimensiones: aproximadamente 98.98 × 73.82 × 100.00 mm.
- Caras: 555040.
- Componentes: 8; el principal contiene 554396 caras.
- Trimesh: `watertight = true`.
- PrusaSlicer 2.7.4: `manifold = yes`, 8 partes, altura 100.000000 mm.
- Inspección original de PrusaSlicer: `prusa-inspection.txt` dentro del proyecto.
- Vista previa y archivo Blender guardados junto al GLB original.

Esto verifica escala y cierre de la malla. Quedan pendientes la valoración del usuario, el fragmento fino que sale de la punta superior, el destino de los componentes pequeños, espesores, estabilidad y revisión de capas con la configuración de impresión elegida. No se ha generado G-code ni realizado una impresión.

## Software

- 14 pruebas automatizadas superadas: escala, conservación de originales y componentes, protección frente a sobrescritura, dimensiones inválidas, validación de imágenes, desconexión, bloqueo de trabajos simultáneos, exportación y acceso limitado a archivos de resultados, superficies de prueba cerradas y límites de volumen.
- Compilación de la interfaz completada. Vite muestra un aviso de tamaño del módulo Three.js; no impide la compilación ni el uso local.
- Se probó la exportación mediante el botón de la interfaz y también mediante la API.
- Se comprobó la recuperación de la conexión de la interfaz después de reiniciar los servicios.
- Los servicios se vinculan a `127.0.0.1`.
- El equipo tiene Blender y laminadores existentes; no fue necesario descargarlos.

Los tiempos son observaciones de esta máquina y estas entradas; no representan una garantía para todas las imágenes.
