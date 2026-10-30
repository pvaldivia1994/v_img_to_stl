import json
import sys

import pytest

from app.persistence import write_json
from scripts import refine_ultrashape as worker


@pytest.mark.parametrize('failure',[False,True])
def test_local_validation_marker_requires_a_completed_probe_and_creates_tracker_directories(tmp_path,monkeypatch,failure):
    data=tmp_path/'data/projects'
    path=data/'probe'
    path.mkdir(parents=True)
    source=tmp_path/'ultrashape-source'
    source.mkdir()
    record={'id':'probe','status':'queued','worker':'ultrashape','seed':42,
            'refinement':{'steps':2,'latents':32768,'resolution':32,'chunks':512,'sequential_cfg':True}}
    write_json(path/'project.json',record)
    monkeypatch.setattr(worker,'DATA',data)
    monkeypatch.setattr(worker,'SOURCE',source)
    monkeypatch.setattr(sys,'argv',['refine_ultrashape','probe','--prepared','--validation-only'])
    def probe(args,path,record,progress):
        if failure:
            raise RuntimeError('GPU compatibility test failed')
        record.update(status='ready',gpu_peak_allocated_mib=5009,gpu_peak_reserved_mib=7630)
        progress.stage(7,'Finished',1,1)
    monkeypatch.setattr(worker,'refine',probe)
    if failure:
        with pytest.raises(RuntimeError,match='compatibility'):
            worker.main()
        assert not (source/'forma-validated.json').exists()
    else:
        worker.main()
        result=json.loads((source/'forma-validated.json').read_text(encoding='utf-8'))
        assert result['probe_project']=='probe' and result['latents']==32768
    assert (tmp_path/'data/fidelity-fox/latest-ultrashape-project-id.txt').read_text()=='probe'
