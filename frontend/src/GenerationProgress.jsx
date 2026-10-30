import React, {useEffect, useState} from 'react';

function duration(seconds){
  const value=Math.max(0,Math.floor(seconds));
  const hours=Math.floor(value/3600), minutes=Math.floor((value%3600)/60);
  return hours?`${hours} h ${minutes} min`:`${minutes} min ${value%60} s`;
}

export default function GenerationProgress({project}){
  const [now,setNow]=useState(Date.now()/1000);
  useEffect(()=>{const timer=setInterval(()=>setNow(Date.now()/1000),1000);return()=>clearInterval(timer);},[]);
  if(project?.status==='stopping')return <section className="generation-progress" aria-label="Progreso de generación"><strong role="status">Deteniendo la generación…</strong><p>Espera a que termine de detenerse para regenerar.</p></section>;
  if(!project||!['queued','running'].includes(project.status))return null;
  const progress=project.progress;
  const percent=Number.isFinite(progress?.percent)?progress.percent:undefined;
  const elapsed=now-(project.started_at||project.created_at);
  return <section className="generation-progress" aria-label="Progreso de generación">
    <div className="progress-heading"><strong aria-live="polite">{progress?.label||'Esperando información del motor'}</strong><span>{progress?`Etapa ${progress.stage_index} de ${progress.stage_count}`:'En curso'}</span></div>
    <progress aria-label={progress?.label||'Generación en curso'} max="100" value={percent}/>
    <div className="progress-details"><span>{percent===undefined?'Esta etapa no informa un porcentaje.':`${percent.toFixed(0)}% de esta etapa · ${progress.value.toLocaleString('es')} de ${progress.total.toLocaleString('es')}`}</span><span>{duration(elapsed)}</span></div>
    <p>{project.quality==='maximum'?'El modo de máximo detalle puede tardar bastante. ':''}Puedes cerrar esta pestaña y volver; mantén el equipo y los servicios encendidos.</p>
    {project.batch&&<p>Comparación {project.batch.index} de {project.batch.total}. {project.batch.next}</p>}
    {project.scheduler_only&&<p>Este trabajo está en espera. Comenzará cuando quede libre la GPU; el refinamiento que ya estaba en curso sigue trabajando.</p>}
    {project.progress_connection==='reconnecting'&&<p role="status">Reconectando el seguimiento. La generación puede seguir trabajando.</p>}
  </section>;
}
