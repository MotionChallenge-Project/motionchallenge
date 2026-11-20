from pathlib import Path
import json,html,shutil,os,re,hashlib
from datetime import datetime, timezone
import current_pages
import publication_checks
ROOT=Path(__file__).parent;D=ROOT/'docs';D.mkdir(exist_ok=True)
# These folders contain only generated pages and exported evidence.
for generated in ('models','evaluations','data','benchmarks','protocol','admission','overview','coverage','leaderboard'):
 path=D/generated
 if path.exists():shutil.rmtree(path)
GH='https://github.com/MotionChallenge-Project'
BASE=os.environ.get('SITE_BASE_PATH','/motionchallenge').rstrip('/')
SITE_URL='https://motionchallenge-project.github.io'+BASE
WEBSITE_SOURCE=GH+'/motionchallenge/tree/website'
UPDATED=datetime.now(timezone.utc).replace(second=0,microsecond=0)
UPDATE_TIME=f'<time datetime="{UPDATED.isoformat()}">{UPDATED.strftime("%d %b %Y, %H:%M UTC")}</time>'
NAMES={'grit':'GRIT','heft':'HEFT','sonic':'SONIC','mimic-lite':'MimicLite','scalebfm':'ScaleBFM','holomotion':'HoloMotion','humanoid-gpt':'Humanoid-GPT','protomotions':'ProtoMotions','bfm-zero':'BFM-Zero','twist2':'TWIST2'}
CONTENT=ROOT/'content'
CITATION=(CONTENT/'citation.bib').read_text()
MODELS=json.loads((CONTENT/'models.json').read_text())
TRACKS=json.loads((CONTENT/'tracks.json').read_text())
rows=json.loads((CONTENT/'results.json').read_text())['rows']
publication_checks.validate(CONTENT,rows,MODELS,TRACKS)
RESULTS_REVISION=hashlib.sha256((CONTENT/'results.json').read_bytes()).hexdigest()[:12]
ASSET_REVISION=hashlib.sha256((ROOT/'style.css').read_bytes()+(ROOT/'app.js').read_bytes()).hexdigest()[:12]
(D/'data').mkdir(exist_ok=True)
(D/'data/results.json').write_text(json.dumps({'tracks':TRACKS,'rows':rows},indent=2))
nav=[('Leaderboard','/'),('Benchmarks','/benchmarks/'),('Models','/models/'),('Protocol','/protocol/'),('Submit','/submit/')]
def page(path,title,body,active,canonical_path=None):
 folder=D/path.strip('/');folder.mkdir(exist_ok=True,parents=True)
 links=''.join(f'<a href="{url}" '+('aria-current="page"' if label==active else '')+f'>{label}</a>' for label,url in nav)
 (folder/'index.html').write_text(f'''<!doctype html><html lang="en"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><title>{title} · MotionChallenge</title><meta name="site-base-path" content="{BASE}"><meta name="results-revision" content="{RESULTS_REVISION}"><link rel="canonical" href="{SITE_URL}{canonical_path or path}"><link rel="icon" type="image/png" href="/assets/favicon.png"><meta name="description" content="An open, reproducible benchmark for humanoid motion tracking. Shared evaluation rules, public code and verified results."><link rel="stylesheet" href="/style.css?v={ASSET_REVISION}"><script src="/app.js?v={ASSET_REVISION}" defer></script></head><body><a class="skip" href="#main">Skip to content</a><header><a class="brand" href="/"><span class="mark">m<span>c</span></span><span>MotionChallenge</span></a><nav aria-label="Main navigation">{links}</nav><a class="github" href="{GH}/MotionChallenge-Core">GitHub ↗</a></header><main id="main">{body}</main><footer><div><a class="brand" href="/">MotionChallenge</a><p>Open evaluation. Reproducible evidence.</p></div><div><a href="{GH}/MotionChallenge-Core">Core repository ↗</a><a href="/submit/">Contribute a controller</a><a href="/about/">About &amp; acknowledgments</a><a href="/#citation">Cite MotionChallenge</a><a href="{WEBSITE_SOURCE}">Website source ↗</a></div><small>Open protocols · Public evidence<br>Last updated · {UPDATE_TIME}</small></footer></body></html>''')
