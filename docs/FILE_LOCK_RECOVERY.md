# Recuperación del refinamiento por bloqueo del archivo de avance

El experimento `ed24ca06c037428da9761ec9c6cfd291` completó las dos mallas
Hunyuan multivista y la prueba de capacidad de 32768 latentes. UltraShape
se interrumpió en el intento `3964ba5201ea46a387842fce8d6d8754` durante
el segundo paso de difusión: `PermissionError: [WinError 5]` al reemplazar
`project.json`. No fue un error de memoria CUDA. El mismo bloqueo impidió
guardar el mensaje de error, por lo que el supervisor mostró un error genérico.

Se añadió guardado JSON atómico compartido con temporales únicos y reintentos
limitados para bloqueos de Windows. Los lectores conservan el último JSON
completo hasta el reemplazo. Si el problema persiste, se conserva el error;
no se publica un resultado como terminado. El manejador del refinador conserva
la excepción original aunque también falle la escritura del estado de error.

El ejecutor admite `--resume ID`: conserva las mallas base terminadas y la
capacidad validada, omite refinamientos terminados y crea nuevos intentos para
los pendientes. El intento fallido, sus registros y los resultados anteriores
permanecen disponibles. La reanudación mantiene 50 pasos, 32768 latentes,
CFG secuencial y extracción a 512; no implica una mejora artística confirmada.

Verificación: 45 pruebas superadas. Incluyen un bloqueo real de lectura en
Windows, reintentos simulados, conservación del último estado ante un bloqueo
persistente y reanudación sin repetir bases, pruebas de capacidad ni
refinamientos terminados.

El registro de la reanudación está en
`data/logs/hybrid-fidelity-resume-filelock-20261028.log`.
La valoración visual y la finalización del refinamiento siguen pendientes.

Nuevo intento: `39557c326fca4b13bb55991f0db48f52`. Se comprobó avance real
hasta 63/2100 bloques, superando los 62/2100 donde falló el intento anterior,
con estado `running` y sin error. La página por la red respondió HTTP 200.
