"""Dense Hunyuan field evaluation with bounded GPU buffers and real progress.

Same grid/order as ComfyUI's VanillaVolumeDecoder; queries and results are
streamed instead of retaining the entire grid and every result on the GPU.
"""
import math
import torch


class StreamingVolumeDecoder:
    def __init__(self, progress_factory):
        self.progress_factory = progress_factory

    @torch.no_grad()
    def __call__(self, latents, geo_decoder, octree_resolution, bounds=1.01,
                 num_chunks=4000, enable_pbar=True, query_dtype=None, **kwargs):
        if isinstance(bounds, (int, float)):
            bounds = [-bounds] * 3 + [bounds] * 3
        side = int(octree_resolution) + 1
        total = side ** 3
        axes = [torch.linspace(bounds[i], bounds[i + 3], side, dtype=torch.float32)
                .to(device=latents.device, dtype=query_dtype or latents.dtype) for i in range(3)]
        result = torch.empty((latents.shape[0], total), device='cpu', dtype=torch.float32)
        progress = self.progress_factory(math.ceil(total / num_chunks)) if enable_pbar else None
        for start in range(0, total, num_chunks):
            end = min(start + num_chunks, total)
            indices = torch.arange(start, end, device=latents.device)
            queries = torch.stack((axes[0][indices // (side * side)],
                                   axes[1][(indices // side) % side],
                                   axes[2][indices % side]), dim=-1)
            queries = queries.unsqueeze(0).repeat(latents.shape[0], 1, 1)
            logits = geo_decoder(queries=queries, latents=latents)
            result[:, start:end].copy_(logits.reshape(latents.shape[0], -1).float().cpu())
            if progress:
                progress.update(1)
        return result.view(latents.shape[0], side, side, side)
