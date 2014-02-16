.PHONY: test readme docs clean infup publish dist

test:
	tox

sphinxbox/expak.py:
	-mkdir sphinxbox
	cd sphinxbox; ln -s ../expak.py .

readme:
	python make_readme.py

docs: sphinxbox/expak.py readme
	sphinx-apidoc -o docs sphinxbox
	cd docs; make html

infup: readme
	python setup.py register

publish: infup
	python setup.py sdist --formats=gztar,zip upload
	python2.6 setup.py bdist_egg upload
	python2.7 setup.py bdist_egg upload
	python3.2 setup.py bdist_egg upload
	python3.3 setup.py bdist_egg upload
	python setup.py bdist_wininst -p win32 upload
	python setup.py bdist_wininst -p win-amd64 upload

dist: readme
	python setup.py sdist --formats=gztar,zip
	python2.6 setup.py bdist_egg
	python2.7 setup.py bdist_egg
	python3.2 setup.py bdist_egg
	python3.3 setup.py bdist_egg
	python setup.py bdist_wininst -p win32
	python setup.py bdist_wininst -p win-amd64

clean:
	python setup.py clean
	-rm -rf build
	-rm -rf dist
	-rm -rf htmlcov
	-rm -rf expak.egg-info
	-rm *.pyc
	-rm test/*.pyc
	-rm -rf test/__pycache__
	-rm -rf __pycache__
	cd docs; make clean

superclean: clean
	-rm -rf *.egg
	-rm -rf sphinxbox
	-rm -rf .tox
