"""Upstream K/V caching must preserve chunk outputs and reset across meshes."""
import sys
import os
os.environ.setdefault('HF_HOME', 'C:/_IA/cache/huggingface')
sys.path.insert(0, 'C:/_IA/UltraShape-1.0')
import torch
from ultrashape.models.autoencoders.attention_blocks import MultiheadCrossAttention

torch.manual_seed(42)
module = MultiheadCrossAttention(width=32, heads=4, qk_norm=True).eval()
queries = torch.randn(1, 24, 32)
latents = torch.randn(1, 41, 32)
with torch.inference_mode():
    expected = torch.cat([module(chunk, latents) for chunk in queries.split(7, dim=1)], dim=1)
    module.kv_cache = True
    actual = torch.cat([module(chunk, latents) for chunk in queries.split(7, dim=1)], dim=1)
    torch.testing.assert_close(actual, expected)
    module.data = None
    new_latents = latents + 1
    fresh = module(queries, new_latents)
    module.kv_cache = False
    torch.testing.assert_close(fresh, module(queries, new_latents))
print('Exact K/V cache: chunk outputs and mesh isolation OK')
