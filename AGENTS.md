# Guía para agentes — Forma / v_img_to_stl

Leer primero este archivo y README.md. Para preparar imágenes, leer la skill
local `.agents/skills/prepare-3d-references/SKILL.md`. La instalación vigente está
en `docs/INSTALLATION.md`; los informes de investigación anteriores son historia,
no instrucciones para repetir comandos con sus IDs locales.

## Objetivo y decisiones del usuario

Aplicación Windows local de imagen a geometría imprimible: ComfyUI/Hunyuan →
GLB base → UltraShape opcional → GLB refinado → STL escalado. Interfaz en español
y lenguaje sencillo. El usuario prioriza flores y anatomía fieles, acepta horas
de cálculo y descartó expresamente Blender como parte del flujo. No introducirlo
como dependencia ni solución manual por defecto; `render_model.py` es legado.

El resultado con imágenes retocadas por IA fue aceptado visualmente el 2026-10-29.
Preservar ese referente y sus parámetros; no confundir aprobación visual con
validación de espesores. El lobito poligonal nuevo terminó, pero no tiene aún
aceptación visual registrada. Los modelos son figuras de ejemplo, no una
restricción universal de lo que puede generar la aplicación.

## Mapa del proyecto

- `app/main.py`: API FastAPI, cola local, subida, historial, exportación y estáticos.
- `app/workflows.py`, `profiles.py`, `fidelity.py`: grafo Hunyuan, perfiles y ajustes.
- `app/progress.py`: eventos WebSocket ComfyUI y progreso por etapa.
- `app/refinement.py`: creación de proyectos UltraShape y proceso aislado.
- `app/job_control.py`: cancelación persistente, propietarios de procesos y grupos.
- `app/persistence.py`: JSON atómico con temporales únicos y reintentos de Windows.
- `app/regeneration.py`: nuevos intentos conservando imágenes y parámetros.
- `app/reference_preparation.py`: reconocimiento conservador de la lámina conocida
  y limpieza de alfa para una referencia de objeto conectado.
- `comfy_nodes/forma_mesh/`: extractor Lewiner y volumen consultado por lotes en RAM.
- `scripts/refine_ultrashape.py`: carga CPU/BF16, offload, refinamiento y extracción.
- `scripts/run_hybrid_fidelity.py`: comparaciones históricas y ejecución de un
  diseño nuevo con `--reference-directory` y `--name`.
- `scripts/prepare_ultrashape_runtime.py`: adaptaciones auditadas a fuente fijada.
- `scripts/sequential_cfg.py`, `ultrashape_compat.py`: CFG por ramas y SDPA.
- `frontend/src`: React/Three.js. `frontend/dist` se compila, no se versiona.
- `config/approved-generation.json`: preset transferible del flujo aceptado.
- `assets/references/`: ejemplos preparados y hashes; originales de experimentos
  y proyectos completos permanecen localmente en `data/`.
- `tests/`: pruebas sin GPU ni motores reales. `.github/workflows/ci.yml`: Windows CI.

## Instalación y rutas

Tres entornos separados: `.venv` (Python 3.11 web/CPU), portable ComfyUI
`C:/_IA/ComfyUI_windows_portable` (Python 3.12/PyTorch cu126) y
`C:/_IA/envs/ultrashape` (Python 3.11/PyTorch 2.5.1+cu121). No mezclar pip/torch.
Pesos y cachés bajo `C:/_IA`. No asumir que existen los IDs históricos en otra PC.
El código obtiene en general su raíz desde `__file__`, pero motores/modelos usan
rutas `C:/_IA` explícitas. Las utilidades de la primera figura son específicas.

ComfyUI: `127.0.0.1:8188`. Web: `0.0.0.0:8000`, sin autenticación y con regla LAN
opcional. No abrir ComfyUI a la red ni habilitar acceso desde Internet por defecto.
Para diagnóstico leer `/api/health`, `/queue`, JSON/logs y procesos; nunca deducir
que no hay cálculo porque la cola de ComfyUI esté vacía: UltraShape va aparte.

## Contratos de datos y ejecución

Cada intento tiene `data/projects/<id>/project.json`, imágenes, GLB original,
historial/ajustes y STL independientes. Estados: `queued`, `running`, `stopping`,
`cancelled`, `ready`, `error`. `ready` exige resultado real, no solo salida sin
excepción. No renombrar/reescribir GLB ni borrar resultados al regenerar.

Los grupos se describen en `data/experiments/<id>/experiment.json`. `worker.json`
registra el propietario y `cancel.request.json` impide que continúen etapas o que
progreso tardío reemplace una cancelación. Los trabajadores externos conservan
su recuperación; el arranque web no debe reanudarlos como trabajos ComfyUI propios.

