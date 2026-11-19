"""Check evidence before building public MJWarp result pages."""
import hashlib,json,math
import run_compatibility
def digest(path):return hashlib.sha256(path.read_bytes()).hexdigest()
def validate(content,rows,models,tracks):
 by_id={t['id']:t for t in tracks};seen=set()
 core_manifest=json.loads((content/'evaluation-source.json').read_text())
 for row in rows:
  key=(row['model'],row['track_id'])
  if key in seen:raise ValueError('Duplicate leaderboard entry')
  seen.add(key);track=by_id[row['track_id']]
  model=models[row['model']]
  if model['admission']['status']!='inference_verified':raise ValueError('Model inference is not admitted')
  origin=model.get('checkpoint_origin',{})
  if origin.get('status')!='author_release_verified' or origin.get('sha256')!=model['runtime']['weights_sha256']:raise ValueError('Official author checkpoint is not verified')
  if not origin.get('author_release_url') or not origin.get('artifact_url'):raise ValueError('Official checkpoint source links are missing')
  evidence=json.loads((content/'evidence'/row['evidence_file']).read_text())
  if row['evidence_sha256']!=digest(content/'evidence'/row['evidence_file']):raise ValueError('Evidence digest mismatch')
  verify=evidence['verification']
  if verify['verification']!='independent_cpu_trace_recomputation_passed' or verify['result_sha256']!=evidence['result_sha256']:raise ValueError('Result is not independently verified')
  if evidence['clips']!=track['clip_count'] or verify['clips']!=track['clip_count']:raise ValueError('Incomplete dataset')
  if row['total']!=track['clip_count']:raise ValueError('Leaderboard total mismatch')
  if evidence['protocol_sha256']!=track['protocol_sha256']:raise ValueError('Wrong protocol')
  protocol_path=content/'protocols'/(track['benchmark_id']+'.json')
  if digest(protocol_path)!=track['protocol_sha256']:raise ValueError('Protocol digest mismatch')
  protocol=json.loads(protocol_path.read_text())
  run_compatibility.validate_run(evidence,evidence['runtime_snapshot'],model,core_manifest)
  engine=evidence['engine']
  if engine['backend']!='mjwarp' or engine['substeps']!=4 or engine['njmax']!=4096 or engine['nconmax']!=100:raise ValueError('Unexpected simulator configuration')
  if engine['versions']!=protocol['engine_versions'] or engine['worlds']!=min(track['clip_count'],4096):raise ValueError('Unexpected engine versions or batch size')
  if evidence['control_period_s']!=protocol['control_period_s'] or evidence['physics_dt_s']!=protocol['physics_dt_s']:raise ValueError('Unexpected evaluation clock')
  if evidence['checkpoint_sha256']!=model['runtime']['weights_sha256']:raise ValueError('Checkpoint mismatch')
  if evidence.get('checkpoint_origin')!=origin:raise ValueError('Checkpoint origin evidence mismatch')
  summary=evidence['summary']
  if row.get('failed')!=track['clip_count']-summary['success_count']:raise ValueError('Failed-motion count mismatch')
  if row['passed']!=summary['success_count'] or row['completion_pct']!=100*summary['completion']:raise ValueError('Summary mismatch')
  if not 0<=row['passed']<=track['clip_count'] or not 0<=row['completion_pct']<=100:raise ValueError('Invalid success or completion')
  for span,prefix in [('full','full_'),('prefix','')]:
   for name,value in summary[span].items():
    if not math.isfinite(value) or value<0:raise ValueError('Invalid metric')
    if name.startswith('mpjpe_') and row[prefix+name]!=value:raise ValueError('Leaderboard metric mismatch')
