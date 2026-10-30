import torch
import comfy.utils
from comfy_api.latest import Types
from comfy_extras.nodes_save_3d import pack_variable_mesh_batch
from .core import extract_surface
from .volume import StreamingVolumeDecoder

class FormaVoxelToMesh:
    @classmethod
    def INPUT_TYPES(cls):
        return {'required': {'voxel': ('VOXEL',), 'threshold': ('FLOAT', {'default': 0.6, 'min': -1.0, 'max': 1.0, 'step': 0.01})}}
    RETURN_TYPES = ('MESH',)
    FUNCTION = 'extract'
    CATEGORY = 'Forma/3D'

    def extract(self, voxel, threshold):
        vertices, faces = [], []
        for field in voxel.data:
            v, f = extract_surface(field.detach().float().cpu().numpy(), threshold)
            vertices.append(torch.from_numpy(v))
            faces.append(torch.from_numpy(f))
        return (pack_variable_mesh_batch(vertices, faces),)

class FormaVAEDecodeHunyuan3D:
    @classmethod
    def INPUT_TYPES(cls):
        return {'required': {'samples': ('LATENT',), 'vae': ('VAE',),
                             'num_chunks': ('INT', {'default': 4000, 'min': 256, 'max': 20000}),
                             'octree_resolution': ('INT', {'default': 512, 'min': 16, 'max': 512})}}
    RETURN_TYPES = ('VOXEL',)
    FUNCTION = 'decode'
    CATEGORY = 'Forma/3D'

    def decode(self, samples, vae, num_chunks, octree_resolution):
        model = vae.first_stage_model
        original = model.volume_decoder
        try:
            model.volume_decoder = StreamingVolumeDecoder(comfy.utils.ProgressBar)
            field = vae.decode(samples['samples'], vae_options={
                'num_chunks': num_chunks, 'octree_resolution': octree_resolution})
        finally:
            model.volume_decoder = original
        return (Types.VOXEL(field),)


NODE_CLASS_MAPPINGS = {'FormaVoxelToMesh': FormaVoxelToMesh, 'FormaVAEDecodeHunyuan3D': FormaVAEDecodeHunyuan3D}
NODE_DISPLAY_NAME_MAPPINGS = {'FormaVoxelToMesh': 'Forma · Superficie para STL',
                             'FormaVAEDecodeHunyuan3D': 'Forma · Detalle con progreso'}
