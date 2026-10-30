import asyncio
import json
import time

import httpx
import pytest
from fastapi.testclient import TestClient

from app import main, job_control
from app.persistence import write_json
from app.regeneration import clone


def make_project(data, identifier, status='ready', **extra):
    path = data/identifier
    path.mkdir()
    record = dict(id=identifier,name='Figura',status=status,created_at=0,seed=42,
                  model_family='hunyuan2',quality='maximum',remove_background=False,
                  views={'front':'input.png','back':'input-back.png'},mode='multiview',
                  fidelity_settings={'steps':50,'threshold':.5,'num_chunks':2048},exports=[])
    record.update(extra)
    for name in ('input.png','input-back.png','source.png','source-back.png','conditioning-front.png'):
        (path/name).write_bytes(name.encode())
    (path/'original.glb').write_bytes(b'completed-model')
    write_json(path/'project.json',record)
    return path,record


@pytest.fixture
def controls(tmp_path, monkeypatch):
    data = tmp_path/'projects'
    data.mkdir()
    monkeypatch.setattr(main,'DATA',data)
    monkeypatch.setattr(main,'ROOT',tmp_path)
    monkeypatch.setattr(main,'tasks',set())
    monkeypatch.setattr(main,'control_lock',asyncio.Lock())
    monkeypatch.setattr(main,'schedule',lambda coroutine:coroutine.close())
    monkeypatch.setattr(main,'refinement_ready',lambda:True)
    monkeypatch.setattr(job_control,'RUNNING_TASKS',{})
    async def health():
        return dict(connected=True,ready=True,busy=False,single_ready=True,multiview_ready=True,
                    maximum_ready=True,hunyuan21_ready=True)
    monkeypatch.setattr(main,'health',health)
    calls = []
    monkeypatch.setattr(job_control,'stop_processes',lambda root,data,records,groups:calls.append(set(records)))
    async def stop_engine(comfy,records):
        calls.append(('engine',set(records)))
    monkeypatch.setattr(job_control,'stop_comfy',stop_engine)
    with TestClient(main.app) as client:
        yield client,data,calls


def test_stop_and_regenerate_preserve_images_settings_and_previous_attempt(controls):
    client,data,calls = controls
    path,original = make_project(data,'one','running')
    stopped = client.post('/api/projects/one/stop').raise_for_status().json()
    assert stopped['status']=='cancelled'
    assert (path/'cancel.request.json').exists()
    assert ('engine',{'one'}) in calls
    assert client.post('/api/projects/one/stop').json()['status']=='cancelled'
    regenerated = client.post('/api/projects/one/regenerate').raise_for_status().json()
    assert regenerated['id']!='one' and regenerated['status']=='queued'
    for key in ('seed','quality','views','fidelity_settings','model_family'):
        assert regenerated[key]==original[key]
    target = data/regenerated['id']
    for name in original['views'].values():
        assert (target/name).read_bytes()==(path/name).read_bytes()
    assert (target/'conditioning-front.png').read_bytes()==(path/'conditioning-front.png').read_bytes()
    assert not (target/'original.glb').exists()
    assert not (target/'cancel.request.json').exists()
    assert (path/'original.glb').read_bytes()==b'completed-model'
    assert json.loads((path/'project.json').read_text(encoding='utf-8'))['status']=='cancelled'


def test_stop_comparison_cancels_pending_but_preserves_completed_results(controls):
    client,data,_ = controls
    make_project(data,'base','ready')
    make_project(data,'active','running')
    make_project(data,'pending','queued',scheduler_only=True)
    directory = data.parent/'experiments'/'comparison'
    directory.mkdir(parents=True)
    write_json(directory/'experiment.json',{'state':'refining','projects':[
        {'id':key,'stage':'base'} for key in ('base','active','pending')]})
    client.post('/api/projects/active/stop').raise_for_status()
    assert json.loads((data/'base/project.json').read_text())['status']=='ready'
    assert json.loads((data/'pending/project.json').read_text())['status']=='cancelled'
    assert json.loads((directory/'experiment.json').read_text())['state']=='cancelled'
    with pytest.raises(job_control.JobCancelled):
        job_control.check_cancelled(directory)


def test_no_false_stop_confirmation_and_no_regeneration_while_stopping(controls,monkeypatch):
    client,data,_ = controls
    make_project(data,'one','running')
    async def still_running(*args):
        raise RuntimeError('El motor sigue calculando')
    monkeypatch.setattr(job_control,'stop_comfy',still_running)
    assert client.post('/api/projects/one/stop').status_code==503
    assert client.get('/api/projects/one').json()['status']=='stopping'
    assert client.post('/api/projects/one/regenerate').status_code==409


