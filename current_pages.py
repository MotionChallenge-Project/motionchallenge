"""Render current MJWarp protocols and independently verified evidence."""
import html,json
import protocol_visuals
def render(content,models,tracks,rows,page,intro,gh):
 e=html.escape
 def model_image(m):
  return f'<img class="model-icon" src="{e(m["icon"],quote=True)}" alt="{e(m.get("icon_label") or m["display_name"],quote=True)}" width="72" height="72" loading="lazy">'
 def dataset_image(t):
  seed=t['benchmark_id']=='seed'
  return '<img class="dataset-logo '+('bones' if seed else 'ubisoft')+'" src="/assets/dataset-logos/'+('bones.svg' if seed else 'ubisoft.png')+'" alt="'+('BONES Studio' if seed else 'Ubisoft')+'" width="150" height="72">'
 def section(text):return '<section class="section docs">'+text+'</section>'
 cards=''.join(f'<a class="dataset-card" href="/benchmarks/{t["benchmark_id"]}/" aria-label="{t["benchmark_label"]}: dataset and protocol"><div class="dataset-card-brand"><span class="diagram-tag">MOTION DATASET</span>{dataset_image(t)}</div><h2>{t["benchmark_label"]}</h2><p class="dataset-size">{t["clip_count"]:,}<span>motions</span></p><p>Unitree G1 · 29 joints<br>Local original data · MJWarp · 50 Hz</p><span class="text-link">Dataset &amp; protocol →</span></a>' for t in tracks)
 page('/benchmarks/','Benchmarks',intro('DATASETS','Choose your benchmark.','Download the upstream motions and evaluate locally.')+'<section class="section dataset-grid">'+cards+'</section>','Benchmarks')
 for t in tracks:
  seed=t['benchmark_id']=='seed';path='/data/seed/g1.tar.gz' if seed else '/data/lafan'
  url='https://huggingface.co/datasets/bones-studio/seed' if seed else 'https://huggingface.co/datasets/lvhaidong/LAFAN1_Retargeting_Dataset'
  data=('We evaluate a feasibility-filtered subset of the original BONES-SEED G1 motion data. Download the original <code>g1.tar.gz</code>; the unified public inclusion list selects 129,561 motions and 113,674,960 source frames at 120 Hz. Every model is evaluated on this same fixed subset. CSV root translations are centimetres; root XYZ Euler angles and joint positions are degrees. Local conversion produces metres, XYZW quaternions and joint radians.' if seed else 'Use the 40 G1 CSV files under <code>g1/</code>, containing 264,705 source frames at 30 Hz. Rows contain root translation in metres, an XYZW quaternion and 29 joint positions in radians.')
  text=f'<h2>Original data</h2><p>{data}</p><p><a href="{url}">Download the original dataset ↗</a>. Obtain and use the files under the upstream terms. Motion data stays in your local directory.</p>'
  if seed:text+=f'<p><a href="{gh}/MotionChallenge-Core/blob/main/suites/seed/filter.json">Dataset identity ↗</a> · <a href="{gh}/MotionChallenge-Core/blob/main/suites/seed/selection.jsonl.gz">Feasibility-filtered motion list ↗</a></p><p>Conversion uses up to eight CPU workers. Archive, selection and converted poses are checked by SHA256. Subsequent models reuse the motion and scoring-reference caches.</p>'
  text+=f'<h2>Evaluate a model</h2><pre><code>uv run --locked python evaluate.py --dataset {t["benchmark_id"]} --data {path} --output results/{t["benchmark_id"]}</code></pre><p>The command obtains the pinned checkpoint, converts it for full-batch inference, validates conversion, evaluates every selected motion and independently verifies recorded pose traces.</p><h2>Evaluation</h2><p>50 Hz control and scoring; four 5 ms physics steps per control period; sliding friction 1.0; Newton solver with 50 maximum iterations. Failure is the first pelvis height error above 0.25 m or gravity-Z error above 0.8. Rollout continues to the endpoint.</p><p><a href="/protocol/">Observation rules and metrics →</a> · <a href="/?benchmark={t["benchmark_id"]}">Results →</a> · <a href="/data/protocols/{t["benchmark_id"]}.json">Frozen protocol ↓</a></p>'
  page('/benchmarks/'+t['benchmark_id']+'/',t['benchmark_label'],intro('LOCAL MOTION DATA',t['benchmark_label'],f'{t["clip_count"]:,} motions · Unitree G1 · 29 joints',dataset_image(t))+section(text),'Benchmarks')
 protocol=protocol_visuals.render()
 page('/protocol/','Evaluation protocol',intro('PROTOCOL','Evaluation standards.','Shared observation rules, failure definitions and tracking metrics. Each benchmark specifies its robot, dataset and evaluation configuration.')+'<div class="protocol-content">'+protocol+'</div>','Protocol')
 cards=[]
 for name,m in models.items():
  status=m['admission']['status'];runtime=m['runtime']
  label='Excluded: required observations' if status=='excluded' else 'Inference verified' if status=='inference_verified' else 'Validation in progress'
  cards.append(f'<article class="model-card"><a class="model-card-image" href="/models/{name}/" aria-label="{e(m["display_name"],quote=True)}">{model_image(m)}</a><h3><a href="/models/{name}/">{e(m["display_name"])}</a></h3><p>{e(m.get("organization",""))}</p><p>{label}</p></article>')
  text=f'<p><strong>{label}</strong></p><p>{e(m["admission"].get("reason",""))}</p><p><a href="{m["adapter_repository"]}">Independent model repository ↗</a> · <a href="{runtime.get("source_repository",m["adapter_repository"])}">Upstream model ↗</a></p><h2>Checkpoint</h2><p>SHA256 <code>{runtime["weights_sha256"]}</code></p>'
  origin=m.get('checkpoint_origin',{})
  if origin.get('status')=='author_release_verified':
   text+=f'<p><a href="{e(origin["author_release_url"],quote=True)}">Official author release ↗</a></p><p>{e(origin.get("verification_scope",""))}</p>'
  if runtime.get('weights_url'):text+=f'<p><a href="{e(runtime["weights_url"],quote=True)}">Pinned original weights ↗</a></p>'
  if status!='excluded':text+=f'<h2>Evaluate locally</h2><pre><code>git clone --recurse-submodules {m["adapter_repository"]}\ncd MotionChallenge-{name}\nuv sync --locked\nuv run --locked python evaluate.py --dataset lafan --data /data/lafan --output results/lafan\nuv run --locked python evaluate.py --dataset seed --data /data/seed/g1.tar.gz --output results/seed</code></pre><p>Weight download, conversion, validation, caching, full-batch rollout and trace verification are automatic.</p>'
  text+='<h2>Metric</h2><p>MPKPE (Mean Per-Keypoint Position Error) measures the 3D Euclidean distance between actual and reference keypoint positions. The protocol defines these keypoints at robot body-frame origins: 14 points for G1. Errors are averaged over keypoints and scoring samples within each motion, then motions are weighted equally. Results report full-motion and first-failure-prefix scores with no alignment, XY alignment, and XY + yaw alignment. XY alignment removes pelvis horizontal translation while retaining height error. Leaderboard values are reported in millimetres (mm).</p>'
  related=[r for r in rows if r['model']==name]
  text+='<h2>Verified evaluations</h2>'+(''.join(f'<p><a href="/evaluations/{r["track_id"]}/{name}/">{r["benchmark_label"]}: {r["passed"]:,}/{r["total"]:,} successful motions →</a></p>' for r in related) or ('<p>No ranked full-suite result.</p>' if status=='excluded' or m.get('evaluation_issues') else '<p>Full-suite results are in validation.</p>'))
  if m.get('evaluation_issues'):
   text+='<h2>Evaluation status</h2>'
   for issue in m['evaluation_issues']:text+=f'<p>{e(issue["message"])}</p><p><a href="{e(issue["evidence"],quote=True)}">Numerical diagnostic evidence ↗</a></p>'
  page('/models/'+name+'/',m['display_name'],intro(m.get('organization',''),e(m['display_name']),e(m.get('version','')),model_image(m))+section(text),'Models')
 page('/models/','Models',intro('CONTROLLERS','Independent model packages.','Each checkpoint has its own adapter, converter and pinned dependencies.')+'<section class="section model-grid">'+''.join(cards)+'</section>','Models')
 for r in rows:
  evidence=json.loads((content/'evidence'/r['evidence_file']).read_text())
  text=f'<p>{r["passed"]:,}/{r["total"]:,} successful motions · {r["completion_pct"]:.2f}% completion</p><p>Protocol <code>{e(evidence["protocol_id"])}</code></p><p>Result SHA256 <code>{evidence["result_sha256"]}</code></p>'
  text+='<p>MPKPE (Mean Per-Keypoint Position Error) measures the 3D Euclidean distance between actual and reference keypoint positions. The protocol defines these keypoints at robot body-frame origins: 14 points for G1. Errors are averaged over keypoints and scoring samples within each motion, then motions are weighted equally. Results report full-motion and first-failure-prefix scores with no alignment, XY alignment, and XY + yaw alignment. XY alignment removes pelvis horizontal translation while retaining height error. Leaderboard values are reported in millimetres (mm).</p>'
  for span,title in [('prefix','Prefix through first failure'),('full','Full motion')]:
   anchor='none' if span=='full' else 'early'
   text+=f'<h2 id="{anchor}">{title}</h2><table><thead><tr><th>Metric</th><th>Value</th></tr></thead><tbody>'
   for key,value in evidence['summary'][span].items():
    unit='mm' if key.endswith('_m') else 'rad' if key.endswith('_rad') else ''
    value=value*1000 if unit=='mm' else value
    label={'mpkpe_world_m':'MPKPE · No alignment','mpkpe_xy_aligned_m':'MPKPE · XY only','mpkpe_xy_yaw_aligned_m':'MPKPE · XY + yaw'}.get(key,key)
    text+=f'<tr><td>{e(label)}</td><td>{value:.5f} {unit}</td></tr>'
   text+='</tbody></table>'
  text+=f'<h2>Evidence</h2><p><a href="/data/evidence/{r["evidence_file"]}">Source hashes and verification receipt (JSON) ↓</a></p><p>The receipt binds the full result and pose-trace manifest. Full artifacts remain with the evaluation output.</p>'
  if evidence.get('reproduction'):
   repro=evidence['reproduction'];text+='<h2>Reproduction</h2><p>Independent pipeline run completed with matching identities. Numerical differences are recorded in the evidence JSON.</p>'
   if repro.get('summary_delta_second_minus_first'):text+='<pre><code>'+e(json.dumps(repro['summary_delta_second_minus_first'],indent=2))+'</code></pre>'
  text+=f'<h2>Run locally</h2><pre><code>uv run --locked python evaluate.py --dataset {r["benchmark_id"]} --data /data/{"seed/g1.tar.gz" if r["benchmark_id"]=="seed" else "lafan"} --output results/{r["benchmark_id"]}</code></pre>'
  page(f'/evaluations/{r["track_id"]}/{r["model"]}/',models[r['model']]['display_name']+' · '+r['benchmark_label'],intro(r['benchmark_label'],e(models[r['model']]['display_name']),'Complete rollout · independently verified pose traces')+section(text),'Leaderboard')
 page('/submit/','Submit a controller',(content.parent/'submit_page.html').read_text(),'Submit')
 page('/about/','About MotionChallenge',intro('ABOUT','Open motion-tracking evaluation.','Public model packages, fixed protocols and independently verified evidence.')+section('<p>MotionChallenge evaluates G1 motion tracking on LAFAN1 and BONES-SEED. Thanks to the model authors, LAFAN1, the LAFAN1 Retargeting Dataset, BONES Studio, MuJoCo, Warp and mjlab.</p>'),'About')

