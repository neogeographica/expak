.PHONY: test docs clean sdist

test:
	tox

sphinxbox/expak.py:
	-mkdir sphinxbox
	cd sphinxbox; ln -s ../expak.py .

docs: sphinxbox/expak.py
	sphinx-apidoc -o docs sphinxbox
	cd docs; make html
	python make_readme.py

sdist:
	python setup.py sdist

clean:
	python setup.py clean
	-rm -rf build
	-rm -rf dist
	-rm -rf htmlcov
	-rm -rf expak.egg-info
	-rm *.pyc
	cd docs; make clean

superclean: clean
	-rm -rf *.egg
	-rm -rf sphinxbox
