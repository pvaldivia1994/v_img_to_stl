# Flujos investigados para mejorar flores y patitas

> Actualización posterior: las mejoras compatibles ya se implementaron, UltraShape pasó dos pruebas completas en la RTX 3050 y el lote largo quedó en ejecución. Estado, instalación y límites en [FLOWER_REFINEMENT.md](FLOWER_REFINEMENT.md). El texto siguiente conserva los hallazgos de la investigación previa.

Revisión del 28 de octubre de 2026. Se inspeccionaron los grafos JSON y el código que los ejecuta. Se distinguen parámetros publicados, observaciones de este equipo e hipótesis por probar. No se instalaron paquetes ni se cambiaron los parámetros de la aplicación durante esta investigación.

## Conclusión

Nuestro flujo ya supera los valores de pasos y resolución de varios ejemplos populares. Las mejoras con mayor fundamento son comparar la preparación de la imagen, revisar la extracción de la superficie y evaluar una segunda etapa de refinamiento geométrico con UltraShape. Subir pasos o polígonos no impone por sí solo la forma correcta de cada pétalo o patita.

## Comparación de flujos

| Flujo inspeccionado | Configuración publicada relevante | Implicación para este proyecto |
|---|---|---|
| [Plantilla nativa de ComfyUI](https://github.com/Comfy-Org/workflow_templates/blob/main/templates/3d_hunyuan3d-v2.1.json) | 30 pasos, CFG 5, Euler/normal, 4096 latentes; decodificación 256 y surface net a 0.6 | Ya usamos 50 pasos y volumen 512. Su grafo no aporta un refinador adicional. Se mantiene nuestro extractor por los problemas de conectividad encontrados antes. |
| [VisualBruno: Mesh_Generation](https://github.com/visualbruno/ComfyUI-Hunyuan3d-2-1/blob/main/example_workflows/Mesh_Generation.json) | 25 pasos, CFG 5, volumen 384, DMC y FlashVDM; incluye nodos de postprocesado y decimación | Es interesante comparar el extractor y el preprocesado. No copiar automáticamente el límite de caras o la eliminación de fragmentos: podrían afectar pétalos pequeños. |
| [VisualBruno: Full_Workflow](https://github.com/visualbruno/ComfyUI-Hunyuan3d-2-1/blob/main/example_workflows/Full_Workflow.json) | 25 pasos, CFG 7.5, volumen 256, MC y reducción a 40000 caras antes del texturizado | Su complejidad adicional se concentra en UV/materiales. Sus valores de reducción no son una mejora de fidelidad del STL. |
| [VisualBruno: Apply_8Views_On_Mesh](https://github.com/visualbruno/ComfyUI-Hunyuan3d-2-1/blob/main/example_workflows/Apply_8Views_On_Mesh.json) | Carga una malla y hornea albedo/materiales desde varias vistas | No reconstruye la forma desde ocho imágenes. No resuelve la falta de entrada trasera de nuestro generador 2.1. |
| [Kijai: nodo simple 2.1](https://github.com/kijai/ComfyUI-Hunyuan3DWrapper/blob/main/nodes.py) | Elimina fondo, usa el pipeline 2.1; expone 50 pasos, CFG 5 y resolución de extracción hasta 1024 | Permite estudiar resoluciones mayores, pero usa los mismos pesos. No convierte una flor mal interpretada en una flor correcta automáticamente. |
| [Hunyuan3D 2.1 + UltraShape](https://github.com/Hahihula/comfyui-ultrashape/blob/master/example_workflows/3d_hunyuan3d-ultrashape-v2.1.json) | La malla de Hunyuan y la imagen entran en un modelo de refinamiento separado | Es el cambio más sustancial de arquitectura encontrado. Su beneficio en esta figura y su ejecución en 8 GB siguen sin medirse. |

Los ejemplos pueden referirse a nombres de nodos antiguos; no se han importado ciegamente como flujos operativos. Copias de consulta, árboles de repositorios y código están bajo `data/research/workflows21`, excluido de Git.

## Preparación de la imagen: diferencia verificable

El [config oficial de Tencent](https://huggingface.co/tencent/Hunyuan3D-2.1/blob/main/hunyuan3d-dit-v2-1/config.yaml) usa `border_ratio: 0.15`. Su [preprocesador](https://github.com/Tencent-Hunyuan/Hunyuan3D-2.1/blob/main/hy3dshape/hy3dshape/preprocessors.py) recorta según alfa, centra, deja margen y compone sobre blanco. Es el 15% total de la dimensión mayor, no 15% por cada lado. La figura queda aproximadamente al 85%.

El [config 2.1 de VisualBruno](https://github.com/visualbruno/ComfyUI-Hunyuan3d-2-1/blob/main/configs/dit_config_2_1.yaml) cambia ese valor a 0.0. Por eso no hay un único encuadre compartido por todos los wrappers. Nuestra referencia actual usa aproximadamente 3% por cada lado, con una ocupación cercana al 94%.

**Prueba propuesta:** comparar la misma figura al 85% y al 94%, conservando semilla, CFG y pasos. Es una hipótesis de mejora por preparación de entrada, no un error demostrado ni una afirmación sobre cómo se entrenó el modelo. Revisar especialmente el borde de los pétalos y las dos patitas antes de usar la imagen.

## Extracción: nivel y método son cambios distintos

El [pipeline de Tencent](https://github.com/Tencent-Hunyuan/Hunyuan3D-2.1/blob/main/hy3dshape/hy3dshape/pipelines.py) usa nivel MC 0.0. ComfyUI transforma el campo con `(x + 1) / 2` y lo limita a `[0, 1]`; el nivel equivalente es 0.5. Actualmente usamos 0.6.

Comparar 0.5 y 0.6 en el mismo campo decodificado puede cambiar el grosor o recuperar una superficie fina. No reconstruye anatomía que el modelo no haya inferido. La comparación anterior en 2.0 aportó pocos cambios; aún no se ha repetido en 2.1. Se puede reutilizar la caché cuando el motor conserva el campo, y verificarlo en su historial.

[DMC](https://github.com/Tencent-Hunyuan/Hunyuan3D-2.1/blob/main/hy3dshape/hy3dshape/models/autoencoders/surface_extractors.py) es otro extractor y requiere `diso`. No es un nuevo generador ni una casilla que añada pétalos. Se debe verificar compatibilidad con Windows/PyTorch, cierre de malla y contornos antes de adoptarlo. FlashVDM modifica cómo se evalúa el volumen; tampoco aporta nuevos pesos de generación.

## Refinamiento real con UltraShape

[UltraShape 1.0](https://github.com/PKU-YuanGroup/UltraShape-1.0) refina una malla inicial usando la imagen. Es una segunda etapa aprendida de geometría, adecuada para investigar cuando la figura general está bien y faltan detalles locales. Esta es una inferencia de adecuación al problema; no se ha probado que reproduzca nuestras flores.

Flujo propuesto: imagen preparada → Hunyuan3D 2.1 → conservar la malla base → liberar los componentes de Hunyuan → cargar UltraShape → refinar con la misma imagen → guardar una variante → comparar flores, patitas y espalda.

El proyecto oficial recomienda para bajo consumo reducir latentes (ejemplo: 8192), bajar el lote de consultas (ejemplo: 2048) y activar `low_vram`. Ver [instrucciones oficiales](https://github.com/PKU-YuanGroup/UltraShape-1.0#low-vram). Una prueba inicial razonable sería salida 384 y después 512 si cabe. No trasladar los 4096 latentes de Hunyuan como si fueran el mismo parámetro o modelo.

**Viabilidad en esta GPU pendiente.** El [wrapper de jtydhr88](https://github.com/jtydhr88/ComfyUI-UltraShape1) ofrece descarga a CPU y estimaciones de memoria, pero esas estimaciones no constituyen una prueba en nuestra RTX 3050. Sus textos sobre `num_chunks` no coinciden siempre con el código; el parámetro real representa puntos por lote y reducirlo disminuye la memoria de consultas.

Además, tanto el [script oficial](https://github.com/PKU-YuanGroup/UltraShape-1.0/blob/main/scripts/infer_dit_refine.py) como el [loader comunitario revisado](https://github.com/jtydhr88/ComfyUI-UltraShape1/blob/master/nodes.py) envían inicialmente los componentes a la GPU antes de activar offload. Para 8 GB habría que controlar también ese pico de carga y no confiar solo en la opción. Las dependencias y sus alternativas para Windows deben revisarse en una instalación separada.

La API del repositorio [infinith/UltraShape](https://huggingface.co/infinith/UltraShape/tree/main) publica `ultrashape_v1.pt` de 7,366,231,254 bytes, SHA256 `c96ae010c4169597fd0006dcb08056bf6104a1fca249b10fed7ddded324c3f0f`. Solo se consultaron sus metadatos; no se descargaron pesos durante esta investigación.

## Orden de pruebas recomendado

1. Revisar la malla 2.1 que ya terminó y fijarla como referencia.
2. Comparar extracción 0.5/0.6 del mismo campo; comprobar que generación y VAE salen de caché.
3. Comparar encuadre 85%/94% manteniendo los demás parámetros.
4. Evaluar tres semillas con el encuadre elegido. Escoger por flores, patitas y silueta, no por número de caras.
5. Preparar UltraShape con carga inicial en CPU y probar el refinamiento con bajo consumo. Medir memoria y resultado antes de integrar sus nodos en la aplicación.
6. Solo después, probar 75 pasos o volumen 768/1024 en la mejor variante. La resolución 1024 tiene cerca de ocho veces los puntos del volumen 512 si se evalúa de forma densa; hay que contemplar RAM, tiempo y extracción además de VRAM.

No se presupone que el máximo de cada parámetro dé el mejor resultado. No se programa un lote largo hasta definir qué variable se está comparando.

## Estado local comprobado

La generación `9cdb7cf5b3a54d93b5f13ca5456b0cfc` terminó sin errores en 675.3 segundos. Máximo observado en las muestras: 7307 MiB; no es una medición continua del pico. Se conserva el GLB de 28,995,200 bytes y todo el flujo. La valoración artística del usuario sigue pendiente.
