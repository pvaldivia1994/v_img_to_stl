# Procedencia y componentes de terceros

El repositorio contiene código propio de integración, adaptación y pruebas, y
archivos de referencia de las herramientas utilizadas. El propietario todavía
no ha seleccionado una licencia general para el código de la aplicación.
No se atribuye una licencia común a todos los pesos y componentes.

| Componente | Fuente y notas |
|---|---|
| ComfyUI | [Comfy-Org/ComfyUI](https://github.com/Comfy-Org/ComfyUI), portable v0.43.0 separado del repositorio |
| Flujos Hunyuan | [Ejemplos Comfy-Org](https://github.com/Comfy-Org/example_workflows) y plantillas incluidas en el portable; ejemplos preservados en `workflows` |
| Hunyuan3D 2.0 / 2mv | [Tencent Hunyuan3D-2](https://github.com/Tencent-Hunyuan/Hunyuan3D-2), pesos descargados aparte; copia de licencia 2.0 en `HUNYUAN-LICENSE.txt` |
| Hunyuan3D 2.1 | [Tencent Hunyuan3D-2.1](https://github.com/Tencent-Hunyuan/Hunyuan3D-2.1), checkpoint integrado publicado por Comfy-Org |
| UltraShape | [PKU-YuanGroup/UltraShape-1.0](https://github.com/PKU-YuanGroup/UltraShape-1.0), fuente fijada y parches auditados; revisar su LICENSE en esa revisión y la licencia de los pesos enlazados |
| DINOv2 | [facebook/dinov2-large](https://huggingface.co/facebook/dinov2-large), configuración del encoder; sus pesos están incluidos en UltraShape |
| Fondo | [rembg](https://github.com/danielgatis/rembg) y U2Net; ejecución CPU opcional |
| Web y geometría | FastAPI, React, Vite, Three.js, trimesh, scikit-image, NumPy y demás dependencias con sus licencias respectivas |

Los modelos Hunyuan y la fuente UltraShape tienen condiciones específicas;
consultar sus archivos LICENSE y model cards antes de redistribuir pesos o
decidir usos comerciales. No se copian pesos a GitHub. Los enlaces identifican
la procedencia y no sustituyen esos textos.

La lámina original `Zorro Durmiente en Luna Creciente.png` fue aportada para el
proyecto y se utiliza como referencia y fixture de regresión. Su autoría/licencia
no se ha determinado en esta sesión. Las imágenes de `assets/references` se
prepararon con el generador integrado de ChatGPT; sus prompts están documentados.
Ninguna de esas referencias se presenta como geometría calibrada o como propiedad
de los autores de los motores de reconstrucción.
