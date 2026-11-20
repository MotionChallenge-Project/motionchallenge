import copy,json,sys,tempfile,unittest,shutil
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
import publication_checks
import run_compatibility
class PublicationTests(unittest.TestCase):
 def setUp(self):
  self.content=Path(__file__).resolve().parents[1]/'content'
  self.rows=json.loads((self.content/'results.json').read_text())['rows']
  self.models=json.loads((self.content/'models.json').read_text())
  self.tracks=json.loads((self.content/'tracks.json').read_text())
 def check(self,rows=None,models=None,tracks=None):
  publication_checks.validate(self.content,self.rows if rows is None else rows,self.models if models is None else models,self.tracks if tracks is None else tracks)
 def test_evidence(self):self.check()
 def test_changed_metric_rejected(self):
  self.assertTrue(self.rows);rows=copy.deepcopy(self.rows);rows[0]['full_mpkpe_xy_aligned_m']+=.01
  with self.assertRaisesRegex(ValueError,'metric mismatch'):self.check(rows=rows)
 def test_excluded_model_rejected(self):
  models=copy.deepcopy(self.models);models[self.rows[0]['model']]['admission']['status']='excluded'
  with self.assertRaisesRegex(ValueError,'not admitted'):self.check(models=models)
 def test_wrong_cohort_rejected(self):
  tracks=copy.deepcopy(self.tracks)
  for t in tracks:
   if t['id']==self.rows[0]['track_id']:t['clip_count']+=1
  with self.assertRaisesRegex(ValueError,'Incomplete'):self.check(tracks=tracks)
 def test_duplicate_rejected(self):
  with self.assertRaisesRegex(ValueError,'Duplicate'):self.check(rows=[*self.rows,self.rows[0]])
 def test_evidence_digest_rejected(self):
  rows=copy.deepcopy(self.rows);rows[0]['evidence_sha256']='0'*64
  with self.assertRaisesRegex(ValueError,'digest mismatch'):self.check(rows=rows)
 def test_unverified_checkpoint_source_rejected(self):
  models=copy.deepcopy(self.models);models[self.rows[0]['model']]['checkpoint_origin']['status']='third_party_export'
  with self.assertRaisesRegex(ValueError,'Official author checkpoint'):self.check(models=models)
 def test_failed_motion_count_rejected(self):
  rows=copy.deepcopy(self.rows);rows[0]['failed']+=1
  with self.assertRaisesRegex(ValueError,'Failed-motion count'):self.check(rows=rows)
 def test_total_rejected(self):
  rows=copy.deepcopy(self.rows);rows[0]['total']+=1
  with self.assertRaisesRegex(ValueError,'total mismatch'):self.check(rows=rows)
 def mutate_evidence(self,change,message):
  with tempfile.TemporaryDirectory() as tmp:
   content=Path(tmp)/'content';shutil.copytree(self.content,content)
   rows=copy.deepcopy(self.rows);path=content/'evidence'/rows[0]['evidence_file']
   evidence=json.loads(path.read_text());change(evidence);path.write_text(json.dumps(evidence))
   rows[0]['evidence_sha256']=publication_checks.digest(path)
   with self.assertRaisesRegex(ValueError,message):
    publication_checks.validate(content,rows,self.models,self.tracks)
 def test_stale_physics_rejected(self):
  self.mutate_evidence(lambda e:e['source_sha256'].__setitem__('simulation/warp_physics.py','0'*64),'Evaluator source mismatch')
 def test_missing_evaluator_source_rejected(self):
  self.mutate_evidence(lambda e:e['source_sha256'].pop('evaluation/tensor_metrics.py'),'Evaluator source mismatch')
 def test_changed_model_helper_rejected(self):
  names=self.models[self.rows[0]['model']]['evaluation_source_sha256']
  helper=next(n for n in names if n!='tensor_adapter.py')
  self.mutate_evidence(lambda e:e['adapter_sha256'].__setitem__(helper,'0'*64),'Model inference source mismatch')
 def test_changed_runtime_dynamics_rejected(self):
  self.mutate_evidence(lambda e:e['runtime_snapshot'].__setitem__('action_mode','different'),'Runtime execution fields mismatch')
 def test_wrong_engine_version_rejected(self):
  self.mutate_evidence(lambda e:e['engine']['versions'].__setitem__('mujoco','0.0.0'),'engine versions')
 def test_model_import_closure(self):
  with tempfile.TemporaryDirectory() as tmp:
   root=Path(tmp);(root/'policy').mkdir()
   (root/'tensor_adapter.py').write_text('from policy.network import Policy\nimport torch\n')
   (root/'policy/__init__.py').write_text('from . import helpers\n')
   (root/'policy/network.py').write_text('from .helpers import scale\nclass Policy: pass\n')
   (root/'policy/helpers.py').write_text('scale = 1\n')
   (root/'validate.py').write_text('pass\n')
   self.assertEqual(set(run_compatibility.model_sources(root,'tensor_adapter:Policy')),{'tensor_adapter.py','policy/__init__.py','policy/network.py','policy/helpers.py'})
if __name__=='__main__':unittest.main()
