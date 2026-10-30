"""Equivalent classifier-free branches evaluated sequentially to bound VRAM."""
def slice_batch(value, index, batch):
    import torch
    if isinstance(value, torch.Tensor):
        return value[index:index+1] if value.ndim and value.shape[0] == batch else value
    if isinstance(value, dict):
        return {k:slice_batch(v,index,batch) for k,v in value.items()}
    if isinstance(value, tuple):
        return tuple(slice_batch(v,index,batch) for v in value)
    if isinstance(value, list):
        return [slice_batch(v,index,batch) for v in value]
    return value


def install_sequential_cfg(model):
    import torch
    original = model.forward
    def forward(x,*args,**kwargs):
        batch = x.shape[0]
        if batch == 1:
            return original(x,*args,**kwargs)
        outputs = []
        for index in range(batch):
            outputs.append(original(x[index:index+1],
                *slice_batch(args,index,batch),**slice_batch(kwargs,index,batch)))
        return torch.cat(outputs,dim=0)
    model.forward = forward
