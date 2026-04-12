# APFA-013.5: Makes app/ a proper Python package so `from app.X import Y`
# resolves when the repo root is on sys.path (via WORKDIR=/opt/apfa in Docker
# or PYTHONPATH=. locally). Previously missing, causing ModuleNotFoundError
# inside the Docker container.
