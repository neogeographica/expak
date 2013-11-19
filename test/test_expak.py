# -* -coding: utf-8 -*-
#
# Copyright 2013 Joel Baxter
#
# This file is part of expak.
#
# expak is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# expak is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with expak.  If not, see <http://www.gnu.org/licenses/>.

"""Test functions for expak"""


import os
import contextlib
import filecmp
import shutil
import expak
import pytest

TEST_HOME = os.path.abspath(os.path.dirname(__file__))

TEST_INPUT_PATH = os.path.join(TEST_HOME, "input")

FILES_PATH = os.path.join(TEST_INPUT_PATH, "files")
MANGLED_FILES_PATH = os.path.join(TEST_INPUT_PATH, "mangled_files")

PAK_A = os.path.join(TEST_INPUT_PATH, "pak_a.pak")
SOME_A_RES = set(["doc_a.txt", "subdir_1/subdir_2/data_a"])
ALL_A_RES = SOME_A_RES.union(set(["data_a", "subdir_1/subdir_2/doc_a.txt"]))

PAK_B = os.path.join(TEST_INPUT_PATH, "pak_b.pak")
SOME_B_RES = set(["data_b", "subdir_1/subdir_2/doc_b.txt"])
ALL_B_RES = SOME_B_RES.union(set(["doc_b.txt", "subdir_1/subdir_2/data_b"]))

NO_RES = set()
SOME_RES = SOME_A_RES.union(SOME_B_RES)
ALL_RES = ALL_A_RES.union(ALL_B_RES)
BAD_RES = set(["undefined/resource/path", "another_bogus_resource"])
BAD_AND_SOME_A_RES = BAD_RES.union(SOME_A_RES)
BAD_AND_SOME_B_RES = BAD_RES.union(SOME_B_RES)
BAD_AND_SOME_RES = BAD_RES.union(SOME_RES)

NO_PAK = os.path.join(TEST_INPUT_PATH, "pak_not_here.pak")
BAD_PAK = os.path.join(TEST_INPUT_PATH, "this_is_not_a.pak")
TINY_BAD_PAK = os.path.join(TEST_INPUT_PATH, "tiny_bad.pak")
TRUNCATED_PAK = os.path.join(TEST_INPUT_PATH, "truncated.pak")
ALL_BAD_PAKS = set([NO_PAK, BAD_PAK, TINY_BAD_PAK, TRUNCATED_PAK])


# utility functions

@contextlib.contextmanager
def temp_workdir(dir):
    cwd = os.getcwd()
    if not os.path.exists(dir):
        os.makedirs(dir)
    os.chdir(dir)
    try:
        yield
    finally:
        os.chdir(cwd)
# Leave the output files in place in case they are needed for test debug.
# pytest should reap temp directories older than 4 test runs.
        shutil.rmtree(dir)

@pytest.fixture
def outdir_gen(tmpdir):
    class OutdirGen:
        part = 0
        def next(self):
            outdir_name = "part" + str(self.part)
            self.part = self.part + 1
            return str(tmpdir.mkdir(outdir_name))
    return OutdirGen()

def expected_error_free(sources):
    if isinstance(sources, basestring):
        return sources not in ALL_BAD_PAKS
    for path in sources:
        if path in ALL_BAD_PAKS:
            return False
    return True

def path_from_resname(name):
    return os.path.join(*name.split("/"))

def targets_from_resnames(names, rename_func):
    return dict((n, path_from_resname(rename_func(n))) for n in names)

def normal_targets(resnames):
    return targets_from_resnames(resnames, lambda n: n)

def renamed_targets(resnames):
    return targets_from_resnames(resnames, lambda n: n.replace("d", "f"))

def flat_targets(resnames):
    return targets_from_resnames(resnames, lambda n: n.replace("/", "_"))

def validate_resource(base_dir, res_file, check_dir, valid_files):
    rel_path = os.path.relpath(res_file, base_dir)
    assert rel_path in valid_files
    check_file = os.path.join(check_dir, valid_files[rel_path])
    assert filecmp.cmp(res_file, check_file, shallow=False)
    del valid_files[rel_path]

