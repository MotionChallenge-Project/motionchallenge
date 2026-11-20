# MotionChallenge website

The site displays LAFAN1 and BONES-SEED evaluations under the shared MJWarp protocol. Every checkpoint has its own model repository and a separate page for each verified dataset result.

## Build

~~~sh
python sync_results.py --workspace /path/to/evaluation-workspace
python -m unittest discover -s tests -v
SITE_BASE_PATH='' python build.py
python -m http.server 8768 --bind 127.0.0.1 --directory docs
~~~

The workspace contains Core, independent model repositories and evaluation outputs under runs/. The importer checks complete cohorts, author-release provenance, original checkpoint hashes, all runtime execution fields, evaluator sources, model inference imports, simulator configuration and independent trace-verification receipts. Duplicate shared exports are excluded from official model entries. Publication checks bind every leaderboard value to its evidence digest and the current evaluation-source manifest.

BONES-SEED uses a feasibility-filtered subset of the original G1 motion data. Users download the original archive and apply the same public inclusion list of 129,561 motions for every model.

content/ holds model metadata, frozen protocols and compact receipts. The builder exports only evidence referenced by current result rows. Full traces, motions and checkpoints stay outside Git. Numerical reproduction differences are recorded separately.

GitHub Pages serves docs/ from the website branch. Building does not publish the site.

The leaderboard opens BONES-SEED and sorts No termination · XY only from low to high. Failed and Success occupy separate columns. No termination precedes Early termination; one vertical rule separates the two metric windows. Failed and Success share a sorting control and highlight together. Completion remains in evidence and detail pages. Dated news links directly to the selected benchmark leaderboard.

Protocol pages describe common evaluation standards; benchmark pages specify the robot and physical configuration. Organization marks and their sources are recorded under assets/model-icons/ and assets/dataset-logos/.

## Metric

MPJPE (Mean Per-Joint Position Error) measures the 3D Euclidean distance between actual and reference keypoint positions. The protocol defines these keypoints at robot body-frame origins: 14 points for G1. Errors are averaged over keypoints and scoring samples within each motion, then motions are weighted equally. Results report full-motion and first-failure-prefix scores with no alignment, XY alignment, and XY + yaw alignment. XY alignment removes pelvis horizontal translation while retaining height error. Leaderboard values are reported in millimetres (mm).
