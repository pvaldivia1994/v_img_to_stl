# Flores, preparación de imagen y dorso: investigación y nuevas pruebas

28 de octubre de 2026. El objetivo sigue siendo reproducir la imagen, especialmente los pétalos y las patitas, sin Blender. Esta fase incorpora una preparación con IA y una malla base guiada por frente y espalda. No se afirma aún una mejora visual del STL: las nuevas generaciones están en cola.

## Hallazgos comprobados

1. **El refinamiento largo anterior todavía no terminó.** El proyecto `d019acb4fd3942c5abc9c0f379bb0183` seguía ejecutando UltraShape al preparar este informe. Las variantes de semillas y 75 pasos de Hunyuan sí habían terminado. No se debe evaluar una de esas mallas como si ya fuera la salida refinada.
2. **Una generación manual recibió la lámina completa.** `422e372381c643c89b1f8b606f1fe3da`, llamada `1000178089`, conserva una imagen con múltiples zorros, varias perspectivas y etiquetas. Esa entrada es ambigua para el generador de una sola vista. Las comparaciones automatizadas anteriores ya usaban un recorte; este hallazgo no explica todos sus defectos.
3. **La ampliación de píxeles tiene un límite.** El [encoder DINO de ComfyUI](https://github.com/Comfy-Org/ComfyUI/blob/master/comfy/image_encoders/dino2_large.json) usa entrada 518 y parches de 14 píxeles. Una imagen ampliada a 4K vuelve a reducirse para ese encoder. Puede ayudar limpiar el fondo o mejorar las señales visuales, pero la ampliación no equivale a recuperar geometría. La última frase es una inferencia del funcionamiento del encoder.
4. **UltraShape sí cambia la geometría, pero depende de la base.** Su [descripción oficial](https://github.com/PKU-YuanGroup/UltraShape-1.0) explica que refina en posiciones espaciales derivadas de la malla inicial. Si una flor quedó fusionada con la luna, la localización inicial limita la reconstrucción del detalle. Su [configuración](https://github.com/PKU-YuanGroup/UltraShape-1.0/blob/main/configs/infer_dit_refine.yaml) contiene 32768 latentes y encoder de imagen 1022; nuestras primeras pruebas usaban 16384 para contener memoria.

## Incorporación del dorso

El [ejemplo oficial Hunyuan3D-2mv](https://github.com/Tencent-Hunyuan/Hunyuan3D-2/blob/main/examples/shape_gen_multiview.py) introduce vistas etiquetadas de frente, izquierda y espalda. Nuestro checkpoint multivista ya está instalado. Hunyuan3D 2.1 y el `SingleImageEncoder` del UltraShape instalado no se convierten en modelos entrenados para dos cámaras añadiendo otro archivo o concatenando imágenes.

La cadena nueva es:

**Frente y espalda separados → Hunyuan3D-2mv → malla base multivista → UltraShape con frente y esa malla → GLB/STL.**

El dorso interviene en la construcción de la geometría base y, por esa vía, en los anclajes del refinador. No se presenta como una segunda imagen leída directamente por UltraShape, ni como garantía de que el refinador conserve exactamente toda la espalda. Ambas imágenes quedan guardadas y visibles para revisión. Las vistas de origen son ilustraciones con perspectiva, no fotografías calibradas; sus diferencias pueden producir ambigüedad.

## Preparación de referencia aplicada

Se usó el editor integrado de esta conversación `image_gen`, mediante la habilidad imagegen (no se instaló ese editor en la PC), para dos ediciones basadas en las vistas originales. Se pidieron las mismas proporciones, pose, silueta, flores y pétalos, con pintura rosa mate en los pétalos y ocre en sus centros, iluminación suave y fondo transparente. El propósito es probar si la separación visual ayuda al encoder a reconocer las flores. Es una hipótesis experimental, no una mejora demostrada por la bibliografía.

Los archivos generados fueron inspeccionados. Mantienen la composición principal y las tres flores del frente; la edición generativa puede alterar detalles finos. Por eso se mantiene un control con las referencias originales. El color solo sirve de señal en la imagen: no añade color ni relieve por sí mismo a un STL.

Los originales generados tenían píxeles sueltos en el alfa. Una preparación específica para esta figura aislada retiene su componente conectado principal, conserva el RGB y el alfa suave de sus bordes y la centra al 85%. Se guardan también los archivos crudos; no se aplica esta limpieza de componentes a las mallas ni a imágenes desconocidas.

Archivos finales:

- `C:\_Github\v_img_to_stl\data\ai-prepared-fox\front.png`
- `C:\_Github\v_img_to_stl\data\ai-prepared-fox\back.png`
- `front-conditioning.png` y `back-conditioning.png` en la misma carpeta conservan alfa para el refinador.
- `preparation.json` contiene hashes, recortes y limpieza de alfa.
- [Prompts completos y roles de cada entrada](IMAGE_PREPARATION_PROMPTS.md).

Se implementó reconocimiento de **esta lámina exacta**: el navegador la separa al seleccionarla y muestra el mensaje correspondiente. Usa tamaño y dos firmas de píxeles como identificación; la API incorpora además SHA256 de los píxeles. Las imágenes desconocidas no se recortan automáticamente. El cambio del navegador ya está activo sin reiniciar servicios y se comprobó seleccionando la lámina real: apareció solo el frente como imagen principal y el dorso en su entrada separada. La ruta de API nueva se carga en un arranque normal posterior; no hace falta reiniciar para estas pruebas.

## Lote programado y parámetros

Experimento: `2b9670edb19547deac01fe9b46b720a0`.

| Variante | Proyecto de malla base | Estado al preparar el informe |
|---|---|---|
| Referencias originales, frente y dorso | `f6cb0429d6b24fc780a973b7ef8393ba` | En cola |
| Referencias preparadas por IA, frente y dorso | `837cc0a985e1463f807bf39bb8e3bc17` | En cola |

Ambas bases usan el mismo modelo multivista, semilla 4007959359, encuadre 85%, 50 pasos, CFG 7,5, volumen 512 y extracción 0,50. Se generan en secuencia cuando termine el trabajo anterior. Después se comprueba UltraShape con 32768 latentes y dos pasos a resolución 32, para validar memoria. Esa prueba interna no se muestra como resultado artístico.

Se implementó CFG secuencial: la predicción condicionada y la no condicionada se calculan separadamente, conservando su combinación matemática. Reduce el lote simultáneo, a costa de tiempo. Su equivalencia se comprobó con tensores y condicionamiento anidado; **la prueba real de 32768 en GPU aún está pendiente de la cola**. Si la prueba falla por CUDA/memoria, el lote intenta 16384 y registra la reducción. Otros errores detienen el lote y se conservan sus mensajes.

Cada base se refinará con 50 pasos y volumen 512. Aquí se compara interpretación geométrica antes de repetir un volumen 768: una superficie más densa no asegura que aparezca un pétalo que el modelo interpretó mal. El experimento anterior a 768 se conserva como comparación independiente. No se reducen caras ni se borran fragmentos de la malla.

También se conservan aberturas reales en la máscara del refinador y solo se rellenan agujeros diminutos de brillos. Se corrigió el muestreador de superficie para que su generador NumPy dependa de la semilla, y se registró el parche en el manifiesto del entorno.

Seguimiento: `data/experiments/2b9670edb19547deac01fe9b46b720a0/experiment.json` registra el trabajo que espera, los proyectos, la validación de capacidad y los errores. Registro: `data/logs/hybrid-fidelity-20261028.log`. No se inició una segunda carga de GPU sobre el refinamiento activo.

## Otros modelos investigados

| Alternativa | Evidencia oficial | Decisión en esta fase |
|---|---|---|
| [TripoSG](https://github.com/VAST-AI-Research/TripoSG) | Generador diferente; publica requisito mínimo 8 GB. Su modo principal usa una imagen y su modo scribble usa dibujo y texto. | Candidato para una comparación posterior si esta cadena falla. No aporta directamente la entrada de dorso que necesitamos. No se descargó en esta fase. |
| [TRELLIS original](https://github.com/microsoft/TRELLIS/blob/main/example_multi_image.py) | Sí tiene inferencia de varias imágenes. Su README advierte que el algoritmo no se entrenó específicamente para multivista; el requisito publicado es 16 GB y la plataforma probada es Linux. | Alternativa real, pero requiere una adaptación adicional para este equipo. No se presume mejor resultado con nuestras vistas. |
| [TRELLIS.2](https://github.com/microsoft/TRELLIS.2) | Publica 24 GB y código probado en Linux. | No se presenta como reemplazo listo para esta GPU de 8 GB. |
| [Hunyuan3D-Omni](https://github.com/Tencent-Hunyuan/Hunyuan3D-Omni) | Acepta controles espaciales como puntos, vóxeles, caja y pose; publica 10 GB. | Puede guiarse por una forma inicial, pero esos controles no equivalen a recibir frente y dorso como fotografías. Sería otra integración, no una opción escondida del modelo instalado. |

## Validación y revisión pendiente

- 40 pruebas de aplicación superadas; incluyen separación conocida, protección de imágenes desconocidas, conservación del dorso y declaración de su uso indirecto.
- CFG secuencial verificado por comparación numérica y prueba de lote uno.
- Interfaz compilada; reconocimiento y separación comprobados en el navegador con la imagen real, sin enviar otro trabajo de GPU.
- Capturas de comprobación: `data/quality/contact-sheet-split.png` y `data/quality/hybrid-fidelity-queue.png`.
- Nuevas entradas inspeccionadas visualmente; originales conservados.
- [ ] Terminar UltraShape anterior y las nuevas bases multivista.
- [ ] Validar 32768 latentes en la GPU o registrar la reducción necesaria.
- [ ] Comparar las dos salidas refinadas: pétalos separados en cada flor, centros, unión con la luna, patitas y dorso.
- [ ] Elegir por parecido, no por número de caras. Preparar el STL elegido y revisar espesores en el laminador.
