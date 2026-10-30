# Reconstrucción con varias vistas

Implementado el 28 de octubre de 2026. Todo el cálculo se realiza en el equipo local; se conserva el generador de una sola vista para comparar.

## Uso en la aplicación

1. Cargar el frente en «Imagen frontal».
2. Activar «Usar varias vistas» y cargar al menos una imagen adicional en Espalda, Izquierda o Derecha. Cada archivo debe contener una sola vista de la misma figura.
3. Usar fondos sencillos, figura completa y orientaciones coherentes. Desactivar «Preparar fondo blanco» si los archivos ya están preparados.
4. Elegir «Más detalle» para el resultado final. Revisar frente y espalda en el visor.
5. Exportar con una altura explícita y revisar el resultado en un laminador. La opción de conservar la pieza principal elimina fragmentos separados de la copia exportada.

Las vistas, parámetros, semilla, GLB y exportaciones se guardan por proyecto. «Generar otra variante» conserva todas las vistas y el perfil; utiliza una nueva semilla.

## Instalación y flujos

- Modelo oficial: [Tencent Hunyuan3D-2mv](https://huggingface.co/tencent/Hunyuan3D-2mv).
- Archivo local: `C:\_IA\models\checkpoints\hunyuan3d-dit-v2-mv.safetensors`.
- Tamaño: 4,928,151,562 bytes.
- SHA256 verificado: `d36f5881bcdc56726b73e517cd444c13c60732431622da7268145355c8d38e9c`.
- Nodo nativo `Hunyuan3Dv2ConditioningMultiView`, con embeddings etiquetados por orientación. No se concatenan las imágenes en una lámina.
- `app/workflows.py` construye el flujo según las vistas disponibles; `workflows/hunyuan3d-2mv-api.json` conserva un ejemplo frontal/trasero. La plantilla oficial de referencia está en `workflows/official-hunyuan3d-2mv.json`.
- CFG 7.5, sampler Euler, scheduler normal, latent 3072; extracción propia Lewiner con umbral 0.6. Perfil rápido: 20 pasos, volumen 256. Perfil de detalle: 40 pasos, volumen 384. Ambos usan 8000 chunks.

Fuente de integración: [documentación oficial de ComfyUI](https://docs.comfy.org/tutorials/3d/hunyuan3D-2).

## Preparación de la referencia del zorro

`scripts/prepare_multiview.py` conserva recortes y resultados en `data/multiview-fox`. Sus coordenadas corresponden exclusivamente a `Zorro Durmiente en Luna Creciente.png`.

Se usaron el panel frontal grande y el trasero de la columna derecha. Se eliminaron regiones grandes de fondo oscuro neutro antes de aplicar U2Net completo: U2Net por sí solo retenía una mancha oscura dentro del hueco de la luna. La selección por tamaño conserva las pequeñas marcas de ojos y nariz. Se revisaron visualmente los resultados sobre blanco.

Los laterales de la franja inferior se conservaron como entradas auxiliares, pero no se usaron en estas dos pruebas: tienen menor resolución y no son vistas calibradas. Los dos paneles elegidos tampoco son ortográficos exactos, por lo que puede haber diferencias entre sus detalles.

## Prueba de diagnóstico

- Proyecto: `data/projects/ffc81538e1454b6fb82c4b7501df43f7`.
- Semilla: 4007959359; frente + espalda; perfil rápido.
- Tiempo registrado por la aplicación: 88.6 segundos, sin incluir exportación.
- Memoria máxima observada por muestreo cada 10 segundos: 6262 MiB. No es una medición continua del pico.
- Exportación original a 100 mm: malla cerrada y orientación consistente, 483206 caras y 4 componentes.
- La espalda tiene una cabeza y una cola mucho más próximas a la referencia; desaparece buena parte del relieve irregular de la generación de una sola vista.
- Las flores tienen pétalos más reconocibles, pero aún aparecen uniones y relieves deformados. El cierre de la malla no demuestra fidelidad artística ni espesor imprimible.

Se conservan `preview-front.png`, `preview-back.png`, GLB, STL e historial de ComfyUI. La prueba de mayor detalle se registra por separado para no sobrescribir este resultado.

## Resultado de mayor detalle

- Proyecto: `data/projects/0bf73cbab92d4b3496c6461723a69b88` (Zorro-MV-detalle).
- Mismas dos imágenes y semilla; 40 pasos y volumen 384. El resultado cambia también por los pasos adicionales; no se atribuye la mejora solo a la resolución de extracción.
- Tiempo: 232.7 segundos, sin exportación. Máximo observado en las muestras de memoria: 6549 MiB.
- Se conserva `original.glb` y el STL con todos sus componentes (`model-abb01a8342.stl`).
- Copia limpia: `model-4ccf81c1e2.stl`, 1,017,954 caras, una pieza, cerrada y con orientación consistente. Se retiraron dos fragmentos de 192 caras en total.
- Dimensiones provisionales: 106.41 × 65.57 × 100 mm.
- PrusaSlicer confirma `manifold = yes` y `number_of_parts = 1`; informe conservado en `prusa-info.txt`. No se realizó laminado ni validación física.
- Vistas para revisar: `preview-front.png` y `preview-back.png`. También se guardan sus escenas de Blender.

La espalda conserva la mejora importante frente al resultado de una sola vista: cabeza lisa y cola definida, próximas al panel trasero. Los pétalos delanteros se distinguen mejor que antes, pero siguen existiendo uniones y formas poco naturales, especialmente en el pequeño grupo trasero y la unión entre flores. La generación de mayor detalle no resuelve por completo este problema artístico.

La aplicación quedó mostrando este proyecto. El siguiente punto de intervención es revisar estas flores y decidir si la mejora es suficiente o si conviene sustituirlas mediante una flor modelada por separado.

## Comprobaciones de la aplicación

23 pruebas automatizadas superadas: incluyen almacenamiento y descarga de vistas, repetición, rechazo de imágenes secundarias inválidas, ausencia del checkpoint y conexiones correctas de cada orientación en el flujo. La interfaz compila correctamente y se revisaron los controles adicionales y el proyecto real en el navegador.

## Límites y siguiente revisión

Más pasos o resolución pueden definir mejor una forma incorrecta. Las imágenes aportan información que faltaba, pero no garantizan que todos los pétalos sean correctos. Si la revisión visual sigue rechazando las flores, el siguiente trabajo artístico es crear una flor de muestra en Blender y acordar su forma antes de sustituir las demás.

La altura de 100 mm sigue siendo provisional. Quedan pendientes la aprobación visual y los datos de impresora/material para evaluar espesores, apoyos y preparación de impresión.
