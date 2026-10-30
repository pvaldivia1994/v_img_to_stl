# Instalación completa en otra PC

Guía vigente de publicación, 2026-10-30. Los informes de experimentos anteriores
son históricos. Las versiones y hashes medidos están en
[MODELS_AND_HARDWARE.md](MODELS_AND_HARDWARE.md).

## 1. Requisitos y distribución de carpetas

Configuración validada: Windows, NVIDIA RTX 3050 8 GB, 64 GB RAM, SSD.
Tener más VRAM puede reducir transferencias; no se han medido otras GPU.
No hay un modo completo de generación solo CPU validado. Linux/macOS requieren
adaptar las rutas, los lanzadores y probar su compatibilidad por separado.

Instalar desde sus fuentes oficiales:

- [Git para Windows](https://git-scm.com/downloads/win).
- [Python 3.11 x64](https://www.python.org/downloads/), incluido el lanzador `py`.
- [Node.js](https://nodejs.org/en/download): usar la rama 22, versión 22.12 o posterior.
- [7-Zip](https://www.7-zip.org/download.html).
- [Controlador NVIDIA](https://www.nvidia.com/Download/index.aspx) compatible con
  CUDA 12.6 del portable y CUDA 12.1 de UltraShape. La referencia registrada usó
  driver 610.88; no se ha establecido mediante pruebas un driver mínimo.
- Un laminador para revisar el STL, por ejemplo el que ya utilice la impresora.
  Blender, Visual Studio C++, CUDA Toolkit y flash-attn no son necesarios para
  la ruta de inferencia adaptada descrita aquí.

Internet es necesario durante instalación/descarga. Los modelos quedan locales;
el editor de imágenes integrado de ChatGPT es un servicio separado y opcional.

```text
C:\_Github\v_img_to_stl\            código de esta aplicación
  .venv\                          Python 3.11 de la web/CPU
  frontend\dist\                  interfaz compilada localmente
  data\                           proyectos, resultados y logs; fuera de Git
C:\_IA\
  downloads\                      archivos descargados
  ComfyUI_windows_portable\        Python GPU independiente + ComfyUI
  UltraShape-1.0\                  fuente fijada y adaptaciones auditadas
  envs\ultrashape\                 segundo Python 3.11 para el refinador
  models\checkpoints\              Hunyuan 2.0, 2mv y 2.1 opcional
  models\ultrashape\               pesos UltraShape + configuración DINO
  models\background\              U2Net opcional
  cache\                          cachés HF/Torch/pip/Numba
```

Los valores `C:/_IA` están hoy en `app/refinement.py`, `scripts/refine_ultrashape.py`,
`prepare_ultrashape_runtime.py`, descargadores, `remove_background.py` y
`start-comfy.ps1`. Para otra unidad, actualizar todos esos puntos coherentemente;
no basta con mover los pesos. No copiar los entornos virtuales entre equipos.

## 2. Clonar y preparar la web

Desde PowerShell:

```powershell
git clone https://github.com/pvaldivia1994/v_img_to_stl.git C:\_Github\v_img_to_stl
Set-Location C:\_Github\v_img_to_stl
New-Item -ItemType Directory -Force C:\_IA\downloads,C:\_IA\models\checkpoints,C:\_IA\models\ultrashape,C:\_IA\cache | Out-Null
py -3.11 -m venv .venv
.venv\Scripts\python.exe -m pip install -r requirements.lock.txt
.venv\Scripts\python.exe -m pip check
Push-Location frontend
npm.cmd ci
npm.cmd run build
Pop-Location
```

`requirements.lock.txt` es la instantánea del entorno de aplicación validado.
`requirements.txt` declara sus dependencias directas; usar la instantánea para
reconstrucción y actualizar versiones solo con verificaciones posteriores.
No instalar este archivo en el Python portable ni en el entorno UltraShape.

## 3. ComfyUI portable y modelos Hunyuan

1. Descargar el [portable NVIDIA cu126 de ComfyUI v0.43.0](https://github.com/Comfy-Org/ComfyUI/releases/download/v0.43.0/ComfyUI_windows_portable_nvidia_cu126.7z).
   Archivo de 1.930.972.692 bytes. SHA256 del release:
   `691dcb5295e73594c6530ff7f3fca8dbe7dfb45114b951328c5dd3df0fff6c6b`.
   Verificar con `Get-FileHash -Algorithm SHA256 RUTA_AL_ARCHIVO`.
   `python -m scripts.download_portable` es un descargador alternativo por rangos;
   comprueba tamaños y rangos HTTP, pero el hash del archivo debe comprobarse aparte.
2. Extraer en `C:\_IA` conservando la carpeta `ComfyUI_windows_portable`.
   No extraer encima de otra instalación personalizada.
3. Descargar los dos checkpoints iniciales de la [tabla de modelos](MODELS_AND_HARDWARE.md),
   verificar sus hashes y guardarlos con estos nombres exactos:

   ```text
   C:\_IA\models\checkpoints\hunyuan3d-dit-v2.safetensors
   C:\_IA\models\checkpoints\hunyuan3d-dit-v2-mv.safetensors
   ```

   El primero permite el modo de una imagen y es el archivo que verifica el
   configurador; el segundo permite el frente/dorso del flujo aceptado.
4. Instalar el extractor y registrar las rutas:

   ```powershell
   C:\_IA\ComfyUI_windows_portable\python_embeded\python.exe -s -m pip install scikit-image==0.26.0
   .venv\Scripts\python.exe -m scripts.configure_comfy
   ```

   El configurador comprueba el SHA256 de Hunyuan 2.0, crea
   `ComfyUI/extra_model_paths.yaml` y copia `comfy_nodes/forma_mesh` a
   `ComfyUI/custom_nodes/forma_mesh`. Si ya existe una configuración de rutas
   distinta, se detiene para revisarla; no debe sobrescribirse a ciegas.
5. Reiniciar ComfyUI después de instalar o actualizar ese nodo. El lanzador usa
   `--lowvram --preview-method none`, puerto 8188 y escucha local.

El portable incluye Python 3.12 y su PyTorch CUDA. **No sustituir sus dependencias
con las de la web o las de UltraShape.** `docs/comfy-requirements.lock.txt` es un
inventario del portable, con rutas de construcción `file:///D:/a/...`; no es un
archivo instalable en otra PC. La fuente reproducible de ese entorno es el archivo
portable verificado, más `scikit-image` y el nodo propio.

Hunyuan3D 2.1 es opcional:

```powershell
.venv\Scripts\python.exe -m scripts.download_hunyuan21
```

Utiliza su checkpoint separado y una sola imagen. No reemplazar el modelo 2mv
por 2.1 esperando conservar la entrada trasera. En la GPU de 8 GB es experimental.

## 4. Primer arranque y generación base

Abrir `Iniciar.cmd`; inicia web y motor si no están activos. También se pueden
usar terminales separadas desde la raíz:

```powershell
powershell -ExecutionPolicy Bypass -File scripts\start-comfy.ps1
```

```powershell
.venv\Scripts\python.exe -m uvicorn app.main:app --host 0.0.0.0 --port 8000
```

Abrir [la web local](http://127.0.0.1:8000/) y esperar «ComfyUI listo». Para una
prueba base, usar `assets/references/approved-fox/front.png` y `back.png`, activar
varias vistas y desactivar preparación de fondo. El modelo multivista debe estar
disponible. La barra debe avanzar y producir un proyecto `ready` con GLB.

La eliminación de fondo es opcional y funciona en CPU. La primera ejecución
descarga U2Net completo a `C:\_IA\models\background` desde el release oficial de
[rembg](https://github.com/danielgatis/rembg/releases). Se puede preparar antes:

```powershell
.venv\Scripts\python.exe -m scripts.remove_background MI_IMAGEN.png IMAGEN_PREPARADA.png
```

No se necesita U2Net para las referencias ya preparadas del repositorio.

## 5. UltraShape: instalación opcional para el flujo completo

Crear un entorno **nuevo**, separado de los dos anteriores. Los siguientes
comandos de clonado son para una carpeta que todavía no exista:

```powershell
git clone https://github.com/PKU-YuanGroup/UltraShape-1.0.git C:\_IA\UltraShape-1.0
git -C C:\_IA\UltraShape-1.0 checkout 5e8dcef05df101ab00ab6cd5fdd0ed0c74fbca66
py -3.11 -m venv C:\_IA\envs\ultrashape
C:\_IA\envs\ultrashape\Scripts\python.exe -m pip install torch==2.5.1 torchvision==0.20.1 --index-url https://download.pytorch.org/whl/cu121
C:\_IA\envs\ultrashape\Scripts\python.exe -m pip install -r requirements-ultrashape.lock.txt
C:\_IA\envs\ultrashape\Scripts\python.exe -m pip check
.venv\Scripts\python.exe -m scripts.download_ultrashape
.venv\Scripts\python.exe -m scripts.prepare_ultrashape_runtime
```

El último comando aplica cambios pequeños auditados a la revisión fijada y
descarga únicamente `config.json` de DINOv2-large. Si la fuente no coincide,
se detiene: no aplicar parches por reemplazo indiscriminado. La procedencia queda
en `C:\_IA\UltraShape-1.0\forma-runtime.json`. Los pesos completos de UltraShape
ya incluyen el encoder DINO; no se necesita descargar otra copia de sus pesos.

Las adaptaciones evitan módulos de entrenamiento y postprocesado que aquí no
se usan, permiten inferencia sin cubvh/flash-attn y fijan el muestreo aleatorio.
El extractor utilizado es Lewiner en CPU; no se ha instalado DMC/diso.

Verificar CUDA y las operaciones adaptadas:

```powershell
C:\_IA\envs\ultrashape\Scripts\python.exe -c "import torch; print(torch.__version__, torch.cuda.is_available(), torch.cuda.get_device_name(0), torch.cuda.is_bf16_supported())"
C:\_IA\envs\ultrashape\Scripts\python.exe -m scripts.check_ultrashape_attention
C:\_IA\envs\ultrashape\Scripts\python.exe -m scripts.check_sequential_cfg
C:\_IA\envs\ultrashape\Scripts\python.exe -m scripts.check_ultrashape_cache
```

## 6. Prueba de compatibilidad en la GPU nueva

Primero generar una malla base terminada desde la web (sección 4). Sin otro
cálculo activo, sustituir `ID_MALLA_BASE` por su ID real:

```powershell
C:\_IA\envs\ultrashape\Scripts\python.exe -m scripts.refine_ultrashape ID_MALLA_BASE --validation-only --steps 2 --latents 32768 --resolution 32 --chunks 512 --sequential-cfg
```

Esta prueba oculta de diagnóstico crea un proyecto independiente. Solo si
termina correctamente escribe `forma-validated.json` en la fuente UltraShape;
entonces la web habilita el refinador. **No copiar el marcador validado de otra
PC para saltarse esta prueba.** Dos pasos y resolución 32 prueban compatibilidad,
no calidad de flores. Si 32768 no cabe, probar 16384 por separado y conservar
ese resultado; no afirmar que el preset 32768 está validado en ese equipo.

## 7. Generación completa y referencias nuevas

```powershell
.venv\Scripts\python.exe -u -m scripts.run_hybrid_fidelity --reference-directory assets\references\approved-fox --name "Figura de prueba"
```

El comando espera a que la GPU esté libre, genera con frente/dorso y después
ejecuta UltraShape con los ajustes aceptados. Para el lobito con dorso corregido,
cambiar el directorio a `assets\references\polygonal-wolf`.
Para otro diseño, preparar `front.png`, `back.png` y opcionalmente
`front-conditioning.png` (RGBA) en una carpeta propia y usar esa ruta.
Leer la [skill local](../.agents/skills/prepare-3d-references/SKILL.md) antes de
generar vistas: una espalda inventada o una cola duplicada perjudican la malla.

Este ejecutor no necesita los proyectos históricos: usa el preset versionado
cuando no existe `data/approved-reference.json`. No ejecutar los comandos de
informes históricos que contienen IDs de otra instalación.

## 8. Comprobaciones, red y respaldo

```powershell
.venv\Scripts\python.exe -m pip install -r requirements-dev.txt
.venv\Scripts\python.exe -m pytest -q
```

La suite de aplicación usa transportes de prueba y archivos temporales; no
descarga pesos ni inicia generaciones. Compilar además `frontend` tras cambios.

Para LAN, ejecutar `Habilitar-red.cmd` como administrador y consultar la IP
actual con `ipconfig`. La regla limita TCP 8000 al Python de esta aplicación,
la interfaz detectada y la subred local. La web no tiene autenticación. No abrir
8188 ni reenviar los puertos desde el router.

Usar el botón **Detener** para cancelar cálculos, y `Detener.cmd` para cerrar
servicios cuando no haya trabajo. Los entornos no se respaldan copiándolos:
reconstruirlos y migrar `data/` según [BACKUP_AND_PUBLICATION.md](BACKUP_AND_PUBLICATION.md).
