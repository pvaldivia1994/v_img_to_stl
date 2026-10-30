import copy
import numpy as np
import pytest
from PIL import Image
from app.fidelity import frame_reference, apply_fidelity
from app.workflows import build_workflow
from app.profiles import apply_profile


def test_frame_preserves_pixels_and_has_requested_margin():
    image = Image.new('RGB', (140, 100), 'white')
    image.paste(Image.new('RGB', (80, 60), (110, 90, 80)), (20, 10))
    framed = frame_reference(image, .85)
    points = np.where(np.any(np.asarray(framed) < 245, axis=2))
    assert framed.width == framed.height
    assert abs((points[1].max()-points[1].min()+1)/framed.width - .85) < .01
    assert np.sum(np.any(np.asarray(framed) < 245, axis=2)) == 80*60
    with pytest.raises(ValueError):
        frame_reference(Image.new('RGB', (20, 20), 'white'))


def test_fidelity_changes_only_recorded_parameters_and_rejects_unsupported_resolution():
    prompt = apply_profile(build_workflow({'front':'front.png'}, 42, 'mesh/test', 'hunyuan21'), 'maximum')
    baseline = copy.deepcopy(prompt)
    apply_fidelity(prompt, {'steps':75, 'threshold':.5})
    assert prompt['3']['inputs']['steps'] == 75
    assert prompt['62']['inputs']['threshold'] == .5
    assert prompt['54'] == baseline['54']
    assert prompt['61'] == baseline['61']
    assert prompt['3']['inputs']['cfg'] == 5
    for settings in ({'threshold':0}, {'threshold':float('nan')}, {'octree_resolution':768}, {'fake':1}):
        with pytest.raises(ValueError):
            apply_fidelity(prompt, settings)
