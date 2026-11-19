"""MJWarp protocol and local dataset pages."""
import json
import html


def render(content, page, intro, github):
    rows=json.loads((content/"mjwarp-admissions.json").read_text())
    excluded=[r["model"] for r in rows if r["status"]=="excluded"]
    common="""<section class="section docs"><h2>Controller observations</h2>
<p>Actual global position and actual linear velocity are prohibited, including world/body-frame velocity, preprocessing, reset and explicit estimation. Joint position/velocity, root orientation/angular velocity, gravity and frozen reference poses/velocities remain available.</p>
<p>Policies requiring forbidden inputs cannot enter this track by replacing those inputs with zeros. Every checkpoint needs a new input audit, batch-inference parity and full evaluation.</p>
<h2>Evaluation</h2><p>Control and scoring run at 50 Hz. Each control interval contains four physics steps of 5 ms. PD torques update at every physics step. Sliding friction is 1.0; the Newton solver uses at most 50 iterations and 20 line-search iterations. Motions run through their exact source endpoint.</p>
<p>Core precomputes scoring reference body poses with MuJoCo/MJWarp before rollout. Actual body poses come from the simulator. Adapters receive root/joint reference information and maintain their own reference body features.</p>
<h2>Evaluation status</h2><p>Checkpoint validation is in progress. Scores are listed after full evaluation, independent trace verification and reproduction checks.</p>
<h2>Currently excluded checkpoints</h2><p>"""+html.escape(", ".join(excluded))+"""</p><p>These released adapter paths consume actual root linear velocity. Other checkpoints remain pending review.</p></section>"""
    page("/protocol/mjwarp/","MJWarp protocol",intro("NEW PROTOCOL · IN VALIDATION","MJWarp evaluation","Batched GPU physics with a strict observation contract.")+common,"Protocol")
    page("/benchmarks/seed/","BONES-SEED",intro("BENCHMARK · IN VALIDATION","BONES-SEED · G1","A fixed local-data cohort matching the existing LeRobot v3 motion selection.")+"""
<section class="section docs"><h2>Download original data</h2>
<p>Obtain <code>g1.tar.gz</code> from <a href="https://huggingface.co/datasets/bones-studio/seed">Bones Studio on Hugging Face</a> after accepting its terms. MotionChallenge does not mirror this dataset.</p>
<pre><code>datasets/seed/g1.tar.gz</code></pre>
<h2>One public motion list</h2><p>129,561 motions, 113,674,960 frames, 120 Hz. The versioned selection ledger defines membership; missing selected files fail validation. Additional source motions do not silently change the benchmark.</p>
<p>Root translations in the original CSV are in centimetres; root Euler rotations and joint angles are in degrees. Conversion to the internal representation must preserve timing and source motion identity.</p>
<p>Motion Data by <a href="https://bones.studio/">Bones Studio</a>. Use is subject to the <a href="https://bones.studio/info/seed-license">BONES-SEED license</a>.</p></section>"""+common,"Benchmarks")
