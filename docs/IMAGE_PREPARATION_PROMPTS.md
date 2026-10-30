# Prompts de la preparación de referencia

Herramienta: editor integrado `image_gen`, modo edición, fondo transparente. Se utilizó el editor de imágenes de esta conversación; ese editor no se instaló en la PC. No se solicitó una clave API. La generación de mallas 3D y su refinamiento continúan en la PC. Las dos referencias finales se copiaron al proyecto y se prepararon para el generador 3D; los originales generados se conservan.

## Frente

Entrada de edición: `C:\_Github\v_img_to_stl\data\multiview-fox\front-source.png`.

Salida final: `C:\_Github\v_img_to_stl\data\ai-prepared-fox\front.png`. Salida con alfa: `front-conditioning.png` en la misma carpeta. Archivo generado crudo: `front-rgba.png`.

Prompt completo:

> Edit target: the supplied front-view reference image of an ivory sculpture of a sleeping baby fox curled on a crescent moon decorated with THREE flowers. Purpose: prepare a clearer input for image-to-3D geometry reconstruction, not a new design. Preserve the exact camera angle, object silhouette, proportions, fox pose, paws, ears, every ornamental curl, round pedestal, and the EXACT number, position, outline, individual petal count, overlap and center details of all three flowers. Do not add, remove or redesign geometry. Make only these appearance changes: remove the dark background to a truly transparent alpha background including the crescent opening; apply a subtle matte dusty rose paint to the existing flower petals and muted golden ochre only to their existing centers, making the boundaries of their solid raised petals clearly readable. Keep the entire fox, moon, pedestal and ornaments ivory. Clean diffuse studio lighting with gentle side light revealing the existing petal relief and rounded paws, crisp clean edges and no shiny highlights, no hard cast shadows. Each flower must remain the SAME sculpture with individually visible smooth petals, not a printed floral decal. Preserve all existing detail, do not invent surface textures, do not thicken, move or enlarge flowers. Single isolated object, square image, full pedestal and moon tip in frame, roughly 85 percent occupancy, no labels, no collage, no extra views.

## Espalda

Entrada 1, objeto de edición: `C:\_Github\v_img_to_stl\data\multiview-fox\back-source.png`.

Entrada 2, guía de pintura/iluminación: `C:\_Github\v_img_to_stl\data\ai-prepared-fox\front-rgba.png`.

Salida final: `C:\_Github\v_img_to_stl\data\ai-prepared-fox\back.png`. Salida con alfa: `back-conditioning.png` en la misma carpeta. Archivo generado crudo: `back-rgba.png`.

Prompt completo:

> Image 1 is the EDIT TARGET: the actual REAR view of a physical ivory sculpture of a curled sleeping baby fox on a decorated crescent moon. Image 2 is a supporting paint/lighting reference of the SAME sculpture viewed from the front. Return ONLY an enhanced version of image 1, a SINGLE REAR VIEW, never a collage. Preserve the exact rear camera, all proportions, rear silhouette, round pedestal, moon tip direction to the LEFT, fox rear fur and back of ears, ornamental curls and the exact number, positions, overlapping petals and outlines of all original flowers visible in image 1 including petal backs partly hidden behind the moon. Do NOT rotate the object toward the front. Do NOT expose the fox face or front paws. Preserve all sculpture geometry. Use image 2 only to match the subtle matte dusty rose paint of flower petals and muted golden ochre flower centers, with the whole fox, moon, pedestal, curls remaining ivory. Apply this paint only to existing flowers, do not invent more flowers. Gently improve clarity and soft diffuse side lighting to show solid petal relief. This is a reference for faithful image-to-3D reconstruction, so do not redesign details or alter geometry. Remove the dark backdrop to a clean truly transparent alpha background, with absolutely no speckles, floating pixels or stray artifacts, retain openings between moon and fox. Full object with tip and pedestal visible, centered square with 85 percent occupancy, no text.

Los prompts describen las restricciones solicitadas; no certifican que un editor generativo conserve cada detalle exactamente. La comparación 3D con la referencia original permanece obligatoria para decidir cuál variante se aproxima más al diseño.
