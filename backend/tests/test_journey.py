import copy
import unittest
from backend.journey import validate_journey, validate_anchors

class JourneyTests(unittest.TestCase):
    def test_selection_preserves_unknown_and_normalized_points(self):
        state={'step':'keep','keepingDecision':'later','selectedCategories':['Chairs','Chairs'],
               'retainedObjects':[{'id':'t1','label':'Table','variant':'Oak','confirmed':False,
                                   'anchor':{'x':.2,'y':.8,'imageUrl':'/api/assets/photo.png'}}]}
        original=copy.deepcopy(state)
        clean=validate_journey(state)
        self.assertEqual(clean['keepingDecision'],'later')
        self.assertFalse(clean['retainedObjects'][0]['confirmed'])
        self.assertEqual(clean['selectedCategories'],['Chairs'])
        self.assertEqual(state,original)
        validate_anchors(clean, {'imageUrl':'/api/assets/photo.png'})
        with self.assertRaises(ValueError):validate_anchors(clean,{'imageUrl':'/api/assets/new.png'})
        with self.assertRaises(ValueError):validate_anchors(clean,None)

    def test_closed_schema_and_invalid_geometry(self):
        for state in ({'step':'purchase'},{'retainedObjects':[{'id':'x','label':'Table','variant':'','confirmed':True,'anchor':{'x':float('nan'),'y':0,'imageUrl':'x'}}]},
                      {'roomMeasurements':{'width':True}}, {'selectedCategories':['a']*11},
                      {'keepingDecision':'replace_all'}, {'apiKey':'hidden'}):
            with self.subTest(state=state),self.assertRaises(ValueError):validate_journey(state)