def validate(out_dir, check_dir, targets):
    unvalidated = dict((targets[k], path_from_resname(k)) for k in targets)
    for (dirpath, dirnames, filenames) in os.walk(out_dir):
        for f in filenames:
            res_file = os.path.join(dirpath, f)
            validate_resource(out_dir, res_file, check_dir, unvalidated)
    assert not unvalidated

def mangler(orig_data, name):
    real_path = path_from_resname(name)
    out_dir = os.path.dirname(real_path)
    if out_dir and not os.path.exists(out_dir):
        os.makedirs(out_dir)
    with open(real_path, 'wb') as outstream:
        outstream.write(orig_data[::-1])
    return True

def bad_converter(orig_data, name):
    raise IOError


# tests

@pytest.mark.parametrize(
    "sources,                 resource_names",
   [(PAK_A,                   ALL_A_RES),
    (NO_PAK,                  None),
    (BAD_PAK,                 None),
    ([PAK_B, PAK_A],          ALL_RES),
    ([NO_PAK, PAK_B, PAK_A],  None),
    ([BAD_PAK, PAK_A, PAK_B], None)])
def test_resource_names(sources, resource_names):
    assert expak.resource_names(sources) == resource_names

@pytest.mark.parametrize(
    "sources,                 resources_out",
   [(PAK_A,                   ALL_A_RES),
    (NO_PAK,                  NO_RES),
    (BAD_PAK,                 NO_RES),
    ([PAK_A, PAK_B],          ALL_RES),
    ([NO_PAK, PAK_A, PAK_B],  ALL_RES),
    ([BAD_PAK, PAK_B, PAK_A], ALL_RES)])
def test_process_all(outdir_gen, sources, resources_out):
    expected = expected_error_free(sources)
    outdir = outdir_gen.next()
    with temp_workdir(outdir):
        error_free = expak.extract_resources(sources)
        assert error_free == expected
        validate(outdir, FILES_PATH, normal_targets(resources_out))
    outdir = outdir_gen.next()
    with temp_workdir(outdir):
        error_free = expak.process_resources(sources, mangler)
        assert error_free == expected
        validate(outdir, MANGLED_FILES_PATH, normal_targets(resources_out))

@pytest.mark.parametrize(
    "sources",
   [PAK_A,
    [PAK_A, PAK_B]])
def test_bad_process_all(tmpdir, sources):
    outdir = str(tmpdir)
    with temp_workdir(outdir):
        assert not expak.process_resources(sources, bad_converter)
        validate(outdir, FILES_PATH, {})

