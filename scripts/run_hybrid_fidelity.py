"""Wait for existing work, then compare original/AI front+back and refine.

No GPU work starts while another project is active. Planned projects are
visible immediately; failure is persisted, never converted into success.
"""
import argparse
import asyncio
import json
from pathlib import Path
import shutil
import subprocess
import time
import uuid

import httpx
from PIL import Image
from app.main import DATA,COMFY,generate,save,read
from app.fidelity import frame_reference
from app.refinement import create_refinement,RUNTIME
from app.persistence import write_json
from app.job_control import check_cancelled, register_worker, JobCancelled, finish_cancelled

ROOT=DATA.parents[1]


def pending_project(variant, directory, experiment_id):
    path=DATA/uuid.uuid4().hex
    path.mkdir()
    for view in ('front','back'):
        with Image.open(directory/(view+'.png')) as image:
            frame_reference(image,.85).save(path/('input.png' if view=='front' else 'input-back.png'))
        shutil.copyfile(path/('input.png' if view=='front' else 'input-back.png'),path/('source.png' if view=='front' else 'source-back.png'))
    alpha=directory/'front-conditioning.png'
    if alpha.is_file():
        shutil.copyfile(alpha,path/'conditioning-front.png')
    record={'id':path.name,'name':f'Flores y dorso · {variant} · multivista',
        'created_at':time.time(),'status':'queued','worker':'hybrid-fidelity','scheduler_only':True,
        'seed':4007959359,'quality':'maximum','model_family':'hunyuan2','mode':'multiview',
        'views':{'front':'input.png','back':'input-back.png'},'remove_background':False,'exports':[],
        'fidelity_settings':{'steps':50,'threshold':.5,'num_chunks':2048},
        'experiment':{'id':experiment_id,'variant':variant,'image_preparation':str(directory),
            'stages':['Hunyuan3D-2mv: frente y dorso','UltraShape: imagen frontal y malla multivista'],
            'planned_refinement':{'latents':32768,'sequential_cfg':True,'steps':50,'resolution':512},
            'note':'Variante experimental. La edición IA puede alterar detalles; comparar con el original.'},
        'progress':{'stage':'waiting','stage_index':1,'stage_count':6,'label':'En espera: terminará primero el refinamiento actual',
                    'percent':None,'updated_at':time.time()}}
    save(path,record)
    return path,record


async def wait_for_gpu(own_ids, manifest, manifest_path):
    while True:
        check_cancelled(manifest_path.parent)
        active=[r for p in DATA.iterdir() if (p/'project.json').is_file()
                and (r:=read(p))['id'] not in own_ids and r.get('status') in ('queued','running')]
        async with httpx.AsyncClient(base_url=COMFY,timeout=30) as client:
            queue=(await client.get('/queue')).raise_for_status().json()
        manifest.update(state='waiting',waiting_for=[r['id'] for r in active],heartbeat=time.time())
        write_json(manifest_path,manifest)
        if not active and not queue.get('queue_running') and not queue.get('queue_pending'):
            # A worker can finish its record just before the CUDA context exits.
            await asyncio.sleep(5)
            return
        await asyncio.sleep(10)


async def refine_job(source, settings, name, validation=False, on_created=None):
    check_cancelled(source)
    path,record=create_refinement(source,DATA,settings,name)
    if validation:
        record['validation_only']=True
        save(path,record)
    if on_created:
        try:
            on_created(record)
        except JobCancelled:
            finish_cancelled(path)
            raise
    log=ROOT/'data/logs'/f'{path.name}-ultrashape.log'
    options={'creationflags':subprocess.CREATE_NO_WINDOW} if hasattr(subprocess,'CREATE_NO_WINDOW') else {}
    with log.open('ab') as output:
        process=await asyncio.create_subprocess_exec(str(RUNTIME),'-u','-m','scripts.refine_ultrashape',
            path.name,'--prepared',cwd=ROOT,stdout=output,stderr=output,**options)
        code=await process.wait()
    record=read(path)
    if code or record.get('status') != 'ready':
        if record.get('status') == 'cancelled':
            raise JobCancelled('Comparación detenida por el usuario.')
        if record.get('status') in ('queued','running'):
            record.update(status='error',error=f'El proceso terminó con código {code}. Consulta {log.name}.')
            save(path,record)
        return path,record
    return path,record


