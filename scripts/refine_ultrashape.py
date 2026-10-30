"""Image-conditioned UltraShape refinement, isolated runtime, real app progress.

Models start on CPU. DiT blocks are offloaded through Accelerate, so initial
loading never requires fitting all components in 8 GB. Dense queries stream
to RAM and use the full VAE attention instead of approximate KV selection.
"""
import argparse
import gc
import hashlib
import importlib.util
import json
import os
from pathlib import Path
import random
import shutil
import sys
import time
import uuid

ROOT = Path(__file__).resolve().parents[1]
DATA = ROOT / 'data/projects'
SOURCE = Path('C:/_IA/UltraShape-1.0')
CHECKPOINT = Path('C:/_IA/models/ultrashape/ultrashape_v1.pt')
os.environ.setdefault('HF_HOME', 'C:/_IA/cache/huggingface')
os.environ.setdefault('TORCH_HOME', 'C:/_IA/cache/torch')
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(SOURCE))
from app.persistence import write_json
from app.job_control import check_cancelled, register_worker, JobCancelled, finish_cancelled


class Progress:
    def __init__(self, path, record):
        self.path, self.record = path, record
        self.last = 0

    def stage(self, index, label, value=None, total=None, force=True):
        check_cancelled(self.path)
        now = time.time()
        if not force and now-self.last < 1:
            return
        previous = self.record.get('progress', {})
        self.record['progress'] = {'stage': 'refine-'+str(index), 'stage_index': index,
            'stage_count': 7, 'label': label, 'value': value, 'total': total,
            'percent': round(100*value/total, 1) if total else None,
            'started_at': previous.get('started_at', now) if previous.get('stage_index') == index else now,
            'updated_at': now}
        self.record['worker_heartbeat'] = now
        write_json(self.path / 'project.json', self.record)
        self.last = now


def rgba_reference(path):
    import numpy as np
    from PIL import Image
    from skimage.morphology import remove_small_holes
    image = Image.open(path).convert('RGBA')
    rgb = np.asarray(image.convert('RGB'))
    if image.getextrema()[3][0] < 255:
        return image
    # Keep real openings; only close tiny white highlight pinholes.
    alpha = remove_small_holes(np.any(rgb < 250, axis=2),area_threshold=64).astype('uint8')*255
    image.putalpha(Image.fromarray(alpha))
    return image


def load_components(progress):
    import torch
    from omegaconf import OmegaConf
    from ultrashape.utils.misc import instantiate_from_config
    config = OmegaConf.load(SOURCE / 'configs/infer_dit_refine.yaml').model.params
    # The full checkpoint includes the image encoder. Only its architecture
    # configuration is needed; do not download duplicate DINO weights.
    config.conditioner_config.params.main_image_encoder.kwargs.config = json.loads(
        Path('C:/_IA/models/ultrashape/dinov2-config.json').read_text())
    config.vae_config.params.enable_flashvdm = False
    weights = torch.load(CHECKPOINT, map_location='cpu', weights_only=True, mmap=True)
    components = {}
    for index, (name, cfg) in enumerate((('vae', config.vae_config), ('dit', config.dit_cfg),
                                        ('conditioner', config.conditioner_config)), 1):
        progress.stage(2, 'Cargando el refinador en RAM', index-1, 3)
        component = instantiate_from_config(OmegaConf.to_container(cfg, resolve=True))
        component.load_state_dict(weights[name], strict=True, assign=True)
        components[name] = component.eval().requires_grad_(False).to(dtype=torch.bfloat16)
    del weights
    components['scheduler'] = instantiate_from_config(config.scheduler_cfg)
    components['processor'] = instantiate_from_config(config.image_processor_cfg)
    gc.collect()
    progress.stage(2, 'Refinador cargado en RAM', 3, 3)
    return components, config


