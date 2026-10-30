# Comparación con Hunyuan3D 2.1

Fecha: 28 de octubre de 2026. El usuario considera que las flores y las patitas aún se alejan de la referencia y acepta más tiempo de cálculo. No se utiliza Blender.

## Motivo de la prueba

La última generación multivista completó 50 pasos y un volumen 512 en 500.7 segundos. Su aumento de resolución mejoró la superficie, pero el usuario sigue observando errores de forma. Esto justifica comparar otro modelo antes de invertir más tiempo en densificar la misma interpretación.

Tencent publica Hunyuan3D-Shape-v2-1 como modelo de 3.3B y documenta 10 GB de VRAM para generar geometría. ComfyUI incorpora un flujo nativo con un checkpoint que incluye los componentes necesarios. En esta RTX 3050 de 8 GB la ejecución es experimental; el motor puede descargar capas a los aproximadamente 64 GB de RAM, pero la disponibilidad de RAM no demuestra por sí sola que el cálculo quepa.

Fuentes: [Tencent Hunyuan3D 2.1](https://github.com/Tencent-Hunyuan/Hunyuan3D-2.1), [flujo nativo de ComfyUI](https://docs.comfy.org/tutorials/3d/hunyuan3D-2).

## Archivo y origen

- Repositorio: [Comfy-Org/Hunyuan-3D-2.1](https://huggingface.co/Comfy-Org/Hunyuan-3D-2.1).
- Descarga: https://huggingface.co/Comfy-Org/Hunyuan-3D-2.1/resolve/main/hunyuan_3d_v2.1.safetensors
- Destino: `C:\_IA\models\checkpoints\hunyuan_3d_v2.1.safetensors`.
- Tamaño publicado por la API: 7,365,943,290 bytes.
- SHA256 publicado como LFS OID: `5f21e98a6cb99b13b5e224abaee33929570fff7af2b6a0060001559a04ba9d72`.
- `scripts/download_hunyuan21.py` conserva una descarga parcial reanudable y solo publica el archivo final después de comprobar tamaño y hash. El estado está en `C:\_IA\downloads\hunyuan21-download.json`.

## Integración

El selector «Modelo de generación» permite elegir 2.0 o 2.1. Los proyectos nuevos guardan `model_family`; los anteriores se interpretan como 2.0. Repetir una variante conserva su modelo, entradas y perfil. Se muestran el modelo y la modalidad en el proyecto.

El flujo 2.1 utiliza una sola imagen frontal. No admite la segunda referencia trasera en este flujo. La API rechaza vistas adicionales en lugar de ignorarlas; la interfaz explica este límite. La comparación debe incluir también la espalda, que puede empeorar al dejar de recibir esa observación.

Parámetros de la comparación final:

- Misma referencia frontal preparada y semilla 4007959359.
- Checkpoint FP16 original, sin reducción adicional de precisión.
- Latentes: 4096, según la plantilla nativa 2.1, frente a 3072 en 2.0.
- Muestreo Euler/normal, shift 1 y sampling flow.
- CFG 5, según la plantilla oficial 2.1; 50 pasos en perfil máximo.
- Volumen 512 y consultas de 2048 puntos por lote mediante el nodo propio de decodificación en RAM.
- Extracción Lewiner a umbral 0.6 y conservación de todos los componentes. No se reduce la malla ni se eliminan pétalos pequeños automáticamente.
- El seguimiento por etapas se mantiene.

La plantilla oficial se conserva en `workflows/official-hunyuan3d-21.json`, extraída del paquete instalado. Aumentar los latentes arbitrariamente no equivale a utilizar un modelo entrenado para otra capacidad.

## Otras opciones y límites

[TripoSG](https://github.com/VAST-AI-Research/TripoSG) declara al menos 8 GB CUDA y sigue siendo una alternativa para una comparación de otra familia. No se ha instalado ni medido en este proyecto.

[TRELLIS.2](https://github.com/microsoft/TRELLIS.2) tiene requisitos oficiales superiores y una instalación distinta; no se presenta como una descarga intercambiable que vaya a funcionar en esta tarjeta.

Más resolución de extracción no proporciona nuevos detalles que el modelo no haya reconstruido. Más pasos tampoco garantizan pétalos correctos ni patas anatómicamente coherentes. El objetivo de esta prueba es determinar si la mayor capacidad del modelo aporta una mejora visible en estas zonas.

## Verificaciones

31 pruebas automatizadas superadas: incluyen configuración nativa 2.1, capacidad latente, CFG, decodificador, preservación al repetir, ausencia del checkpoint y rechazo de vistas incompatibles. La interfaz compila correctamente.

La prueba de ejecución real y la calidad artística se registrarán por separado. No confundir una descarga completada con una prueba de generación superada.

## Ejecución sin reiniciar servicios

La revisión automática rechazó el intento de reiniciar los servicios. Para no interrumpirlos, `scripts/run_model_comparison.py` utiliza el motor existente y crea un proyecto normal en disco. El proceso no abre puertos: registra las vistas, parámetros, avance y resultado para que la aplicación que ya está abierta pueda mostrarlos. Verifica antes que no haya trabajos activos y que el checkpoint final esté disponible en ComfyUI.

El selector de modelo de la API actualizada estará activo en el próximo arranque normal de la aplicación. No reiniciar durante esta comparación: el proceso separado mantiene el seguimiento hasta que termine. El rechazo del reinicio no se presenta como una restricción de calidad del modelo.

## Trabajo real iniciado

- Checkpoint descargado por completo y hash SHA256 verificado.
- Proyecto: `9cdb7cf5b3a54d93b5f13ca5456b0cfc`, «Zorro - Hunyuan 2.1 - flores y patitas».
- Página de red: http://10.0.0.83:8000/?project=9cdb7cf5b3a54d93b5f13ca5456b0cfc
- El motor identificó `Hunyuan3Dv2_1`, preparó aproximadamente 5818 MB de pesos de forma para carga dinámica y comenzó los pasos de muestreo sin error de memoria. Esto verifica el arranque, no toda la generación.
- Los registros del ejecutor están en `data/logs/hunyuan21.stdout.log` y `hunyuan21.stderr.log`; las muestras de memoria se guardan en la carpeta del proyecto.
- El botón para repetir proyectos 2.1 permanece desactivado si la página detecta que la API antigua sigue cargada: evita repetir accidentalmente con el modelo 2.0. Se activará tras el próximo arranque con la API actualizada y el checkpoint disponible.

La generación completa y la comparación artística siguen pendientes. El trabajo queda ejecutándose para revisión posterior del usuario.

Se comprobó después que terminaron los 50 pasos del muestreo y comenzó la decodificación de superficie: 65,921 lotes a resolución 512. Las primeras lecturas de esta etapa muestran aproximadamente 6320 MiB usados, sin error de memoria. Durante el muestreo se observaron alrededor de 7152 MiB. Son muestras puntuales, no un pico continuo. La finalización de la malla y su fidelidad siguen pendientes.

## Actualización: ejecución completada

La generación terminó correctamente en 675.3 segundos. El máximo de las muestras conservadas fue 7307 MiB. GLB guardado: 28,995,200 bytes. Esto confirma la ejecución completa de esta configuración en el equipo; la fidelidad de flores y patitas requiere revisión visual.

La investigación posterior de flujos, diferencias y siguiente plan de comparación está en [WORKFLOWS_HUNYUAN21.md](WORKFLOWS_HUNYUAN21.md). En esa investigación no se instalaron wrappers ni se cambiaron los valores predeterminados.
