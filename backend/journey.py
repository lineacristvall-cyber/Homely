"""Bounded, versioned progressive room setup; photo points are manual annotations."""
import copy
import math

STEPS = {'room', 'intent', 'photo', 'measurements', 'keep', 'categories', 'preferences', 'fit', 'results', 'saved'}

def _text(value, limit=100):
    if not isinstance(value, str) or len(value.strip()) > limit:
        raise ValueError('Setup text exceeds its allowed size.')
    return value.strip()

def validate_journey(value):
    if value is None:
        return {}
    if not isinstance(value, dict) or set(value) - {'step','selectedCategories','retainedObjects','keepingDecision','roomMeasurements','categoryOther','categoryGuideIndex','resultMode'}:
        raise ValueError('Unsupported room setup fields.')
    out = copy.deepcopy(value)
    if 'step' in out and out['step'] not in STEPS:
        raise ValueError('Unsupported room setup step.')
    if out.get('keepingDecision') not in (None, 'keep','fresh','later'):
        raise ValueError('Choose whether to keep furniture, start fresh or decide later.')
    if out.get('resultMode') not in (None, 'fit','inspiration'):
        raise ValueError('Choose fitting recommendations or inspiration.')
    if 'selectedCategories' in out:
        items = out['selectedCategories']
        if not isinstance(items,list) or len(items)>10:
            raise ValueError('Choose up to ten categories.')
        out['selectedCategories'] = list(dict.fromkeys(_text(x) for x in items))
    if 'categoryOther' in out:
        out['categoryOther'] = _text(out['categoryOther'])
    if 'categoryGuideIndex' in out and (type(out['categoryGuideIndex']) is not int or not 0 <= out['categoryGuideIndex'] <= 20):
        raise ValueError('Invalid category question.')
    if 'roomMeasurements' in out:
        dimensions=out['roomMeasurements']
        if not isinstance(dimensions,dict) or set(dimensions)-{'width','depth','height','unit'} or dimensions.get('unit','in') not in ('in','cm'):
            raise ValueError('Invalid room measurements.')
        for key,number in dimensions.items():
            if key=='unit' or number is None: continue
            if isinstance(number,bool) or not isinstance(number,(int,float)) or not math.isfinite(number) or number<=0 or number>100000:
                raise ValueError('Room dimensions must be positive finite measurements.')
    if 'retainedObjects' in out:
        items=out['retainedObjects']
        if not isinstance(items,list) or len(items)>20:
            raise ValueError('Keep up to twenty objects.')
        seen=set()
        for obj in items:
            if not isinstance(obj,dict) or set(obj)-{'id','label','variant','confirmed','anchor'}:
                raise ValueError('Invalid retained object.')
            for k in ('id','label','variant'):
                obj[k]=_text(obj.get(k,''),100)
            if not obj['id'] or obj['id'] in seen or not obj['label'] or type(obj.get('confirmed')) is not bool:
                raise ValueError('Retained objects need a unique ID, label and explicit confirmation.')
            seen.add(obj['id'])
            if obj.get('anchor') is not None:
                anchor=obj['anchor']
                if not isinstance(anchor,dict) or set(anchor)!={'x','y','imageUrl'}:
                    raise ValueError('Invalid photo annotation.')
                for k in ('x','y'):
                    n=anchor[k]
                    if isinstance(n,bool) or not isinstance(n,(int,float)) or not math.isfinite(n) or not 0<=n<=1:
                        raise ValueError('Photo annotations must lie inside the image.')
                anchor['imageUrl']=_text(anchor['imageUrl'],2048)
    return out


def validate_anchors(journey, room):
    """A point may refer only to this project's current uploaded room."""
    current=(room or {}).get('imageUrl')
    for obj in (journey or {}).get('retainedObjects',[]):
        if obj.get('anchor') and (not current or obj['anchor']['imageUrl'] != current):
            raise ValueError('This photo selection is stale. Select the object on the current room photo.')