def intro(kicker,title,text,decoration=''):
 heading=f'<h1>{title}</h1>'
 if decoration:heading=f'<div class="heading-with-logo">{heading}{decoration}</div>'
 lede=f'<p class="lede">{text}</p>' if text else ''
 return f'<section class="pagehead"><p class="eyebrow">{kicker}</p>{heading}{lede}</section>'
def news():
 items=json.loads((CONTENT/'news.json').read_text())
 entries=[]
 for item in sorted(items,key=lambda x:x['date'],reverse=True):
  date=datetime.strptime(item['date'],'%Y-%m-%d')
  entries.append(f'<li><time datetime="{item["date"]}">{date.strftime("%Y/%m/%d")}</time><span>{html.escape(item["text"])} <a href="{html.escape(item["href"],quote=True)}">Explore →</a></span></li>')
 return '<section class="leaderboard-news" aria-labelledby="news-heading"><div class="news-panel"><h2 id="news-heading">News</h2><ul>'+''.join(entries)+'</ul></div></section>'
leaderboard_body=intro('BENCHMARK RESULTS','MotionChallenge Leaderboard','')+news()+'''<section class="board-section"><div class="track-selectors"><label>Benchmark<select id="benchmark-select" aria-label="Benchmark"></select></label><label>Robot<select id="robot-select" aria-label="Robot"></select></label><a id="track-details" href="/benchmarks/">Dataset &amp; failure conditions ↗</a><a href="/protocol/#observations">Observation rules ↗</a></div><div class="toolbar"><div><p id="sort-caption" class="sort-caption" aria-live="polite"></p></div><label class="search">Find a model <input id="model-search" type="search" placeholder="Model, type or organization…"></label></div>
<div class="table-scroll"><table id="leaderboard"><colgroup><col class="col-rank"><col class="col-model"><col class="col-type"><col class="col-org"><col span="6" class="col-metric"><col class="col-failed"><col class="col-success"></colgroup><thead><tr><th rowspan="3" scope="col">Rank</th><th rowspan="3" scope="col">Model</th><th rowspan="3" scope="col"><abbr title="Control policy family used by the evaluated checkpoint">Type</abbr></th><th rowspan="3" scope="col">Organization</th><th colspan="6" scope="colgroup" class="metric-title">Mean Per-Keypoint Position Error · MPKPE <span>mm</span><small>Lower is better</small></th><th rowspan="3" scope="col"><button data-sort="failed">Failed ↑</button></th><th rowspan="3" scope="col"><button data-sort="passed">Success ↓</button></th></tr><tr><th colspan="3" scope="colgroup" class="metric-group full-motion">No termination<small>Entire motion, including post-failure states</small></th><th colspan="3" scope="colgroup" class="metric-group">Early termination<small>Until first failure, including the failure frame</small></th></tr><tr><th scope="col"><button data-sort="full_mpkpe_xy_aligned_m">XY only ↑</button></th><th scope="col"><button data-sort="full_mpkpe_xy_yaw_aligned_m">XY + yaw ↑</button></th><th scope="col"><button data-sort="full_mpkpe_world_m">No alignment ↑</button></th><th scope="col"><button data-sort="mpkpe_xy_aligned_m">XY only ↑</button></th><th scope="col"><button data-sort="mpkpe_xy_yaw_aligned_m">XY + yaw ↑</button></th><th scope="col"><button data-sort="mpkpe_world_m">No alignment ↑</button></th></tr></thead>
<tbody></tbody></table><p id="empty" hidden>No models match your search.</p></div><div class="leaderboard-limit"><select id="page-size" aria-label="Models shown"><option value="5">Top 5</option><option value="10" selected>Top 10</option><option value="15">Top 15</option><option value="25">Top 25</option><option value="all">Top All</option></select><button data-page="previous" aria-label="Previous page">← Previous</button><button data-page="next" aria-label="Next page">Next →</button></div>
<p class="table-note"><strong>Type:</strong> Dense = continuous dense policies (MLP, convolutional, graph or Transformer); FSQ = finite scalar quantization; MoE = mixture of experts; FB = forward-backward latent policy; Flow = flow matching. Sources are linked from each model card.</p>
<p class="table-note">Each MJWarp evaluation reports success, completion and six tracking-error views. Results cover the complete selected dataset and pass independent CPU trace verification. <a href="https://github.com/MotionChallenge-Project/MotionChallenge-Core">Evaluator repository ↗</a></p>
<p class="table-note"><strong>Shared rules. Public code. Reproducible runs.</strong> Within each benchmark, robot and protocol, the core fixes data, physics, failures and scoring. Each entry identifies its checkpoint and inference implementation.</p>
<p class="table-note">Rank follows the selected metric, always best first: higher success, lower tracking error. The leaderboard opens with No termination · XY only sorted from low to high. Medals mark the top three. MPKPE uses the benchmark’s declared body origins as keypoints (14 for G1). It averages 3D Euclidean distances over keypoints and scoring samples within each motion, then weights motions equally. Early-termination errors cover the observed prefix. No-termination errors cover the entire motion. </p><a class="text-link" href="/data/results.json" download>Download results (JSON) ↓</a></section>
<section class="section three"><article><h3>Success</h3><p>A motion passes only if it reaches the final reference frame without any declared failure. All motions in an evaluation use the same policy and checkpoint.</p></article><article><h3>Completion</h3><p>Mean fraction of motion completed before failure. Reported alongside tracking error to describe how much of each motion was completed.</p></article><article><h3>Six tracking-error views</h3><p>Each time range reports XY only, XY + yaw and no alignment. These remove horizontal translation, translation and heading, or neither. Height is retained in all six views.</p><a href="/protocol/#alignment">Metric definitions →</a></article></section>'''
leaderboard_body=leaderboard_body.replace('class="pagehead"','class="pagehead leaderboard-head"',1)
leaderboard_body=leaderboard_body.replace('</section>',f'<p class="site-updated">Last updated · {UPDATE_TIME}</p></section>',1)
leaderboard_body+=f'''<section class="section citation" id="citation" aria-labelledby="citation-heading"><div class="citation-heading"><div><h2 id="citation-heading">Citation</h2><p>If you use MotionChallenge in your research, please cite:</p></div><div class="citation-actions"><button type="button" data-copy-citation aria-live="polite">Copy BibTeX</button></div></div><pre><code id="citation-code" class="language-bibtex">{html.escape(CITATION)}</code></pre></section>'''
page('/','Leaderboard',leaderboard_body,'Leaderboard')
page('/leaderboard/','Leaderboard',leaderboard_body,'Leaderboard',canonical_path='/')
current_pages.render(CONTENT,MODELS,TRACKS,rows,page,intro,GH)
(D/'data/evidence').mkdir(exist_ok=True)
for row in rows:
 shutil.copy2(CONTENT/'evidence'/row['evidence_file'],D/'data/evidence'/row['evidence_file'])
shutil.copytree(CONTENT/'protocols',D/'data/protocols',dirs_exist_ok=True)
shutil.copy2(CONTENT/'evaluation-source.json',D/'data/evaluation-source.json')
shutil.copytree(ROOT/'assets/dataset-logos',D/'assets/dataset-logos',dirs_exist_ok=True,ignore=shutil.ignore_patterns('README.md','._*'))
shutil.copytree(ROOT/'assets/model-icons',D/'assets/model-icons',dirs_exist_ok=True,ignore=shutil.ignore_patterns('README.md','._*'))
for name in ('app.js','style.css'):
 shutil.copy2(ROOT/name,D/name)
shutil.copy2(ROOT/'assets/favicon.png',D/'assets/favicon.png')
(D/'.nojekyll').write_text('')
for document in D.rglob('*.html'):
 text=document.read_text()
 text=re.sub(r'(href|src)="/(?!/)',lambda m:m.group(1)+'="'+BASE+'/',text)
 document.write_text(text)
print('Built',len(list(D.rglob('index.html'))),'pages;',len(rows),'verified evaluations')
