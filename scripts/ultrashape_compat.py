"""Exact per-sequence SDPA fallback for packed, variable-length attention.

No learned layers, padding conventions or model weights are changed.
"""
def flash_attn_varlen_func(q, k, v, cu_seqlens_q, cu_seqlens_k,
                          max_seqlen_q, max_seqlen_k, dropout_p=0.,
                          softmax_scale=None, causal=False, **kwargs):
    import torch
    import torch.nn.functional as functional
    outputs = []
    for index in range(len(cu_seqlens_q)-1):
        qa, qb = int(cu_seqlens_q[index]), int(cu_seqlens_q[index+1])
        ka, kb = int(cu_seqlens_k[index]), int(cu_seqlens_k[index+1])
        query = q[qa:qb].transpose(0, 1).unsqueeze(0)
        key = k[ka:kb].transpose(0, 1).unsqueeze(0)
        value = v[ka:kb].transpose(0, 1).unsqueeze(0)
        result = functional.scaled_dot_product_attention(query, key, value,
            dropout_p=dropout_p, is_causal=causal, scale=softmax_scale)
        outputs.append(result.squeeze(0).transpose(0, 1))
    return torch.cat(outputs, dim=0)
