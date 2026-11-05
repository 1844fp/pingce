"""Build a source-only archive under the canonical project root."""
from pathlib import Path
from zipfile import ZipFile, ZIP_DEFLATED

root=Path(__file__).resolve().parents[1]
destination=root/'evaluation-platform-source.zip'
excluded={'.venv','node_modules','__pycache__','.pytest_cache','.git','work','.local','data','backups'}
with ZipFile(destination,'w',ZIP_DEFLATED) as archive:
    for path in root.rglob('*'):
        if not path.is_file() or excluded.intersection(path.relative_to(root).parts): continue
        if path.name=='.env' or path.name.startswith('.env.'): continue
        if path.suffix=='.zip' or '.db' in path.name or path.name.endswith('.lock') and path.name!='package-lock.json': continue
        archive.write(path,Path('evaluation-platform')/path.relative_to(root))
print(destination)
