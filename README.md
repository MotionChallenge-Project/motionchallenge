# MotionChallenge website

The site displays LAFAN1 and BONES-SEED evaluations under the shared MJWarp protocol. Every checkpoint has its own model repository and a separate page for each verified dataset result.

## Build

~~~sh
python sync_results.py --workspace /path/to/evaluation-workspace
python -m unittest discover -s tests -v
SITE_BASE_PATH='' python build.py
python -m http.server 8768 --bind 127.0.0.1 --directory docs
~~~

The workspace contains Core, independent model repositories and evaluation outputs under runs/. The importer checks complete cohorts, author-release provenance, original checkpoint hashes, execution fields, simulator configuration and independent trace-verification receipts. Duplicate shared exports are excluded from official model entries. Publication checks bind every leaderboard value to its evidence digest.

content/ holds model metadata, frozen protocols and compact receipts. The builder exports only evidence referenced by current result rows. Full traces, motions and checkpoints stay outside Git. Numerical reproduction differences are recorded separately.

GitHub Pages serves docs/ from the website branch. Building does not publish the site.

The leaderboard opens BONES-SEED and sorts Success from high to low. Failed and Success occupy separate columns. Early termination precedes No termination; fine vertical rules separate major column groups. Dated news links directly to the selected benchmark leaderboard.

Protocol pages describe common evaluation standards; benchmark pages specify the robot and physical configuration. Organization marks and their sources are recorded under assets/model-icons/ and assets/dataset-logos/.
