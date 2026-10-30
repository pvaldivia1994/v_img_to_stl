import asyncio
import json
import uuid

import pytest

from scripts import run_hybrid_fidelity as hybrid
from app.persistence import write_json
from app.job_control import JobCancelled


@pytest.mark.parametrize('original_already_refined', [False, True])
def test_resume_reuses_bases_and_capacity_and_only_runs_missing_refinements(tmp_path, monkeypatch, original_already_refined):
    data = tmp_path / 'data/projects'
    data.mkdir(parents=True)
    monkeypatch.setattr(hybrid, 'ROOT', tmp_path)
    monkeypatch.setattr(hybrid, 'DATA', data)
    identifier = uuid.uuid4().hex
    manifest = {'id':identifier,'projects':[], 'validated_latents':32768,
                'state':'error','error':'Previous file lock','finished_at':1}
    for index, variant in enumerate(('Original','Referencia IA')):
        path = data / f'base{index}'
        path.mkdir()
        (path/'original.glb').write_bytes(b'completed-geometry')
        write_json(path/'project.json', {'id':path.name,'status':'ready','experiment':{'variant':variant}})
        manifest['projects'].append({'id':path.name,'variant':variant,'stage':'base'})
    old = data/'old-refinement'
    old.mkdir()
    write_json(old/'project.json',{'status':'ready' if original_already_refined else 'error'})
    manifest['projects'].append({'id':old.name,'variant':'Original','stage':'refined'})
    directory = tmp_path/'data/experiments'/identifier
    directory.mkdir(parents=True)
    write_json(directory/'experiment.json',manifest)
    calls = []
    async def no_wait(*args):
        pass
    async def forbidden_generate(*args):
        pytest.fail('A completed base must not be regenerated')
    async def refine(source, settings, name, validation=False, on_created=None):
        assert not validation, 'The validated capacity probe must be reused'
        assert settings == {'steps':50,'latents':32768,'resolution':512,'chunks':1024,'sequential_cfg':True,'seed':42}
        calls.append(source.name)
        path = data / uuid.uuid4().hex
        path.mkdir()
        record = {'id':path.name,'status':'queued'}
        on_created(record)
        record['status'] = 'ready'
        write_json(path/'project.json',record)
        return path,record
    monkeypatch.setattr(hybrid,'wait_for_gpu',no_wait)
    monkeypatch.setattr(hybrid,'generate',forbidden_generate)
    monkeypatch.setattr(hybrid,'refine_job',refine)
    asyncio.run(hybrid.main(identifier))
    assert calls == (['base1'] if original_already_refined else ['base0','base1'])
    saved = json.loads((directory/'experiment.json').read_text(encoding='utf-8'))
    assert saved['state'] == 'ready'
    assert saved['previous_errors'] == ['Previous file lock']
    for name in ('base0','base1'):
        assert (data/name/'original.glb').read_bytes() == b'completed-geometry'


def test_stop_arriving_between_refinement_creation_and_registration_leaves_no_queued_orphan(tmp_path,monkeypatch):
    path = tmp_path/'attempt'
    path.mkdir()
    record = {'id':path.name,'status':'queued'}
    write_json(path/'project.json',record)
    monkeypatch.setattr(hybrid,'create_refinement',lambda *args:(path,record))
    def stop_arrived(record):
        raise JobCancelled('Stop requested while the record was being created')
    with pytest.raises(JobCancelled):
        asyncio.run(hybrid.refine_job(tmp_path,{},'New refinement',on_created=stop_arrived))
    assert json.loads((path/'project.json').read_text(encoding='utf-8'))['status']=='cancelled'


@pytest.mark.parametrize('profile_location',['data/approved-reference.json','config/approved-generation.json'])
def test_new_design_runs_one_multiview_base_and_one_refinement_with_approved_settings(tmp_path,monkeypatch,profile_location):
    from PIL import Image
    data=tmp_path/'data/projects'
    data.mkdir(parents=True)
    references=tmp_path/'references'
    references.mkdir()
    for view in ('front','back'):
        Image.new('RGB',(32,48),'gray').save(references/(view+'.png'))
    settings={'steps':50,'latents':32768,'resolution':512,'chunks':1024,'sequential_cfg':True}
    profile=tmp_path/profile_location
    profile.parent.mkdir(parents=True,exist_ok=True)
    write_json(profile,{
        'project_id':'approved','generation':{'seed':4007959359,'fidelity_settings':{'steps':50,'threshold':.5,'num_chunks':2048}},
        'refinement':settings})
    monkeypatch.setattr(hybrid,'ROOT',tmp_path)
    monkeypatch.setattr(hybrid,'DATA',data)
    calls=[]
    async def no_wait(*args):pass
    async def generate(path,record):
        calls.append('base')
        assert record['mode']=='multiview' and set(record['views'])=={'front','back'}
        assert record['seed']==4007959359 and record['fidelity_settings']['steps']==50
        assert record['name']=='Lobito poligonal · multivista'
        record['status']='ready'
        write_json(path/'project.json',record)
    async def refine(source,actual,name,on_created):
        calls.append('refined')
        assert actual=={**settings,'seed':42}
        assert name=='Lobito poligonal · UltraShape'
        record={'id':'final','status':'queued'}
        on_created(record)
        return data/'final',{**record,'status':'ready'}
    monkeypatch.setattr(hybrid,'wait_for_gpu',no_wait)
    monkeypatch.setattr(hybrid,'generate',generate)
    monkeypatch.setattr(hybrid,'refine_job',refine)
    asyncio.run(hybrid.generate_reference(references,'Lobito poligonal'))
    assert calls==['base','refined']
    manifest=json.loads(next((tmp_path/'data/experiments').glob('*/experiment.json')).read_text(encoding='utf-8'))
    assert manifest['state']=='ready' and len(manifest['projects'])==2