@pytest.mark.parametrize(
    "sources,                 resources_in,       resources_out, target_fun",
   [(PAK_A,                   ALL_B_RES,          NO_RES,        None),
    (PAK_A,                   ALL_B_RES,          NO_RES,        renamed_targets),
    (NO_PAK,                  ALL_RES,            NO_RES,        None),
    (NO_PAK,                  ALL_RES,            NO_RES,        renamed_targets),
    (BAD_PAK,                 ALL_RES,            NO_RES,        None),
    (BAD_PAK,                 ALL_RES,            NO_RES,        renamed_targets),
    (PAK_B,                   SOME_RES,           SOME_B_RES,    None),
    (PAK_B,                   SOME_RES,           SOME_B_RES,    renamed_targets),
    (PAK_B,                   SOME_RES,           SOME_B_RES,    flat_targets),
    ([PAK_A, PAK_B],          BAD_RES,            NO_RES,        None),
    ([PAK_A, PAK_B],          BAD_RES,            NO_RES,        renamed_targets),
    ([NO_PAK, PAK_B, PAK_A],  BAD_RES,            NO_RES,        None),
    ([NO_PAK, PAK_B, PAK_A],  BAD_RES,            NO_RES,        renamed_targets),
    ([BAD_PAK, PAK_A, PAK_B], BAD_RES,            NO_RES,        None),
    ([BAD_PAK, PAK_A, PAK_B], BAD_RES,            NO_RES,        renamed_targets),
    ([PAK_A, PAK_B],          BAD_AND_SOME_B_RES, SOME_B_RES,    None),
    ([PAK_A, PAK_B],          BAD_AND_SOME_B_RES, SOME_B_RES,    renamed_targets),
    ([PAK_A, PAK_B],          BAD_AND_SOME_B_RES, SOME_B_RES,    flat_targets),
    ([NO_PAK, PAK_A, PAK_B],  BAD_AND_SOME_B_RES, SOME_B_RES,    None),
    ([NO_PAK, PAK_A, PAK_B],  BAD_AND_SOME_B_RES, SOME_B_RES,    renamed_targets),
    ([NO_PAK, PAK_A, PAK_B],  BAD_AND_SOME_B_RES, SOME_B_RES,    flat_targets),
    ([BAD_PAK, PAK_A, PAK_B], BAD_AND_SOME_B_RES, SOME_B_RES,    None),
    ([BAD_PAK, PAK_A, PAK_B], BAD_AND_SOME_B_RES, SOME_B_RES,    renamed_targets),
    ([BAD_PAK, PAK_A, PAK_B], BAD_AND_SOME_B_RES, SOME_B_RES,    flat_targets),
    ([PAK_A, PAK_B],          BAD_AND_SOME_A_RES, SOME_A_RES,    None),
    ([PAK_A, PAK_B],          BAD_AND_SOME_A_RES, SOME_A_RES,    renamed_targets),
    ([PAK_A, PAK_B],          BAD_AND_SOME_A_RES, SOME_A_RES,    flat_targets),
    ([NO_PAK, PAK_A, PAK_B],  BAD_AND_SOME_A_RES, SOME_A_RES,    None),
    ([NO_PAK, PAK_A, PAK_B],  BAD_AND_SOME_A_RES, SOME_A_RES,    renamed_targets),
    ([NO_PAK, PAK_A, PAK_B],  BAD_AND_SOME_A_RES, SOME_A_RES,    flat_targets),
    ([BAD_PAK, PAK_A, PAK_B], BAD_AND_SOME_A_RES, SOME_A_RES,    None),
    ([BAD_PAK, PAK_A, PAK_B], BAD_AND_SOME_A_RES, SOME_A_RES,    renamed_targets),
    ([BAD_PAK, PAK_A, PAK_B], BAD_AND_SOME_A_RES, SOME_A_RES,    flat_targets),
    ([PAK_A, PAK_B],          BAD_AND_SOME_RES,   SOME_RES,      None),
    ([PAK_A, PAK_B],          BAD_AND_SOME_RES,   SOME_RES,      renamed_targets),
    ([PAK_A, PAK_B],          BAD_AND_SOME_RES,   SOME_RES,      flat_targets),
    ([NO_PAK, PAK_A, PAK_B],  BAD_AND_SOME_RES,   SOME_RES,      None),
    ([NO_PAK, PAK_A, PAK_B],  BAD_AND_SOME_RES,   SOME_RES,      renamed_targets),
    ([NO_PAK, PAK_A, PAK_B],  BAD_AND_SOME_RES,   SOME_RES,      flat_targets),
    ([BAD_PAK, PAK_A, PAK_B], BAD_AND_SOME_RES,   SOME_RES,      None),
    ([BAD_PAK, PAK_A, PAK_B], BAD_AND_SOME_RES,   SOME_RES,      renamed_targets),
    ([BAD_PAK, PAK_A, PAK_B], BAD_AND_SOME_RES,   SOME_RES,      flat_targets)])
def test_process_selected(outdir_gen, sources,
                          resources_in, resources_out, target_fun):
    if target_fun:
       targets_in = target_fun(resources_in)
       targets_out = target_fun(resources_out)
    else:
       targets_in = resources_in.copy()
       targets_out = normal_targets(resources_out)
    expected = expected_error_free(sources)
    outdir = outdir_gen.next()
    with temp_workdir(outdir):
        error_free = expak.extract_resources(sources, targets_in)
        assert error_free == expected
        validate(outdir, FILES_PATH, targets_out)
        remaining_resources = resources_in.difference(resources_out)
        if isinstance(targets_in, dict):
            assert remaining_resources == set(targets_in.keys())
        else:
            assert remaining_resources == targets_in
    if target_fun:
       targets_in = target_fun(resources_in)
    else:
       targets_in = resources_in.copy()
    outdir = outdir_gen.next()
    with temp_workdir(outdir):
        error_free = expak.process_resources(sources, mangler, targets_in)
        assert error_free == expected
        validate(outdir, MANGLED_FILES_PATH, targets_out)
        remaining_resources = resources_in.difference(resources_out)
        if isinstance(targets_in, dict):
            assert remaining_resources == set(targets_in.keys())
        else:
            assert remaining_resources == targets_in

