# Refinamiento de flores sin edición manual

Implementación del 28 de octubre de 2026. El usuario autorizó aplicar las mejoras investigadas y acepta cálculos largos. Se conservan todas las referencias y mallas iniciales. No se utiliza Blender.

## Cambios aplicados

- Comparación del nivel de superficie 0,60/0,50 sobre el mismo campo de Hunyuan3D 2.1. El proyecto `87e832c073b24963bf65379e462f5fc4` terminó en 6,7 s; se reutilizó el trabajo anterior del motor.
- Encuadre al 85% conservando los píxeles de la figura, la semilla, CFG 5 y 50 pasos. Proyecto `1dd7fa8aabca428c8099f75d2a6b0790`, terminado y conservado junto al encuadre anterior del 94%.
- Ejecutor secuencial para comparar otras dos semillas y 75 pasos; los ajustes, entradas, historial del motor y resultados se guardan por proyecto.
- Integración de UltraShape como segunda etapa aprendida: imagen frontal y malla inicial → refinador → GLB nuevo → exportación STL habitual. No es un aumento artificial de polígonos de la malla anterior.
- Progreso real durante los bloques de difusión y los lotes de decodificación. Las etapas sin medida permanecen indeterminadas. El visor incorpora frente, espalda y acercamiento, y permite consultar los ajustes y la referencia de cada comparación.

## Instalación aislada

- Código oficial: `C:\_IA\UltraShape-1.0`, revisión `5e8dcef05df101ab00ab6cd5fdd0ed0c74fbca66`.
- Entorno: `C:\_IA\envs\ultrashape`, Python 3.11, PyTorch 2.5.1+cu121 y torchvision 0.20.1+cu121. Dependencias completas en `requirements-ultrashape.lock.txt`; `pip check` sin conflictos.
- Pesos: `C:\_IA\models\ultrashape\ultrashape_v1.pt`, 7.366.231.254 bytes. SHA256 verificado: `c96ae010c4169597fd0006dcb08056bf6104a1fca249b10fed7ddded324c3f0f`.
- Configuración de DINO: descargada del repositorio oficial `facebook/dinov2-large`. El checkpoint completo ya incluye sus pesos; se evita una segunda descarga de pesos idénticos.
- Cachés y descargas bajo `C:\_IA`. No se cambiaron las dependencias del ComfyUI portable ni sus puertos.

Las adaptaciones de importación para inferencia están registradas con hashes en `C:\_IA\UltraShape-1.0\forma-runtime.json`. Se omiten dependencias de entrenamiento y postprocesado que no se usan, se hace opcional la importación de cubvh y se sustituye la atención de secuencias variables por SDPA de PyTorch cuando flash-attn no está disponible. No se cambian capas aprendidas ni pesos.

## Memoria y precisión

El script oficial mueve todos los componentes a CUDA antes de activar offload. Aquí se inicializan y cargan en CPU, en BF16; Accelerate mantiene los pesos de DiT en RAM y lleva sus bloques a la GPU al ejecutarlos. El encoder de imagen y el VAE se usan en fases separadas. Antes se liberan los modelos inactivos de ComfyUI mediante `/free`, sin detener su servicio.

La decodificación consulta el volumen completo por lotes y guarda el campo en RAM. Usa toda la atención del VAE, sin selección aproximada de tokens. Se activa la caché K/V exacta expuesta por el código oficial para no recalcular las mismas proyecciones en cada lote. Las coordenadas se mantienen en float32 hasta la codificación de Fourier: BF16 no ofrece suficiente precisión de coordenadas para aprovechar todas las posiciones de un volumen 768/1024.

Configuración del lote largo: UltraShape con 75 pasos, 16.384 latentes, CFG 5, consultas de 1024 puntos, volumen 768 y nivel bruto 0. Se conserva `refined-latents.pt`, `voxel-indices.pt` y `refined-field.npy` junto al resultado. No se reducen caras ni se eliminan componentes.

La prueba de compatibilidad `4cf7591150604faaace9a5e445db7ec9` completó carga, dos pasos con 16.384 latentes, decodificación 32 y GLB cerrado en 82,3 s. PyTorch registró un máximo asignado de 5009 MiB y reservado de 7630 MiB; son medidas del asignador de ese proceso, no del consumo total del sistema. Este resultado solo valida compatibilidad: dos pasos y resolución 32 no sirven para evaluar flores. Las pruebas internas se conservan y se ocultan del historial de usuario.