def refine(args, path, record, progress):
    import httpx
    import numpy as np
    import torch
    import trimesh
    from accelerate import cpu_offload
    from skimage.measure import marching_cubes
    # Free idle ComfyUI weights without stopping the service or changing ports.
    with httpx.Client(base_url='http://127.0.0.1:8188', timeout=30) as client:
        queue = client.get('/queue').raise_for_status().json()
        if queue.get('queue_running') or queue.get('queue_pending'):
            raise RuntimeError('ComfyUI está ocupado; no se cargó otro modelo sobre la GPU.')
        client.post('/free', json={'unload_models': True, 'free_memory': True}).raise_for_status()
    progress.stage(1, 'Verificando los pesos del refinador')
    expected = 'c96ae010c4169597fd0006dcb08056bf6104a1fca249b10fed7ddded324c3f0f'
    with CHECKPOINT.open('rb') as stream:
        if hashlib.file_digest(stream, 'sha256').hexdigest() != expected:
            raise RuntimeError('Los pesos no superaron la verificación SHA256.')
    if not torch.cuda.is_available():
        raise RuntimeError('El entorno del refinador no encuentra CUDA.')
    random.seed(args.seed)
    np.random.seed(args.seed)
    torch.manual_seed(args.seed)
    torch.cuda.manual_seed_all(args.seed)
    torch.cuda.reset_peak_memory_stats()
    components, config = load_components(progress)
    from ultrashape.pipelines import UltraShapePipeline
    from ultrashape.surface_loaders import SharpEdgeSurfaceLoader
    from ultrashape.utils import voxelize_from_point
    pipeline = UltraShapePipeline(vae=components['vae'], model=components['dit'],
        conditioner=components['conditioner'], scheduler=components['scheduler'],
        image_processor=components['processor'], device='cpu', dtype=torch.bfloat16)
    # Keep weights in RAM and load one DiT block at a time during forward.
    cpu_offload(pipeline.model, execution_device=torch.device('cuda:0'),
                preload_module_classes=['DiTBlock'])
    if args.sequential_cfg:
        from scripts.sequential_cfg import install_sequential_cfg
        install_sequential_cfg(pipeline.model)
    pipeline.device = torch.device('cuda:0')
    original_encode = pipeline.encode_cond
    def encode(*a, **kw):
        pipeline.conditioner.to('cuda')
        output = original_encode(*a, **kw)
        pipeline.conditioner.to('cpu')
        torch.cuda.empty_cache()
        return output
    pipeline.encode_cond = encode
    progress.stage(3, 'Muestreando bordes y volumen de la malla inicial')
    loader = SharpEdgeSurfaceLoader(num_sharp_points=204800, num_uniform_points=204800)
    surface = loader(str(path / 'coarse.glb'), normalize_scale=.99)
    # Voxelization on CPU avoids allocating a large temporary unique-sort buffer
    # on the GPU and follows the same official operation and random seed.
    _, voxel_idx = voxelize_from_point(surface[:, :, :3], args.latents,
                                       resolution=config.vae_config.params.voxel_query_res)
    torch.save(voxel_idx, path / 'voxel-indices.pt')
    del surface
    block_count = len(pipeline.model.blocks)
    cfg_passes = 2 if args.sequential_cfg else 1
    total_blocks = args.steps*block_count*cfg_passes
    step_state = {'completed':0}
    progress.stage(4, 'Refinando geometría con la imagen', 0, total_blocks)
    def block_finished(index):
        def update(module, inputs, output):
            step_state['completed'] += 1
            progress.stage(4, 'Refinando geometría con la imagen', step_state['completed'], total_blocks, force=False)
        return update
    for index, block in enumerate(pipeline.model.blocks):
        block.register_forward_hook(block_finished(index))
    def callback(index, timestep, output):
        progress.stage(4, 'Refinando geometría con la imagen', step_state['completed'], total_blocks)
    with torch.inference_mode(), torch.autocast('cuda', dtype=torch.bfloat16):
        reference = path / 'conditioning-front.png'
        _, latents = pipeline(image=rgba_reference(reference if reference.exists() else path / 'input.png'),
            voxel_cond=voxel_idx.to('cuda'), generator=torch.Generator('cuda').manual_seed(args.seed),
            num_inference_steps=args.steps, guidance_scale=5., output_type='latent',
            callback=callback, callback_steps=1)
        torch.save(latents.cpu(), path / 'refined-latents.pt')
        # Remove DiT references/hooks before loading the VAE. No geometry reduction.
        vae = pipeline.vae
        del pipeline, components, original_encode, encode
        gc.collect()
        torch.cuda.empty_cache()
        progress.stage(5, f'Calculando relieve a resolución {args.resolution}')
        vae.to('cuda')
        decoded = vae(latents / vae.scale_factor)
        # The same mesh uses the same latent K/V projections for every query.
        # Upstream exposes this exact cache; no token selection/approximation.
        vae.geo_decoder.cross_attn_decoder.attn.kv_cache = True
        vae.geo_decoder.cross_attn_decoder.attn.data = None
        spec = importlib.util.spec_from_file_location('forma_stream_volume', ROOT / 'comfy_nodes/forma_mesh/volume.py')
        module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(module)
        class VolumeProgress:
            def __init__(self, total):
                self.total, self.value = total, 0
            def update(self, count):
                self.value += count
                progress.stage(5, f'Calculando relieve a resolución {args.resolution}', self.value, self.total, force=False)
        field = module.StreamingVolumeDecoder(VolumeProgress)(decoded, vae.geo_decoder,
            octree_resolution=args.resolution, bounds=1., num_chunks=args.chunks, query_dtype=torch.float32)
        vae.geo_decoder.cross_attn_decoder.attn.data = None
        del decoded, vae, latents
        gc.collect()
        torch.cuda.empty_cache()
    np.save(path / 'refined-field.npy', field[0].numpy())
    progress.stage(6, 'Construyendo la superficie sin reducir pétalos')
    values = field[0].numpy()
    if not np.isfinite(values).all():
        raise RuntimeError('El refinador produjo valores no finitos; no se publicó una malla incompleta.')
    vertices, faces, _, _ = marching_cubes(values, 0., allow_degenerate=False)
    vertices = vertices / args.resolution * 2. - 1.
    mesh = trimesh.Trimesh(vertices=vertices, faces=faces, process=False)
    if mesh.volume < 0:
        mesh.invert()
    progress.stage(7, 'Guardando la variante refinada')
    mesh.export(path / 'original.glb')
    record.update(status='ready', elapsed_seconds=round(time.time()-record['started_at'], 1),
                  mesh_report={'vertices': len(mesh.vertices), 'faces': len(mesh.faces),
                    'watertight': bool(mesh.is_watertight), 'winding_consistent': bool(mesh.is_winding_consistent)},
                  gpu_peak_allocated_mib=round(torch.cuda.max_memory_allocated()/1024**2),
                  gpu_peak_reserved_mib=round(torch.cuda.max_memory_reserved()/1024**2))
    progress.stage(7, 'Refinamiento disponible para comparar', 1, 1)


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('source_project')
    parser.add_argument('--prepared', action='store_true')
    parser.add_argument('--validation-only', action='store_true')
    parser.add_argument('--sequential-cfg', action='store_true')
    parser.add_argument('--steps', type=int, default=75)
    parser.add_argument('--latents', type=int, choices=[8192, 16384, 32768], default=16384)
    parser.add_argument('--resolution', type=int, choices=[32, 128, 256, 384, 512, 768, 1024], default=768)
    parser.add_argument('--chunks', type=int, default=1024)
    parser.add_argument('--seed', type=int, default=42)
    parser.add_argument('--name', default='Flores · UltraShape · relieve fino')
    args = parser.parse_args()
    if not 1 <= args.steps <= 100 or not 256 <= args.chunks <= 4096 or not 0 <= args.seed < 2**32:
        parser.error('Parámetros fuera del rango admitido.')
    source = DATA / args.source_project
    if args.prepared:
        path = source
        record = json.loads((path / 'project.json').read_text(encoding='utf-8'))
        if record.get('worker') != 'ultrashape' or record.get('status') != 'queued':
            raise RuntimeError('El proyecto de refinamiento no esta en espera.')
        for key in ('steps', 'latents', 'resolution', 'chunks'):
            setattr(args, key, record['refinement'][key])
        args.seed = record['seed']
        args.sequential_cfg = record['refinement'].get('sequential_cfg',False)
    else:
        from app.refinement import create_refinement
        path, record = create_refinement(source, DATA, {key:getattr(args,key) for key in ('steps','latents','resolution','chunks','seed','sequential_cfg')}, args.name)
    if any(json.loads(p.read_text(encoding='utf-8')).get('status') in ('running', 'queued')
           for p in DATA.glob('*/project.json') if p.parent != path and not json.loads(p.read_text(encoding='utf-8')).get('scheduler_only')):
        record.update(status='error', error='Hay otro trabajo activo; no se cargo el refinador.')
        Progress(path, record).stage(1, 'Esperando a que termine el otro trabajo')
        raise RuntimeError(record['error'])
    check_cancelled(path)
    register_worker(path)
    record.update(status='running', started_at=time.time())
    if args.validation_only:
        record['validation_only'] = True
    progress = Progress(path, record)
    progress.stage(1, 'Preparando el refinamiento de las flores')
    print('Project: '+path.name, flush=True)
    tracker=DATA.parent / 'fidelity-fox/latest-ultrashape-project-id.txt'
    tracker.parent.mkdir(parents=True,exist_ok=True)
    tracker.write_text(path.name)
    try:
        refine(args, path, record, progress)
        if args.validation_only and record.get('status')=='ready':
            write_json(SOURCE/'forma-validated.json',{
                'probe_project':record['id'],'validated_at':time.time(),
                'latents':args.latents,'steps':args.steps,'resolution':args.resolution,
                'allocated_mib':record.get('gpu_peak_allocated_mib'),
                'reserved_mib':record.get('gpu_peak_reserved_mib'),
                'note':'Local execution compatibility only; not an artistic quality approval.'})
        print(json.dumps(record, ensure_ascii=True), flush=True)
    except JobCancelled:
        finish_cancelled(path)
        print('Detenido por el usuario.',flush=True)
    except Exception as error:
        record.update(status='error', error=str(error), elapsed_seconds=round(time.time()-record['started_at'], 1))
        try:
            progress.stage(record['progress']['stage_index'], 'El refinamiento necesita atención')
        except OSError as persistence_error:
            print(f'No se pudo guardar el error original: {persistence_error}', file=sys.stderr, flush=True)
        raise


if __name__ == '__main__':
    main()