@pytest.mark.parametrize(
    "sources,                 resources_in,     target_fun",
   [(PAK_A,                   SOME_RES,         None),
    (PAK_A,                   SOME_RES,         renamed_targets),
    ([PAK_A, PAK_B],          BAD_AND_SOME_RES, None),
    ([PAK_A, PAK_B],          BAD_AND_SOME_RES, renamed_targets)])
def test_bad_process_selected(tmpdir, sources, resources_in, target_fun):
    if target_fun:
       targets_in = target_fun(resources_in)
    else:
       targets_in = resources_in.copy()
    outdir = str(tmpdir)
    with temp_workdir(outdir):
        assert not expak.process_resources(sources, bad_converter, targets_in)
        validate(outdir, FILES_PATH, {})
        if isinstance(targets_in, dict):
            assert resources_in == set(targets_in.keys())
        else:
            assert resources_in == targets_in

@pytest.mark.parametrize(
    "sources",
   [TINY_BAD_PAK,
    TRUNCATED_PAK])
def test_misc_bad_paks(outdir_gen, sources):
    assert expak.resource_names(sources) == None
    outdir = outdir_gen.next()
    with temp_workdir(outdir):
        assert not expak.extract_resources(sources)
        validate(outdir, FILES_PATH, {})
    outdir = outdir_gen.next()
    with temp_workdir(outdir):
        assert not expak.extract_resources(sources, ALL_RES.copy())
        validate(outdir, FILES_PATH, {})
    outdir = outdir_gen.next()
    with temp_workdir(outdir):
        assert not expak.extract_resources(sources, renamed_targets(ALL_RES))
        validate(outdir, FILES_PATH, {})

def test_main_usage(capsys):
    assert expak.simple_expak([]) == 0
    (out, err) = capsys.readouterr()
    assert str(out).lstrip().startswith("To extract all resources from pak files:")

def test_main_cmdline_args(capsys):
    assert expak.simple_expak() == 0
    (out, err) = capsys.readouterr()
    assert str(out).strip() == "not found (or not successfully extracted):\n    test"

@pytest.mark.parametrize(
    "sources",
    [[PAK_A],
     [NO_PAK],
     [BAD_PAK],
     [PAK_A, PAK_B],
     [NO_PAK, PAK_A, PAK_B],
     [BAD_PAK, PAK_B, PAK_A]])
def test_main_extract_all(tmpdir, capsys, sources):
    expected = 0 if expected_error_free(sources) else 1
    outdir = str(tmpdir)
    with temp_workdir(outdir):
        assert expak.simple_expak(sources) == expected
    (out, err) = capsys.readouterr()
    assert not str(out).strip()

@pytest.mark.parametrize(
    "sources,                 resources_in,     all_found",
   [([PAK_A],                 ALL_A_RES,        True),
    ([PAK_A],                 SOME_RES,         False),
    ([NO_PAK],                SOME_RES,         False),
    ([BAD_PAK],               ALL_B_RES,        False),
    ([PAK_A, PAK_B],          ALL_RES,          True),
    ([PAK_A, PAK_B],          BAD_AND_SOME_RES, False),
    ([NO_PAK, PAK_A, PAK_B],  ALL_RES,          True),
    ([NO_PAK, PAK_A, PAK_B],  BAD_AND_SOME_RES, False),
    ([BAD_PAK, PAK_B, PAK_A], ALL_RES,          True),
    ([BAD_PAK, PAK_B, PAK_A], BAD_AND_SOME_RES, False)])
def test_main_extract_selected(tmpdir, capsys, sources, resources_in, all_found):
    expected = 0 if expected_error_free(sources) else 1
    argv = sources + list(resources_in)
    outdir = str(tmpdir)
    with temp_workdir(outdir):
        assert expak.simple_expak(argv) == expected
    (out, err) = capsys.readouterr()
    if all_found:
        assert not str(out).strip()
    else:
        assert str(out).strip().startswith("not found (or not successfully extracted):")
