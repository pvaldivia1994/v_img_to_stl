"""Verify packed attention fallback against independent padded SDPA calls."""
import torch
import torch.nn.functional as F
from scripts.ultrashape_compat import flash_attn_varlen_func

torch.manual_seed(42)
q = torch.randn(7, 2, 8)
k = torch.randn(9, 2, 8)
v = torch.randn(9, 2, 8)
qs = torch.tensor([0, 4, 7], dtype=torch.int32)
ks = torch.tensor([0, 3, 9], dtype=torch.int32)
actual = flash_attn_varlen_func(q, k, v, qs, ks, 4, 6)
expected = torch.cat([
    F.scaled_dot_product_attention(q[a:b].transpose(0, 1).unsqueeze(0),
        k[c:d].transpose(0, 1).unsqueeze(0), v[c:d].transpose(0, 1).unsqueeze(0))
        .squeeze(0).transpose(0, 1)
    for a,b,c,d in [(0,4,0,3),(4,7,3,9)]])
torch.testing.assert_close(actual, expected)
# Distinct sequences must never attend to one another.
changed = k.clone()
changed[3:] += 100
isolated = flash_attn_varlen_func(q, changed, v, qs, ks, 4, 6)
torch.testing.assert_close(isolated[:4], actual[:4])
print('Packed SDPA fallback: values, shapes and sequence isolation OK')
