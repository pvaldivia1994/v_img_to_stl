# Detener y regenerar

Los dos botones aparecen debajo del nombre del proyecto.

- **Detener** se activa para trabajos en espera, en ejecución o pendientes de
  confirmar su detención. Cambia a «Deteniendo» mientras cierra los procesos
  del cálculo y comprueba la cola del motor. En una comparación cancela también
  sus trabajos pendientes y evita que el ejecutor lance la siguiente etapa.
  Conserva los modelos terminados, las imágenes, las exportaciones y los registros.
- **Regenerar** se activa cuando no hay cálculos en curso. Crea otro proyecto
  con las mismas imágenes, vistas, semilla, modelo y ajustes. Para UltraShape
  conserva la malla inicial y sus parámetros de refinamiento. Es un nuevo intento
  del proyecto seleccionado; no reinicia toda su comparación original.

Los intentos antiguos permanecen en el historial. Si el motor no confirma que
se detuvo, se muestra un aviso y se conserva el estado «Deteniendo». Se puede
volver a pulsar Detener; Regenerar permanece bloqueado para evitar dos cálculos
simultáneos. La aplicación y ComfyUI siguen encendidos.

## Implementación

`POST /api/projects/{id}/stop` registra una solicitud persistente, cancela las
tareas locales y termina únicamente los procesos Python de cálculo identificados
por su módulo, directorio, proyecto o registro de propietario. Verifica la fecha
de creación para registros con PID reutilizado. Detiene el ejecutor antes de sus
hijos y vuelve a comprobar nuevos hijos/etapas. Los servicios no son candidatos.
La cancelación de ComfyUI usa `/api/jobs/{prompt_id}/cancel`, que comprueba
atómicamente el identificador; no emplea una interrupción global ni borra toda
la cola. Las escrituras tardías no pueden sustituir un estado cancelado.

`POST /api/projects/{id}/regenerate` copia los datos de entrada a un directorio
nuevo. No copia resultados, errores, solicitudes de cancelación, registros de
procesos ni exportaciones. Conserva los ajustes de fidelidad y la preparación
de imagen; un refinamiento utiliza otra vez su `coarse.glb` exacto. El nuevo
intento queda separado del grupo anterior y registra `regenerated_from`.

Se añadió `psutil` al entorno de la aplicación para identificar los procesos.
Los entornos de ComfyUI y UltraShape permanecen separados; los trabajadores
solo importan este módulo al detener procesos desde la aplicación web.

## Verificación

- 55 pruebas automatizadas superadas, incluida cancelación de una comparación,
  protección de resultados previos, rechazo de regeneración con GPU ocupada,
  conservación de todas las vistas y parámetros, bloqueo de escrituras tardías,
  identificación de procesos y protección frente a PID reutilizado.
- Prueba de la llegada de una solicitud de detención durante la creación de
  una etapa: no queda un proyecto en espera sin ejecutor.
- Interfaz compilada y ambos botones verificados en el navegador.
- API de cancelación específica de ComfyUI verificada con un identificador de
  prueba inexistente (`cancelled: false`), sin detener un trabajo del usuario.
- Acceso por red comprobado con respuesta HTTP 200.

La comprobación de interfaz está en `data/quality/generation-controls.png`.