- No ejecutar dos cálculos GPU simultáneos. Revisar todos los estados activos y
  la cola del motor. Mantener `stopping` bloqueando nuevas generaciones hasta confirmar.
- Detener el ejecutor del grupo antes de sus hijos; cancelar también las etapas
  pendientes. Seleccionar procesos por módulo, directorio, proyecto y propietario;
  proteger frente a PID reutilizado. Nunca matar todos los Python ni los servicios
  al cancelar un proyecto.
- Usar la cancelación ComfyUI por ID (`/api/jobs/{prompt_id}/cancel`) del portable
  probado; no interrupción global ni limpieza de colas ajenas.
- Reiniciar solo lo necesario para activar cambios. El cierre de la web no implica
  que termine un refinador. No interrumpir cálculos del usuario por una actualización.
- Progreso real de bloques/pasos/lotes, siempre por etapa. No inventar porcentajes
  globales ni anunciar que se terminará en un plazo sin evidencia suficiente.
- Escribir snapshots compartidos con `write_json`; el WinError 5 por reemplazar
  JSON interrumpió un cálculo largo y hasta ocultó su error original. No volver
  a introducir un temporal fijo compartido o escritura no atómica en esos estados.

API principal: `POST /api/projects`, `GET /api/projects`,
`GET /api/projects/{id}`, `POST /{id}/stop`, `POST /{id}/regenerate`,
`POST /{id}/refine`, `POST /{id}/export` y `GET /{id}/files/{filename}`,
estos últimos bajo `/api/projects`. Mantener la lista permitida de descargas.

## Reglas de geometría y calidad

- Hunyuan 2mv acepta vistas etiquetadas; 2.1 en este flujo solo acepta frontal y
  debe rechazar vistas extra, no ignorarlas. No añadir condicionamiento textual
  inexistente al generador de mallas.
- UltraShape recibe directamente frontal y malla. El dorso entra a través de la
  malla base, no como otra imagen del refinador. Mostrar esta distinción.
- Preset aceptado en `config/approved-generation.json`; la referencia local de
  `data/approved-reference.json` puede prevalecer en la instalación original.
  El botón exploratorio de refinamiento tiene otros valores: no confundirlos.
- Conservar semillas, parámetros, imágenes usadas y procedencia por proyecto.
  No aumentar latentes o resolución arbitrariamente ni presentar densificación
  como detalle aprendido. No prometer que low-poly de una imagen se conserve
  exactamente en la malla generada.
- No retirar componentes, pétalos ni fragmentos automáticamente. La limpieza de
  pieza principal es una opción explícita de la exportación y no modifica el GLB.
- Cierre de malla, millones de caras y uso alto de GPU no demuestran parecido,
  grosor suficiente ni imprimibilidad. 100 mm fue una medida provisional de ejemplo.

## Imágenes y precedentes importantes

Los frentes/dorsos IA se crearon con el editor integrado de ChatGPT, no ComfyUI
ni un modelo descargado localmente. Es opcional y no está integrado a la API.
Conservar originales generados, prompts y referencias preparadas por separado.
No separar una lámina desconocida con recortes fijos del zorro original.

El primer dorso del lobito inventó una segunda cola que envolvía la espalda,
aunque la única cola estaba delante. El usuario lo señaló: se detuvo el cálculo,
se editó solo el dorso y se reinició con `polygonal-wolf-v2`. Antes de encolar,
inspeccionar ambas imágenes: identidad, silueta, orientación y oclusión de cola,
flores, patas y orejas. Una vista trasera no es espejar el frente ni duplicar
objetos ocultos. Ver la skill y los prompts conservados.

## Comprobaciones antes de entregar cambios

```powershell
.venv\Scripts\python.exe -m pytest -q
Push-Location frontend
npm.cmd ci
npm.cmd run build
Pop-Location
```

No lanzar generaciones caras para verificar documentación o cambios pequeños.
Las pruebas de API no deben conectar al motor del usuario: usar los transportes
aislados existentes. Para atención/offload, ejecutar los verificadores del
entorno UltraShape que correspondan; probar compatibilidad en cada GPU nueva.

No versionar `.venv`, `node_modules`, `dist`, `data`, pesos, cachés, tokens ni
exportaciones pesadas. Git no sustituye el respaldo de resultados locales.
No elegir una licencia general para el código sin instrucción del propietario;
conservar la procedencia y licencias de terceros. El usuario puede autorizar
publicación o commits durante la tarea; este archivo no impone aprobaciones extra.
