# Modelos, descargas y hardware medido

Instantánea de las generaciones realizadas el 2026-10-28/29; publicación el
2026-10-30. Los hashes identifican los archivos usados, no cualquier archivo
con un nombre parecido. Los checkpoints se descargan aparte de Git.

## Pesos y fuentes

Todos los Hunyuan siguientes se guardan en `C:\_IA\models\checkpoints`.

| Modelo / nombre local exacto | URL del archivo usado | Bytes | SHA256 |
|---|---|---:|---|
| Hunyuan 2.0 / `hunyuan3d-dit-v2.safetensors` | [Tencent 2.0 FP16](https://huggingface.co/tencent/Hunyuan3D-2/resolve/main/hunyuan3d-dit-v2-0/model.fp16.safetensors) | 4.928.151.562 | `360bc281fc956d4acac0c3d36d5ec0ebf8cdddbf4b8892e894d12419388d479b` |
| Hunyuan 2mv / `hunyuan3d-dit-v2-mv.safetensors` | [Tencent 2mv FP16](https://huggingface.co/tencent/Hunyuan3D-2mv/resolve/main/hunyuan3d-dit-v2-mv/model.fp16.safetensors) | 4.928.151.562 | `d36f5881bcdc56726b73e517cd444c13c60732431622da7268145355c8d38e9c` |
| Hunyuan 2.1 / `hunyuan_3d_v2.1.safetensors` (opcional) | [Paquete Comfy-Org](https://huggingface.co/Comfy-Org/Hunyuan-3D-2.1/resolve/main/hunyuan_3d_v2.1.safetensors) | 7.365.943.290 | `5f21e98a6cb99b13b5e224abaee33929570fff7af2b6a0060001559a04ba9d72` |
| UltraShape / `C:\_IA\models\ultrashape\ultrashape_v1.pt` | [Checkpoint enlazado por UltraShape](https://huggingface.co/infinith/UltraShape/resolve/main/ultrashape_v1.pt) | 7.366.231.254 | `c96ae010c4169597fd0006dcb08056bf6104a1fca249b10fed7ddded324c3f0f` |

Verificar cada archivo con `Get-FileHash -Algorithm SHA256`. Un renombrado no
cambia el hash; una descarga parcial no es un checkpoint válido.

Descargas auxiliares:

- [ComfyUI portable NVIDIA cu126 v0.43.0](https://github.com/Comfy-Org/ComfyUI/releases/download/v0.43.0/ComfyUI_windows_portable_nvidia_cu126.7z),
  1.930.972.692 bytes, SHA256
  `691dcb5295e73594c6530ff7f3fca8dbe7dfb45114b951328c5dd3df0fff6c6b`.
- [Fuente UltraShape](https://github.com/PKU-YuanGroup/UltraShape-1.0), revisión
  `5e8dcef05df101ab00ab6cd5fdd0ed0c74fbca66`.
- [Configuración DINOv2-large](https://huggingface.co/facebook/dinov2-large/resolve/main/config.json):
  se guarda como `C:\_IA\models\ultrashape\dinov2-config.json`. SHA256 observado
  `11d68fe0b000b42314c9c8f7ecaf4f4c92ff95218578add56d8f5caabd1660df`.
  El preparador valida 1024 dimensiones y 24 capas. Los pesos DINO ya están en
  UltraShape; no descargar otra copia de ellos para este ejecutor.
- [U2Net completo](https://github.com/danielgatis/rembg/releases/download/v0.0.0/u2net.onnx),
  ~176 MB, opcional si se usa preparación de fondo. rembg lo guarda en
  `C:\_IA\models\background`. U2NetP (~4,6 MB) quedó como alternativa de pruebas;
  no fue la preparación final elegida.
- [Ruedas PyTorch CUDA 12.1](https://download.pytorch.org/whl/cu121) para el entorno
  UltraShape. Los comandos exactos están en la instalación.

No se descargaron modelos de texturizado Hunyuan Paint para este flujo STL.
TripoSG, TRELLIS/TRELLIS.2, Omni y otros modelos fueron investigados, no instalados
ni presentados como resultados medidos de esta aplicación.

## Entornos efectivos

| Entorno | Versión registrada | Función |
|---|---|---|
| Web/CPU `.venv` | Python 3.11, paquetes en `requirements.lock.txt` | FastAPI, imágenes, exportación, control de procesos |
| Portable ComfyUI | v0.43.0, Python 3.12.10, PyTorch 2.14.1+cu126 | Hunyuan en CUDA y nodo propio |
| UltraShape aislado | Python 3.11, torch 2.5.1+cu121, torchvision 0.20.1+cu121 | Refinador en CUDA con BF16 y offload |
| Interfaz | React 19, Vite 7, Three.js; versiones en `frontend/package-lock.json` | Visor WebGL y controles |

No mezclar los tres entornos Python. `docs/runtime.json` registra el portable
que se utilizó. El inventario `docs/comfy-requirements.lock.txt` contiene rutas de
la máquina de construcción del portable y no sirve para reinstalar con pip.

## GPU y memoria

- GPU de todas las generaciones locales registradas: **NVIDIA GeForce RTX 3050,
  8192 MiB de VRAM**, arquitectura Ampere con BF16 compatible.
- RAM física del equipo: aproximadamente **64 GiB**. No se han validado como
  suficientes 16 o 32 GB para el refinamiento largo con estos ajustes.
- Controlador observado al publicar: **610.88**. No es una afirmación de mínimo.
- ComfyUI usa `--lowvram`. UltraShape inicia pesos en CPU, mantiene bloques en
  RAM y los lleva a CUDA por fases; VAE y encoder se ejecutan en etapas separadas.
- Durante una comprobación real de UltraShape: GPU al **100 %**, entre 5165 y
  5417 MiB globales ocupados, ~8,1 GiB de RAM residente del proceso y ~14,79 GiB
  de memoria privada comprometida. Son muestras puntuales, no mínimos ni picos.
- Windows puede clasificar la carga CUDA de este proceso como motor «3D» en
  sus contadores. Comprobar también `nvidia-smi`, VRAM y progreso del trabajador.
- La cola de ComfyUI puede estar vacía mientras UltraShape calcula: este último
  usa un proceso independiente, no un nodo que figure en esa cola.

Los requisitos upstream de geometría 2.1 son superiores a 8 GB (10 GB publicados
por Tencent); la ejecución aquí fue experimental con offload, no una garantía
para cualquier GPU de 8 GB. Mayor resolución o más pasos no garantizan fidelidad.

## Ajustes aceptados

### Malla base

Hunyuan3D-2mv, frente + dorso, 3072 latentes, semilla **4007959359**, 50 pasos,
CFG **7,5**, Euler/normal, flujo nativo ComfyUI; volumen **512**, lotes **2048**,
umbral normalizado **0,5**. Nodo propio `FormaVAEDecodeHunyuan3D` para consultas
en lotes y `FormaVoxelToMesh` para extracción Lewiner. No reducir caras ni
eliminar componentes automáticamente.

### Refinamiento

UltraShape: **50 pasos, 32768 latentes, CFG 5, semilla 42**, ramas CFG secuenciales,
extracción **512**, lotes **1024**, nivel bruto **0**. Atención completa con caché
K/V exacta, volumen en RAM y coordenadas float32 antes de Fourier. Usa frontal y
malla; el dorso condiciona la malla base, no un segundo encoder de imagen del refinador.

El preset transferible está en `config/approved-generation.json`. Los valores
del botón exploratorio de UltraShape (75/16384/768) son distintos deliberadamente
y se conservan registrados; usar el ejecutor documentado para el preset aceptado.

## Resultados registrados

| Resultado | Identificador histórico | Tiempo de esa etapa | Medición / estado |
|---|---|---:|---|
| Hunyuan 2.1 | `9cdb7cf5b3a54d93b5f13ca5456b0cfc` | 675,3 s | Terminó en 8 GB; hasta 7307 MiB observados por muestreo |
| UltraShape, figura aceptada | `6dd7d7413b1c4fdbbed159505530d82d` | 5975,9 s (~99,6 min) | Aceptación visual del usuario el 2026-10-29 |
| Base lobito poligonal con dorso corregido | `f965df99c83b4a84b3936a978911011d` | 574,7 s (~9,6 min) | Terminó |
| UltraShape lobito poligonal | `067996cb019e4b1bb083698b841111ba` | 5721,0 s (~95,4 min) | Terminó; aceptación visual pendiente |

En ambos refinamientos completos PyTorch registró **5009 MiB asignados** y
**7630 MiB reservados** como máximos de su asignador. No equivalen al consumo
global de todos los programas ni a «todo el modelo cabe simultáneamente».
El lobito final tiene 867043 vértices y 1734098 caras, malla cerrada y orientación
consistente según trimesh. Eso no certifica parecido ni espesores.

Los proyectos completos y sus pesos no se publican en Git; los IDs son trazabilidad
de la sesión original, no recursos que una instalación nueva pueda abrir.
