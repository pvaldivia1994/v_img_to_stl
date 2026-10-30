import asyncio
import copy

import pytest

from app import main
from app.progress import apply_event, set_stage
from app.profiles import apply_profile
from app.workflows import build_workflow


@pytest.fixture
def record():
    return {'id': 'sample', 'prompt_id': 'owned', 'status': 'running',
            'prompt': build_workflow({'front': 'front.png', 'back': 'back.png'}, 42, 'mesh/test')}


def test_progress_is_owned_and_reports_stage_not_total(record):
    assert not apply_event(record, {'type': 'progress', 'data': {'prompt_id': 'other', 'node': '3', 'value': 10, 'max': 50}})
    assert 'progress' not in record
    assert apply_event(record, {'type': 'progress', 'data': {'prompt_id': 'owned', 'node': '3', 'value': 25, 'max': 50}})
    assert record['progress']['stage'] == 'shape'
    assert record['progress']['percent'] == 50
    apply_event(record, {'type': 'executing', 'data': {'prompt_id': 'owned', 'node': '61'}})
    assert record['progress']['stage'] == 'details'
    assert record['progress']['percent'] is None


def test_volume_progress_uses_real_counts_and_no_early_completion(record):
    apply_profile(record['prompt'], 'maximum')
    apply_event(record, {'type': 'progress_state', 'data': {'prompt_id': 'owned', 'nodes': {
        '3': {'node_id': '3', 'state': 'finished', 'value': 50, 'max': 50},
        '61': {'node_id': '61', 'state': 'running', 'value': 1000, 'max': 2000},
    }}})
    assert record['progress']['stage'] == 'details'
    assert record['progress']['percent'] == 50
    apply_event(record, {'type': 'executing', 'data': {'prompt_id': 'owned', 'node': None}})
    assert record['status'] == 'running'
    assert record['progress']['stage'] == 'saving'
    assert record['progress']['percent'] is None
    # A cached/preparation event arriving late cannot reset the active stage.
    assert not apply_event(record, {'type': 'executing', 'data': {'prompt_id': 'owned', 'node': '54'}})


def test_finished_project_cannot_be_overwritten_by_late_events(record):
    set_stage(record, 'complete', 1, 1)
    record['status'] = 'ready'
    previous = copy.deepcopy(record)
    assert not apply_event(record, {'type': 'progress', 'data': {'prompt_id': 'owned', 'node': '61', 'value': 1, 'max': 2}})
    assert record == previous


def test_maximum_profile_keeps_latent_capacity_and_changes_field_resolution():
    prompt = build_workflow({'front': 'front.png', 'back': 'back.png'}, 42, 'mesh/test')
    apply_profile(prompt, 'maximum')
    assert prompt['66']['inputs']['resolution'] == 3072
    assert prompt['3']['inputs']['steps'] == 50
    assert prompt['61']['class_type'] == 'FormaVAEDecodeHunyuan3D'
    assert prompt['61']['inputs'] == {'samples': ['3', 0], 'vae': ['54', 2], 'num_chunks': 4000, 'octree_resolution': 512}
