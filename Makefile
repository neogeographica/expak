.PHONY: test readme docs clean sdist infup publish winpublish

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

sdist: readme
	python setup.py sdist

infup: readme
	python setup.py register

publish: readme
	python setup.py sdist upload
	python2.6 setup.py bdist_egg upload
	python2.7 setup.py bdist_egg upload

winpublish:
	C:\Python26\python.exe setup.py bdist_wininst --target-version=2.6 upload
	C:\Python27\python.exe setup.py bdist_wininst --target-version=2.7 upload

clean:
	python setup.py clean
	-rm -rf build
	-rm -rf dist
	-rm -rf htmlcov
	-rm -rf expak.egg-info
	-rm *.pyc
	-rm test/*.pyc
	-rm -rf test/__pycache__
	cd docs; make clean

superclean: clean
	-rm -rf *.egg
	-rm -rf sphinxbox
	-rm -rf .tox
