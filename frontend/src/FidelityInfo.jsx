import React from 'react';

export default function FidelityInfo({project}) {
  if(!project?.comparison&&!project?.refinement&&!project?.experiment&&!project?.input_preparation)return null;
  const refinement=project.refinement;
  const source=refinement?.source_project||project.comparison?.source_project;
  const steps=refinement?.steps||project.prompt?.['3']?.inputs?.steps;
  const resolution=refinement?.resolution||project.prompt?.['61']?.inputs?.octree_resolution;
  return <details className="fidelity-info"><summary>{refinement?'Refinamiento con UltraShape':'Comparación de detalle'} · ver ajustes</summary>
    <p>{refinement?'La imagen y la malla inicial guían un segundo modelo de geometría. Revisa las flores y las patitas antes de elegir esta variante.':'Esta variante conserva la referencia y registra el cambio para poder comparar las flores, las patitas y la silueta.'}</p>
    {project.experiment&&<p>{project.experiment.variant}: se usan frente y espalda para construir la malla base. Después se refina con UltraShape. La referencia editada por IA es una prueba y puede cambiar detalles.</p>}
    {project.input_preparation&&<p>La lámina se separó en vistas antes de generar: {project.input_preparation.used_views.map(view=>view==='front'?'frente':'espalda').join(' y ')}.</p>}
    {refinement?.base_geometry_views?.includes('back')&&<p>La espalda guió la malla inicial. El refinador lee directamente la imagen frontal y esa malla; la espalda se conserva para comparar.</p>}
    <dl><dt>Pasos</dt><dd>{steps}</dd><dt>Resolución de superficie</dt><dd>{resolution}</dd>
      <dt>Semilla</dt><dd>{project.seed}</dd>{project.comparison?.occupancy&&<><dt>Ocupación de la imagen</dt><dd>{Math.round(project.comparison.occupancy*100)}%</dd></>}
      {refinement?<><dt>Capacidad de refinamiento</dt><dd>{refinement.latents.toLocaleString('es')} latentes</dd><dt>Superficie</dt><dd>Sin reducción de caras ni eliminación de fragmentos</dd></>:<><dt>Nivel de superficie</dt><dd>{project.prompt?.['62']?.inputs?.threshold}</dd></>}
    </dl>{source&&<a href={`/?project=${source}`}>Ver modelo de referencia →</a>}
  </details>;
}
