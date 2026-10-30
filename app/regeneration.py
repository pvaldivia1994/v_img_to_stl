"""New attempts keep their exact inputs/settings and never overwrite a result."""
import copy
import json
from pathlib import Path
import shutil
import time
import uuid

from app.persistence import write_json


def clone(source, data):
    baseline = json.loads((source/'project.json').read_text(encoding='utf-8'))
    keys = ('name','seed','quality','model_family','mode','views','remove_background',
            'background_model','fidelity_settings','input_preparation','refinement','experiment')
    record = {key:copy.deepcopy(baseline[key]) for key in keys if key in baseline}
    record.setdefault('views',{'front':'input.png'})
    names = set(record['views'].values()) | {'input.png'}
    if record.get('model_family') == 'ultrashape':
        names.add('coarse.glb')
    for name in names:
        if Path(name).name != name or not (source/name).is_file():
            raise ValueError('Falta una referencia o la malla inicial para regenerar.')
    path = data/uuid.uuid4().hex
    path.mkdir()
    try:
        for name in names | {p.name for p in source.glob('source*.png')} | {'conditioning-front.png'}:
            if (source/name).is_file():
                shutil.copyfile(source/name,path/name)
        if record.get('experiment'):
            original_group = record['experiment'].pop('id',None)
            if original_group:
                record['experiment']['origin_experiment_id'] = original_group
        record.update(id=path.name,status='queued',created_at=time.time(),exports=[],
                      regenerated_from=baseline['id'])
        if record.get('model_family') == 'ultrashape':
            record['worker'] = 'ultrashape'
        write_json(path/'project.json',record)
    except Exception:
        # Only this just-created, private attempt can be rolled back.
        assert path.resolve().parent == data.resolve() and len(path.name) == 32
        shutil.rmtree(path)
        raise
    return path,record
