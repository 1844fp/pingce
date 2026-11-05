from pathlib import Path
import yaml

ROOT=Path(__file__).resolve().parents[1]


def test_compose_static_topology():
    config=yaml.safe_load((ROOT/'infra/containers/compose.yaml').read_text(encoding='utf-8'))
    assert set(config['services'])=={'api','worker'}
    api=config['services']['api']; worker=config['services']['worker']
    assert api['ports']==['127.0.0.1:8765:8765']
    assert api['volumes']==worker['volumes']
    assert worker['deploy']['replicas']==1
    assert worker['depends_on']['api']['condition']=='service_healthy'
    assert api['environment']['EVAL_DB']==worker['environment']['EVAL_DB']
    assert api['environment']['EVAL_ARTIFACT_ROOT']==worker['environment']['EVAL_ARTIFACT_ROOT']=='/data/artifacts'


def test_image_has_migration_artifact():
    dockerfile=(ROOT/'infra/containers/Dockerfile').read_text()
    ignore=(ROOT/'infra/containers/Dockerfile.dockerignore').read_text()
    assert 'COPY infra/sqlite/ infra/sqlite/' in dockerfile
    assert '!infra/sqlite/**' in ignore
    assert (ROOT/'infra/sqlite/001_initial.sql').is_file()
