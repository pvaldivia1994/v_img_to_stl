"""Run with the ComfyUI Python, which supplies torch. No model/GPU needed."""
import importlib.util
from pathlib import Path
import math
import torch

root = Path(__file__).resolve().parents[1]
spec = importlib.util.spec_from_file_location('forma_volume', root / 'comfy_nodes/forma_mesh/volume.py')
module = importlib.util.module_from_spec(spec)
spec.loader.exec_module(module)

for dtype in (torch.float32, torch.float16):
    events = []
    class Progress:
        def __init__(self, total):
            self.total = total
            events.append(('total', total))
        def update(self, increment):
            events.append(('step', increment))
    def field(queries, latents):
        # A non-symmetric plane exposes coordinate swaps and chunk ordering bugs.
        values = queries[..., 0] + 2 * queries[..., 1] - 3 * queries[..., 2]
        return values.unsqueeze(-1)
    latents = torch.zeros((2, 3, 4), dtype=dtype)
    result = module.StreamingVolumeDecoder(Progress)(latents, field, 8, num_chunks=37)
    axis = torch.linspace(-1.01, 1.01, 9).to(dtype)
    x, y, z = torch.meshgrid(axis, axis, axis, indexing='ij')
    expected = (x + 2 * y - 3 * z).float()
    assert result.shape == (2, 9, 9, 9)
    assert result.device.type == 'cpu'
    assert torch.equal(result[0], expected) and torch.equal(result[1], expected)
    assert events[0] == ('total', math.ceil(9**3 / 37))
    assert sum(amount for kind, amount in events if kind == 'step') == math.ceil(9**3 / 37)
print('Volume coordinates, batches, precision and progress verified for float32/float16.')

# UltraShape uses BF16 weights but keeps high-resolution query coordinates
# in float32 until Fourier encoding, avoiding BF16 grid quantization.
latents = torch.zeros((1, 3, 4), dtype=torch.bfloat16)
result = module.StreamingVolumeDecoder(Progress)(latents, field, 8, num_chunks=37, query_dtype=torch.float32)
axis = torch.linspace(-1.01, 1.01, 9)
x, y, z = torch.meshgrid(axis, axis, axis, indexing='ij')
assert torch.equal(result[0], x + 2*y - 3*z)
print('Float32 query coordinates with BF16 latents verified.')
