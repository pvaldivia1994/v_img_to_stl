import numpy as np
from PIL import Image
from app.reference_preparation import REFERENCE, REGIONS, split_known_sheet, prepare_ai_cutout


def test_known_sheet_split_uses_real_back_and_leaves_other_images_alone():
    with Image.open(REFERENCE) as sheet:
        views, meta = split_known_sheet(sheet.convert('RGB'),'hunyuan2')
        assert set(views) == {'front','back'}
        assert meta['regions']['back'] == REGIONS['back']
        assert views['back'].width == REGIONS['back'][2]-REGIONS['back'][0]
        single, _ = split_known_sheet(sheet.convert('RGB'),'hunyuan21')
        assert set(single) == {'front'}
        changed = sheet.convert('RGB')
        changed.putpixel((0,0),(1,2,3))
        assert split_known_sheet(changed,'hunyuan2') == (None,None)


def test_alpha_cleanup_preserves_main_rgb_and_internal_holes():
    image = Image.new('RGBA',(60,60),(0,0,0,0))
    image.paste((90,100,110,255),(10,10,45,45))
    image.paste((255,255,255,0),(20,20,30,30))
    image.putpixel((55,55),(120,0,0,255))
    rgba,rgb,meta = prepare_ai_cutout(image)
    assert meta['alpha_speckle_pixels_removed'] == 1
    assert np.sum(np.asarray(rgba)[...,3] == 255) == 35*35-100
    assert set(map(tuple,np.asarray(rgba)[np.asarray(rgba)[...,3]>0,:3])) == {(90,100,110)}
    assert rgba.width == rgba.height
    assert tuple(np.asarray(rgb)[0,0]) == (255,255,255)
