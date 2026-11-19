import copy,json,sys,tempfile,unittest
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
import publication_checks
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
  self.assertTrue(self.rows);rows=copy.deepcopy(self.rows);rows[0]['full_mpjpe_xy_aligned_m']+=.01
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
if __name__=='__main__':unittest.main()
