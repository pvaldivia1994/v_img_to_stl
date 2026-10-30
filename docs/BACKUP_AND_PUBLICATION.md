# Qué incluye GitHub y cómo respaldar el trabajo

## Incluido en el repositorio

Código Python y React, nodo ComfyUI propio, flujos JSON/ejemplo oficial, pruebas,
archivos de dependencias, lanzadores, guías y prompts. La imagen original de
referencia y las imágenes preparadas seleccionadas se incluyen para pruebas
y reproducción de entradas. `assets/references` contiene las referencias
aceptadas y las del lobito con dorso corregido, junto con sus hashes.

`config/approved-generation.json` es el preset público y transferible. Sus IDs
históricos aportan trazabilidad; no necesitan existir para generar otro diseño.
La skill vive en `.agents/skills/prepare-3d-references/SKILL.md` y AGENTS.md indica
cuándo leerla; no contiene claves ni depende de la ruta del perfil del autor.

## Excluido de Git, conservado localmente

- `.venv`, `node_modules`, `frontend/dist` y cachés.
- `data/`: proyectos, GLB/STL, latentes, campos de volumen, logs, manifiestos de
  procesos, solicitudes de cancelación y aceptación local.
- Pesos `.pt/.onnx/.safetensors`, archivos comprimidos y los motores bajo `C:\_IA`.
- `.env`, variantes de `.env`, tokens y claves.

Esto evita una clonación de decenas de GB y archivos que excedan los límites
habituales de GitHub. **Publicar el código no es un respaldo de las mallas**.
No forzar la inclusión de un checkpoint o de toda la carpeta `data` para migrar.

## Migrar los resultados a otra PC

1. Detener cálculos con el botón correspondiente; comprobar que no quede un
   refinador independiente. Cerrar servicios antes de tomar una copia consistente.
2. Copiar `data/projects` completo a un respaldo externo si se necesitan todos
   los modelos; incluir imágenes, `project.json`, GLB, reportes y STL. Opcionalmente
   copiar `data/experiments`, referencias IA originales, logs y manifiesto de
   referencia aceptada para conservar la procedencia.
3. En el equipo nuevo reconstruir los entornos siguiendo INSTALLATION.md y
   colocar los proyectos bajo su propia carpeta `data/projects`.
4. No reanudar ciegamente estados `running/queued/stopping`, `worker.json` o grupos
   de otra máquina. Los PID y trabajos ComfyUI anteriores no son válidos allí.
   Resolver esos estados como intentos interrumpidos o conservarlos como archivo,
   y usar Regenerar para un intento nuevo con sus entradas.
5. Los campos de reporte pueden contener rutas absolutas históricas: conservarlos
   como procedencia; las descargas actuales se resuelven por proyecto y archivo.

Para guardar solo un resultado elegido, copiar su carpeta completa y documentar
qué malla base y referencias utilizó. Los pesos se pueden copiar verificando SHA256
o descargar otra vez; no copiar entornos Python, ni un marcador `forma-validated.json`
ajeno como si certificara la GPU nueva.

## Publicación inicial

Destino solicitado: `https://github.com/pvaldivia1994/v_img_to_stl.git`.
La revisión previa a publicación debe confirmar exclusiones, ausencia de secretos,
tamaños de archivos, pruebas y compilación. No se ha elegido una licencia general
del código: la publicación no relicencia componentes ni pesos de terceros.
Después de subir, verificar que el commit remoto coincide y que las guías y assets
están en el repositorio. El estado de CI remoto se informa solo después de leerlo;
las pruebas locales no equivalen a un CI ya completado.
