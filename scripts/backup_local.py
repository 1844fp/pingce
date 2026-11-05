"""Bundle local database and artifact key/data; restore only into a new directory."""
import argparse
import hashlib
import json
from pathlib import Path
import shutil
import sys
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from scripts.backup_database import snapshot

ROOT=Path(__file__).resolve().parents[1]


def copy_artifacts(source,destination):
    if not source.exists():return
    for path in [source,*source.rglob('*')]:
        if path.is_symlink() or getattr(path,'is_junction',lambda:False)():raise ValueError('linked artifact paths forbidden')
    shutil.copytree(source,destination)


def create(root,destination):
    root=Path(root).resolve();destination=Path(destination).resolve()
    if destination==root or destination.is_relative_to(root/'data'):raise ValueError('invalid backup destination')
    destination.mkdir(parents=True,exist_ok=False)
    snapshot(root/'evaluation.db',destination/'evaluation.db')
    copy_artifacts(root/'data/artifacts',destination/'data/artifacts')
    files={str(p.relative_to(destination)).replace('\\','/'):hashlib.sha256(p.read_bytes()).hexdigest() for p in destination.rglob('*') if p.is_file()}
    manifest={'schema':'local-backup-v1','files':files,'limits':'本机副本；包含产物完整性密钥，需保护目录权限；不是异地容灾'}
    (destination/'manifest.json').write_text(json.dumps(manifest,ensure_ascii=False,indent=2),encoding='utf-8')
    return {'destination':str(destination),'files':len(files)}


def restore(bundle,destination):
    bundle=Path(bundle).resolve();destination=Path(destination).resolve()
    manifest=json.loads((bundle/'manifest.json').read_text(encoding='utf-8'))
    if manifest.get('schema')!='local-backup-v1' or 'evaluation.db' not in manifest.get('files',{}):raise ValueError('invalid backup manifest')
    for relative,digest in manifest['files'].items():
        path=(bundle/relative).resolve()
        if not path.is_relative_to(bundle) or not path.is_file() or hashlib.sha256(path.read_bytes()).hexdigest()!=digest:raise ValueError('backup integrity mismatch')
    actual={str(p.relative_to(bundle)).replace('\\','/') for p in bundle.rglob('*') if p.is_file() and p.name!='manifest.json'}
    if actual!=set(manifest['files']):raise ValueError('backup contains unlisted files')
    destination.mkdir(parents=True,exist_ok=False)
    result=snapshot(bundle/'evaluation.db',destination/'evaluation.db',restore=True)
    copy_artifacts(bundle/'data/artifacts',destination/'data/artifacts')
    return {'destination':str(destination),'interrupted_tasks':result['interrupted_tasks']}


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('operation',choices=['backup','restore']);parser.add_argument('--source',type=Path);parser.add_argument('--destination',type=Path,required=True)
    args=parser.parse_args()
    if not args.destination.resolve().is_relative_to(ROOT):parser.error('目标必须位于项目根目录内')
    if args.operation=='backup':result=create(ROOT,args.destination)
    else:
        if not args.source:parser.error('恢复需要--source')
        result=restore(args.source,args.destination)
    print(json.dumps(result,ensure_ascii=False))


if __name__=='__main__':main()