async def main(resume=None):
    experiment_id=uuid.UUID(resume).hex if resume else uuid.uuid4().hex
    plan_dir=ROOT/'data/experiments'/experiment_id
    plan_dir.mkdir(parents=True,exist_ok=bool(resume))
    manifest_path=plan_dir/'experiment.json'
    check_cancelled(plan_dir)
    register_worker(plan_dir)
    jobs=[]
    manifest={'id':experiment_id,'created_at':time.time(),'state':'preparing','projects':[],
        'purpose':'Comparar referencia original y preparada por IA con dorso en la malla base.'}
    if resume:
        manifest=json.loads(manifest_path.read_text(encoding='utf-8'))
        for item in manifest['projects']:
            if item['stage']=='base':
                path=DATA/item['id']
                record=read(path)
                if record.get('status')!='ready' or not (path/'original.glb').is_file():
                    raise RuntimeError('Solo se reanudan refinamientos con las mallas base terminadas.')
                jobs.append((path,record))
        if len(jobs)!=2:
            raise RuntimeError('El experimento debe contener sus dos mallas base.')
        if manifest.get('error'):
            manifest.setdefault('previous_errors',[]).append(manifest.pop('error'))
        manifest.pop('finished_at',None)
        manifest['resumed_at']=time.time()
    try:
        # The original is the control; both variants use identical framing/seed/profile.
        original=ROOT/'data/hybrid-original-fox'
        original.mkdir(exist_ok=True)
        for view in (() if resume else ('front','back')):
            with Image.open(ROOT/'data/multiview-fox'/(view+'.png')) as image:
                frame_reference(image,.85).save(original/(view+'.png'))
        for variant,directory in ([] if resume else [('Original',original),('Referencia IA',ROOT/'data/ai-prepared-fox')]):
            path,record=pending_project(variant,directory,experiment_id)
            jobs.append((path,record))
            manifest['projects'].append({'id':record['id'],'variant':variant,'stage':'base'})
        own_ids={r['id'] for _,r in jobs}
        print(json.dumps({'experiment':experiment_id,'base_projects':list(own_ids),'resumed':bool(resume)},ensure_ascii=True),flush=True)
        await wait_for_gpu(own_ids,manifest,manifest_path)
        for path,record in jobs:
            check_cancelled(plan_dir)
            if record['status']=='ready':
                continue
            manifest.update(state='generating',active_project=record['id'],heartbeat=time.time())
            write_json(manifest_path,manifest)
            record.pop('scheduler_only',None)
            record['progress']={}
            await generate(path,record)
            if record['status'] != 'ready':
                raise RuntimeError(record.get('error','Falló la malla multivista.'))
        # Validate the larger latent count before committing a full denoising run.
        settings={'steps':2,'latents':32768,'resolution':32,'chunks':512,'sequential_cfg':True,'seed':42}
        latents=manifest.get('validated_latents') if resume else None
        if not latents:
            check_cancelled(plan_dir)
            probe_path,probe=await refine_job(jobs[0][0],settings,'Diagnóstico 32768 · no imprimir',True)
            manifest['capacity_probe']={'id':probe['id'],'status':probe['status'],'error':probe.get('error')}
            latents=32768
        else:
            probe={'status':'ready'}
        if probe['status'] != 'ready':
            error=probe.get('error','').lower()
            if 'out of memory' not in error and 'cuda' not in error:
                raise RuntimeError('La prueba del refinador falló: '+probe.get('error','Revisa el registro.'))
            # A crashed subprocess releases its CUDA context before this retry.
            latents=16384
            settings['latents']=latents
            _,retry=await refine_job(jobs[0][0],settings,'Diagnóstico 16384 · no imprimir',True)
            manifest['capacity_retry']={'id':retry['id'],'status':retry['status']}
            if retry['status'] != 'ready':
                raise RuntimeError('No se pudo validar la capacidad del refinador: '+retry.get('error',''))
        manifest['validated_latents']=latents
        for source,base in jobs:
            check_cancelled(plan_dir)
            variant=base['experiment']['variant']
            if any(item.get('stage')=='refined' and item.get('variant')==variant
                   and read(DATA/item['id']).get('status')=='ready' for item in manifest['projects']):
                continue
            settings.update(steps=50,latents=latents,resolution=512,chunks=1024)
            def on_created(record):
                check_cancelled(plan_dir)
                manifest['projects'].append({'id':record['id'],'variant':variant,'stage':'refined','status':record['status']})
                manifest.update(state='refining',active_project=record['id'],heartbeat=time.time())
                write_json(manifest_path,manifest)
            path,result=await refine_job(source,settings,f'Flores y dorso · {variant} · UltraShape',on_created=on_created)
            manifest['projects'][-1]['status']=result['status']
            write_json(manifest_path,manifest)
            if result['status'] != 'ready':
                raise RuntimeError(result.get('error','Falló el refinamiento.'))
        manifest.update(state='ready',finished_at=time.time())
    except JobCancelled:
        manifest.update(state='cancelled',finished_at=time.time())
    except Exception as error:
        manifest.update(state='error',error=str(error),finished_at=time.time())
        for path,_ in jobs:
            record=read(path)
            if record.get('status') in ('queued','running'):
                record.update(status='error',error='Lote detenido: '+str(error))
                save(path,record)
        raise
    finally:
        write_json(manifest_path,manifest)


