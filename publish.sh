# publish to PyPi
pip install -q twine

rm -rf dist build *.egg-info
find ./ -name '*.pyc' -exec rm -f {} \;
find ./ -name 'Thumbs.db' -exec rm -f {} \;
find ./ -name '*~' -exec rm -f {} \;

python3 -m pip install --upgrade build twine
python3 setup.py sdist bdist_wheel
twine upload dist/*
