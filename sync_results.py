"""Collect verified MJWarp runs into the local website repository."""
import argparse,hashlib,json,math,shutil
from pathlib import Path

def sha(path):
 with Path(path).open('rb') as f:return hashlib.file_digest(f,'sha256').hexdigest()

def main():
 p=argparse.ArgumentParser();p.add_argument('--workspace',type=Path,required=True);args=p.parse_args()
 base=args.workspace.resolve();site=Path(__file__).resolve().parent;content=site/'content';core=base/'MotionChallenge-Core'
 catalog=json.loads((content/'models.json').read_text())
 keep=('organization','organization_source','version','version_kind','family','display_name','controller_type','icon','icon_label','icon_source','project_url','adapter_repository')
 models={}
 for name,old in catalog.items():
  if name in {'scalebfm','sonic'}:continue
  root=base/('MotionChallenge-'+name)
  if not (root/'runtime.mjwarp.json').exists():continue
  item={k:v for k,v in old.items() if k in keep};item['runtime']=json.loads((root/'runtime.mjwarp.json').read_text());item['admission']=json.loads((root/'admission.mjwarp.json').read_text());models[name]=item
  origin=root/'validation/checkpoint-origin.json'
  item['checkpoint_origin']=json.loads(origin.read_text()) if origin.exists() else {'status':'source_verification_pending'}
 for name,item in models.items():
  issues=[]
  for dataset,label in [('lafan','LAFAN'),('seed','BONES-SEED')]:
   failure=base/('MotionChallenge-'+name)/f'validation/{dataset}-numerical-failure.json'
   if failure.exists():
    issues.append({'dataset':dataset,'message':label+' full-suite simulation encountered numerical instability. Inference parity passed; no complete score is ranked.','evidence':'https://github.com/MotionChallenge-Project/MotionChallenge-'+name+f'/blob/main/validation/{dataset}-numerical-failure.json'})
  if issues:item['evaluation_issues']=issues
 tracks=[]
 (content/'protocols').mkdir(exist_ok=True)
 for name,label,count in [('lafan','LAFAN1',40),('seed','BONES-SEED',129561)]:
  source=core/f'suites/{name}/protocol.mjwarp311-no-linear-velocity-v1.json';protocol=json.loads(source.read_text())
  shutil.copy2(source,content/'protocols'/f'{name}.json')
  tracks.append({'id':name+'-g1-mjwarp-no-linear-velocity-v1','benchmark_id':name,'benchmark_label':label,'robot_id':'g1-29dof','robot_label':'Unitree G1 · 29 DoF','clip_count':count,'protocol_id':protocol['id'] if 'id' in protocol else protocol['protocol_id'],'protocol_sha256':sha(source),'state_access':'proprioceptive-no-position-no-linear-velocity-v1','primary_metric':'passed'})
 track_by_name={x['benchmark_id']:x for x in tracks}
 evidence_dir=content/'evidence';evidence_dir.mkdir(exist_ok=True)
 selected={};rejected=[]
 by_runtime={m['runtime']['id']:name for name,m in models.items()}
 production=('tensor_adapter.py','tensor_policy.py','torch_policy.py','torch_graph.py','reference_model.py','tensor_common.py','tensor_reference.py')
 for path in sorted((base/'runs').glob('*/result.json'),key=lambda p:p.stat().st_mtime):
  try:
   result=json.loads(path.read_text())
   if result.get('status')!='unverified_full_rollout' or not result.get('traces_recorded'):continue
   verification_path=path.with_name('verification.json')
   if not verification_path.exists():continue
   verification=json.loads(verification_path.read_text());digest=sha(path)
   if verification.get('verification')!='independent_cpu_trace_recomputation_passed' or verification.get('result_sha256')!=digest:continue
   runtime_path=path.with_name('runtime.json');runtime=json.loads(runtime_path.read_text())
   if sha(runtime_path)!=result['runtime_sha256']:raise ValueError('Runtime snapshot hash mismatch')
   name=by_runtime.get(runtime['id'])
   if name is None:continue
   model=models[name];root=base/('MotionChallenge-'+name)
   if model['admission']['status']!='inference_verified':continue
   origin=model['checkpoint_origin']
   if origin.get('status')!='author_release_verified' or origin.get('sha256')!=model['runtime']['weights_sha256']:continue
   if result['checkpoint_sha256']!=model['runtime']['weights_sha256']:continue
   # Evidence/admission records can be added after a run. Compare execution fields.
   fields=('tensor_entrypoint','inference_config_sha256','control_period_s','reference_offsets_s','weights_sha256')
   if any(runtime.get(k)!=model['runtime'].get(k) for k in fields):continue
   if any(file in result['adapter_sha256'] and (not (root/file).exists() or sha(root/file)!=result['adapter_sha256'][file]) for file in production):continue
   dataset=result['dataset'];track=track_by_name[dataset]
   if result['protocol_sha256']!=track['protocol_sha256']:continue
   if len(result['clips'])!=track['clip_count'] or verification['clips']!=track['clip_count']:continue
   if len({x['name'] for x in result['clips']})!=track['clip_count']:raise ValueError('Duplicate motion')
   engine=result['engine']
   if engine.get('substeps')!=4 or engine.get('njmax')!=4096 or engine.get('nconmax')!=100:continue
   if not all(math.isfinite(v) for span in ['full','prefix'] for v in result['summary'][span].values()):raise ValueError('Nonfinite metrics')
   selected[(name,dataset)]=(path,result,verification,digest)
  except (ValueError,KeyError,OSError) as error:rejected.append({'path':str(path),'reason':str(error)})
 rows=[]
 for (name,dataset),(path,result,verification,digest) in sorted(selected.items()):
  model=models[name];track=track_by_name[dataset];summary=result['summary']
  evidence={k:result[k] for k in ['protocol_id','protocol_sha256','checkpoint_sha256','runtime_sha256','source_sha256','adapter_sha256','converted_weights_sha256','dataset_identity','engine','control_period_s','physics_dt_s','summary','timing','traces']}
  evidence.update(checkpoint_origin=model['checkpoint_origin'],result_sha256=digest,clips=len(result['clips']),verification=verification,runtime_snapshot=json.loads(path.with_name('runtime.json').read_text()),inference_admission=model['admission'],inference_admission_sha256=sha(base/('MotionChallenge-'+name)/'admission.mjwarp.json'))
  repro=base/('MotionChallenge-'+name)/f'validation/{dataset}-reproduction.json'
  if repro.exists():
   report=json.loads(repro.read_text())
   if report.get('status')=='pipeline_reproduction_passed' and digest in [report.get('first_result_sha256'),report.get('second_result_sha256')]:evidence['reproduction']=report
  filename=name+'.'+dataset+'.json';target=evidence_dir/filename
  target.write_text(json.dumps(evidence,indent=2)+'\n')
  row={'model':name,'label':model['display_name'],'version':model.get('version',''),'organization':model.get('organization',''),'controller_type':model['controller_type'],'icon':model.get('icon'),'icon_label':model.get('icon_label',''),'benchmark_id':dataset,'benchmark_label':track['benchmark_label'],'robot_id':track['robot_id'],'track_id':track['id'],'termination_mode':'unified','failed':track['clip_count']-summary['success_count'],'passed':summary['success_count'],'total':track['clip_count'],'completion_pct':100*summary['completion'],'evidence_file':filename,'evidence_sha256':sha(target),'verification':'independent_cpu_trace_recomputation_passed'}
  for span,prefix in [('full','full_'),('prefix','')]:
   for key,value in summary[span].items():row[prefix+key]=value
  rows.append(row)
 (content/'models.json').write_text(json.dumps(models,indent=2)+'\n')
 (content/'tracks.json').write_text(json.dumps(tracks,indent=2)+'\n')
 (content/'results.json').write_text(json.dumps({'rows':rows},indent=2)+'\n')
 import publication_checks
 publication_checks.validate(content,rows,models,tracks)
 (base/'website-sync-report.json').write_text(json.dumps({'selected':{name+'/'+dataset:str(value[0]) for (name,dataset),value in selected.items()},'rejected':rejected},indent=2)+'\n')
 print(json.dumps({'models':len(models),'verified_results':len(rows),'lafan':sum(x['benchmark_id']=='lafan' for x in rows),'seed':sum(x['benchmark_id']=='seed' for x in rows),'rejected':len(rejected)}))
if __name__=='__main__':main()