## Alcance y límites

DMC se investigó y se comprobó la ausencia de wheel de `diso==0.1.4` para este entorno Windows. Tampoco se encontró el componente de compilación C++ de Visual Studio necesario para construirlo. Se mantiene Marching Cubes de Lewiner en CPU. DMC y FlashVDM son alternativas de extracción/evaluación, no pesos de refinamiento adicionales; no se presentan como mejoras ya validadas en flores. No se instala un binario de terceros incompatible para forzar esta opción.

El generador Hunyuan activo mantiene su límite comprobado de volumen 512. La resolución 768 se aplica en el refinador independiente; no se envía un valor que el nodo activo rechazaría. La resolución 1024 queda disponible por CLI, sin lanzarse automáticamente: supone más del doble de consultas que 768 y no garantiza mayor parecido.

El fondo, las flores y las patitas deben revisarse visualmente al terminar. Ninguna medida de caras, cierre de malla o uso de memoria demuestra que los pétalos tengan la forma correcta. La espalda sigue siendo interpretada por esta cadena de una imagen.

## Ejecución y recuperación

Lote largo iniciado y verificado en ejecución: primera variante `3342ae7c46184f73b3168a05a57b7779` («Flores · encuadre 85% · semilla B»). El motor confirmó muestreo y la API publicó progreso real. Después siguen la semilla C, los 75 pasos y UltraShape. Registro persistente: `data/logs/fidelity-batch-20261028.log`. El enlace de la aplicación en la red es `http://10.0.0.83:8000/`.

La segunda comprobación interna, `25d64515837343b2941a37875d41b969`, también terminó: 79,3 s, malla cerrada, 5009 MiB asignados y 7630 MiB reservados. Incluyó progreso por bloques, caché K/V y coordenadas float32 en la ejecución real del VAE. No valida la calidad artística a resolución 768; esa salida sigue pendiente del lote largo.

El lote actual no necesita reiniciar servicios. El ejecutor independiente escribe proyectos normales, visibles por la aplicación que ya está abierta. La API incorpora `/api/projects/{id}/refine` y el botón «Refinar detalles con UltraShape». Se comprobó que el servidor actual ya informa `refinement_ready: true`; el botón permanece deshabilitado mientras el lote ocupa la GPU. No se necesita reiniciar para seguir este lote. No detener el equipo ni los procesos durante el lote.

Para iniciar una comparación posterior desde la raíz del proyecto:

```powershell
.venv\Scripts\python.exe -m scripts.run_fidelity_batch 9cdb7cf5b3a54d93b5f13ca5456b0cfc --start-trial 1 --trials 3 --skip-extraction --refine-after
```

No ejecutar de nuevo mientras haya un trabajo activo. El refinador se ejecuta después de las tres comparaciones, sobre la variante de 75 pasos. Esta elección fija la prueba más exigente; no afirma que sea la mejor artísticamente. Los manifiestos de lote están en `data/fidelity-fox/batch-*.json`; los IDs del último refinamiento se guardan en `latest-ultrashape-project-id.txt`. Si un proceso informa error, se conserva el proyecto y el motivo, y el lote se detiene.

## Validación

- 35 pruebas de aplicación superadas: se comprueba también preservación de malla y referencia, creación separada del refinamiento, bloqueo de concurrencia y rechazo si el refinador falta.
- Interfaz compilada correctamente.
- Atención SDPA comprobada contra resultados independientes y aislamiento entre secuencias.
- Caché K/V comprobada contra la versión sin caché y reinicio entre mallas.
- Coordenadas, lotes y progreso del decodificador verificados, incluyendo coordenadas float32 con latentes BF16.
- La comprobación artística de la salida larga queda pendiente del resultado y del usuario.

Fuentes: [UltraShape oficial](https://github.com/PKU-YuanGroup/UltraShape-1.0), [pesos publicados](https://huggingface.co/infinith/UltraShape), [versiones oficiales de PyTorch](https://pytorch.org/get-started/previous-versions/), [investigación previa](WORKFLOWS_HUNYUAN21.md).