def test_regeneration_rejects_active_and_other_busy_projects(controls):
    client,data,_ = controls
    make_project(data,'finished')
    make_project(data,'active','running')
    assert client.post('/api/projects/active/regenerate').status_code==409
    assert client.post('/api/projects/finished/regenerate').status_code==409
    assert client.post('/api/projects/finished/stop').status_code==409
    assert len(list(data.iterdir()))==2


def test_ultrashape_regeneration_reuses_exact_coarse_geometry_and_settings(controls):
    client,data,_ = controls
    settings={'source_project':'base','steps':50,'latents':32768,'resolution':512,
              'chunks':1024,'sequential_cfg':True}
    path,_ = make_project(data,'ultra','error',model_family='ultrashape',refinement=settings)
    (path/'coarse.glb').write_bytes(b'precise-initial-geometry')
    result = client.post('/api/projects/ultra/regenerate').raise_for_status().json()
    assert result['refinement']==settings and result['worker']=='ultrashape'
    assert (data/result['id']/'coarse.glb').read_bytes()==b'precise-initial-geometry'


def test_regeneration_detaches_old_comparison_and_missing_inputs_create_no_attempt(tmp_path):
    path,record = make_project(tmp_path,'one',experiment={'id':'old-group','variant':'Original'})
    target,result = clone(path,tmp_path)
    assert 'id' not in result['experiment'] and result['experiment']['origin_experiment_id']=='old-group'
    (path/'input-back.png').unlink()
    with pytest.raises(ValueError):
        clone(path,tmp_path)
    assert len(list(tmp_path.iterdir()))==2


def test_cancel_marker_prevents_stale_progress_overwriting_cancelled_state(tmp_path):
    path,record = make_project(tmp_path,'one','running')
    write_json(path/'cancel.request.json',{})
    job_control.finish_cancelled(path)
    main.save(path,dict(record,status='ready'))
    assert json.loads((path/'project.json').read_text(encoding='utf-8'))['status']=='cancelled'


def test_comfy_cancels_only_owned_prompt_without_interrupting_another_job(monkeypatch):
    original_client = httpx.AsyncClient
    calls = []
    def entry(identifier,client):
        return [1,identifier,{}, {'client_id':client}]
    def handler(request):
        calls.append((request.method,request.url.path))
        if request.url.path=='/queue':
            owned = [] if ('POST','/api/jobs/ours/cancel') in calls else [entry('ours','one')]
            return httpx.Response(200,json={'queue_running':[entry('foreign','other')],'queue_pending':owned})
        return httpx.Response(200,json={'cancelled':True})
    monkeypatch.setattr(httpx,'AsyncClient',lambda **kw:original_client(transport=httpx.MockTransport(handler),**kw))
    asyncio.run(job_control.stop_comfy('http://mock',{'one':{'model_family':'hunyuan2'}}))
    assert ('POST','/api/jobs/ours/cancel') in calls
    assert not any(path in ('/interrupt','/free','/api/jobs/foreign/cancel') for method,path in calls)


def test_process_stop_verifies_module_directory_job_and_registration(tmp_path,monkeypatch):
    import psutil
    now = time.time()
    class Process:
        def __init__(self,pid,module,argument,cwd=tmp_path):
            self.pid=pid
            self.info=dict(pid=pid,name='python.exe',cmdline=['python','-m',module,*argument],
                           cwd=str(cwd),create_time=now-1)
        def parents(self):return []
        def children(self,recursive=False):return []
        def terminate(self):stopped.append(self.pid)
    stopped=[]
    processes=[Process(100,'scripts.refine_ultrashape',['one','--prepared']),
               Process(101,'scripts.run_hybrid_fidelity',[]),
               Process(102,'uvicorn',['app.main:app']),
               Process(103,'scripts.refine_ultrashape',['foreign','--prepared']),
               Process(104,'scripts.refine_ultrashape',['one','--prepared'],tmp_path/'other'),
               Process(105,'scripts.run_hybrid_fidelity',[])]
    monkeypatch.setattr(psutil,'process_iter',lambda attrs:iter(processes))
    monkeypatch.setattr(psutil,'wait_procs',lambda processes,timeout:(processes,[]))
    data=tmp_path/'projects'
    (data/'one').mkdir(parents=True)
    group=tmp_path/'group'
    group.mkdir()
    write_json(group/'worker.json',{'pid':101,'registered_at':now})
    # A reused PID with a newer process creation time must be ignored.
    write_json(data/'one/worker.json',{'pid':105,'registered_at':now-1000})
    job_control.stop_processes(tmp_path,data,{'one':{}},[group])
    assert stopped==[101,100]
