import torch
from scripts.sequential_cfg import install_sequential_cfg

class Model(torch.nn.Module):
    def __init__(self):
        super().__init__()
        self.linear = torch.nn.Linear(8,8)
    def forward(self,x,t,contexts,voxel_cond=None,guidance=None):
        return self.linear(x) + t[:,None,None] + contexts['main'] + voxel_cond + guidance

torch.manual_seed(42)
model=Model().eval()
x=torch.randn(2,13,8)
t=torch.tensor([.5,.5])
contexts={'main':torch.randn(2,13,8)}
voxels=torch.randn(2,13,8)
with torch.inference_mode():
    expected=model(x,t,contexts,voxel_cond=voxels,guidance=3.)
    install_sequential_cfg(model)
    actual=model(x,t,contexts,voxel_cond=voxels,guidance=3.)
    torch.testing.assert_close(actual,expected)
    torch.testing.assert_close(model(x[:1],t[:1],{'main':contexts['main'][:1]},voxel_cond=voxels[:1],guidance=3.),expected[:1])
print('Sequential CFG: batch independence, nested conditioning and single batch verified')