async def generate_reference(directory, name):
    """One new design through the accepted front/back + UltraShape settings."""
    directory=Path(directory).resolve()
    if not all((directory/(view+'.png')).is_file() for view in ('front','back')):
        raise ValueError('Se necesitan las referencias front.png y back.png.')
    settings_path=ROOT/'data/approved-reference.json'
    if not settings_path.is_file():
        settings_path=ROOT/'config/approved-generation.json'
    approved=json.loads(settings_path.read_text(encoding='utf-8'))
    experiment_id=uuid.uuid4().hex
    plan_dir=ROOT/'data/experiments'/experiment_id
    plan_dir.mkdir(parents=True)
    manifest_path=plan_dir/'experiment.json'
    register_worker(plan_dir)
    path,record=pending_project(name,directory,experiment_id)
    record.update(name=name+' · multivista',seed=approved['generation']['seed'],
                  fidelity_settings=approved['generation']['fidelity_settings'])
    record['progress']['label']='Preparando la nueva generación'
    record['design']={'style':'low-poly','reference_directory':str(directory),
                      'settings_from_approved_project':approved['project_id']}
    save(path,record)
    manifest={'id':experiment_id,'created_at':time.time(),'state':'preparing',
              'purpose':name,'projects':[{'id':record['id'],'variant':name,'stage':'base'}],
              'approved_reference_project':approved['project_id']}
    write_json(manifest_path,manifest)
    print(json.dumps({'experiment':experiment_id,'project':record['id'],'name':name},ensure_ascii=True),flush=True)
    try:
        await wait_for_gpu({record['id']},manifest,manifest_path)
        check_cancelled(plan_dir)
        record.pop('scheduler_only',None)
        record['progress']={}
        manifest.update(state='generating',active_project=record['id'])
        write_json(manifest_path,manifest)
        await generate(path,record)
        check_cancelled(plan_dir)
        if record['status']!='ready':
            raise RuntimeError(record.get('error') or 'Falló la malla inicial.')
        def on_created(refined):
            check_cancelled(plan_dir)
            manifest['projects'].append({'id':refined['id'],'variant':name,'stage':'refined','status':'queued'})
            manifest.update(state='refining',active_project=refined['id'],heartbeat=time.time())
            write_json(manifest_path,manifest)
        settings={key:approved['refinement'][key] for key in ('steps','latents','resolution','chunks','sequential_cfg')}
        settings['seed']=approved.get('refinement_seed',42)
        _,result=await refine_job(path,settings,name+' · UltraShape',on_created=on_created)
        manifest['projects'][-1]['status']=result['status']
        if result['status']!='ready':
            raise RuntimeError(result.get('error') or 'Falló el refinamiento.')
        manifest.update(state='ready',finished_at=time.time())
    except JobCancelled:
        manifest.update(state='cancelled',finished_at=time.time())
    except Exception as error:
        manifest.update(state='error',error=str(error),finished_at=time.time())
        current=read(path)
        if current.get('status') in ('queued','running'):
            current.update(status='error',error=str(error))
            save(path,current)
        raise
    finally:
        write_json(manifest_path,manifest)


if __name__=='__main__':
    parser=argparse.ArgumentParser()
    parser.add_argument('--resume',help='Reanudar refinamientos de un experimento conservando sus mallas base.')
    parser.add_argument('--reference-directory',help='Generar y refinar un diseño nuevo con front.png y back.png.')
    parser.add_argument('--name',default='Nueva referencia IA')
    args=parser.parse_args()
    if args.resume and args.reference_directory:
        parser.error('Elige reanudar o una referencia nueva.')
    asyncio.run(generate_reference(args.reference_directory,args.name) if args.reference_directory else main(args.resume))
