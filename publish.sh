# publish to PyPi

rm -rf dist build ads.egg-info
find ./ -name '*.pyc' -exec rm -f {} \;
find ./ -name 'Thumbs.db' -exec rm -f {} \;
find ./ -name '*~' -exec rm -f {} \;

python3 -m pip install --upgrade build twine
python3 setup.py sdist bdist_wheel
twine upload dist/*