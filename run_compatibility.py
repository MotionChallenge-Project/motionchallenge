"""Bind published runs to the evaluator and model code used for rollout."""
import ast
import hashlib
from pathlib import Path

# These files launch jobs or independently verify a completed rollout. Their
# original hashes remain in each receipt, but they do not define rollout scores.
CORE_NON_ROLLOUT = {'__main__.py', 'runtime/mjwarp_entrypoint.py',
                    'evaluation/tensor_verify.py'}
RUNTIME_METADATA = {'weights_url', 'prepare_checkpoint', 'checkpoint_source',
                    'source_repository', 'source_commit', 'migration_status',
                    'official', 'observation_contract', 'provenance_status'}


def sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def core_sources(core):
    root = Path(core) / 'src/motion_challenge'
    return {p.relative_to(root).as_posix(): sha(p)
            for p in sorted(root.rglob('*.py'))
            if p.relative_to(root).as_posix() not in CORE_NON_ROLLOUT}


def model_sources(root, entrypoint):
    """Follow local imports, including helper modules and package initializers."""
    root = Path(root)
    pending = [entrypoint.split(':')[0]]
    found = {}
    while pending:
        module = pending.pop()
        path = root.joinpath(*module.split('.')).with_suffix('.py')
        if not path.is_file():
            path = root.joinpath(*module.split('.'), '__init__.py')
        if not path.is_file():
            continue  # Installed dependencies are pinned by the model lockfile.
        relative = path.relative_to(root).as_posix()
        if relative in found:
            continue
        found[relative] = sha(path)
        parts = module.split('.')
        for n in range(1, len(parts)):
            pending.append('.'.join(parts[:n]))
        package = parts if path.name == '__init__.py' else parts[:-1]
        for node in ast.walk(ast.parse(path.read_text(), filename=str(path))):
            if isinstance(node, ast.Import):
                pending.extend(alias.name for alias in node.names)
            elif isinstance(node, ast.ImportFrom):
                base = package[:len(package) - node.level + 1] if node.level else []
                if node.module:
                    base += node.module.split('.')
                if base:
                    pending.append('.'.join(base))
                pending.extend('.'.join([*base, alias.name])
                               for alias in node.names if alias.name != '*')
    if not found:
        raise ValueError('Missing tensor entrypoint source')
    return dict(sorted(found.items()))


def execution_fields(runtime):
    return {k: v for k, v in runtime.items() if k not in RUNTIME_METADATA}


def validate_run(result, runtime, model, core_manifest):
    if execution_fields(runtime) != execution_fields(model['runtime']):
        raise ValueError('Runtime execution fields mismatch')
    expected = core_manifest['source_sha256']
    if not expected:
        raise ValueError('Missing evaluator source manifest')
    recorded = {k: v for k, v in result['source_sha256'].items()
                if k not in CORE_NON_ROLLOUT}
    if recorded != expected:
        changed = sorted(k for k in recorded.keys() | expected.keys()
                         if recorded.get(k) != expected.get(k))
        raise ValueError('Evaluator source mismatch: ' + ', '.join(changed))
    expected = model['evaluation_source_sha256']
    if not expected:
        raise ValueError('Missing model source manifest')
    changed = sorted(k for k, v in expected.items()
                     if result['adapter_sha256'].get(k) != v)
    if changed:
        raise ValueError('Model inference source mismatch: ' + ', '.join(changed))
