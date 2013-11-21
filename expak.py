# -*- coding: utf-8 -*-
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

"""Extract and process resources from Quake-style pak files.

The :func:`extract_resources` and :func:`process_resources` functions of this
module enable programmatic extraction and (optional) processing of resources
from one or more pak files.

The :func:`resource_names` function retrieves a set of all the resource names
in one or more pak files.

All of these functions have a ``sources`` parameter which can accept either a
string specifying the filepath of a single pak file to process, or an iterable
container of strings specifying multiple pak files to process.

Resource selection (using a set of names or a name map) and processing (with a
user-provided function hook) is described in more detail in the documentation
for each function.

The return status of :func:`extract_resources`/:func:`process_resources` is an
indicator of whether exceptions were encountered while reading the pak file or
processing resources. For the simple "extract everything" uses, this return
status maps directly to whether all of the intended resources were extracted.
For usage patterns that explicitly supply an input set or dict of resources
however, you should check that container after the invocation to see which
resources were not handled (if any).

Example of retrieving resource names from a pak file:

.. code-block:: python

    pak0_resource_set = expak.resource_names("pak0.pak")

Example of extracting all resources from multiple pak files:

.. code-block:: python

    expak.extract_resources(["pak0.pak", "pak1.pak"])

Example of extracting specified resources from multiple pak files:

.. code-block:: python

    sources = ["pak0.pak", "pak1.pak"]
    targets = set(["sound/misc/basekey.wav", "sound/misc/medkey.wav"])
    expak.extract_resources(sources, targets)

More complex example:

.. code-block:: python

    # Extract sound/misc/basekey.wav, convert it to OGG format, and save the
    # result as base_key.ogg. Similarly process sound/misc/medkey.wav to
    # create medieval_key.ogg. Look for those resources in pak0.pak and in
    # pak1.pak.
    def ogg_converter(orig_data, name):
        new_data = my_ogg_conversion_func_not_shown_here(orig_data)
        with open(name, 'wb') as outstream:
            outstream.write(new_data)
        return True
    sources = ["pak0.pak", "pak1.pak"]
    targets = {"sound/misc/basekey.wav" : "base_key.ogg",
               "sound/misc/medkey.wav"  : "medieval_key.ogg"}
    expak.process_resources(sources, ogg_converter, targets)
    # Notify if some of the desired files were not created.
    if targets:
        print("not found (or not successfully processed):")
        for p in targets:
            print("    %s" % p)

"""

__all__ = ['process_resources',
           'extract_resources',
           'resource_names',
           'nop_converter',
           'print_err']

__version__ = "1.0"


import struct
import sys
import os
import errno

PAK_FILE_SIGNATURE = "PACK"
RESOURCE_NAME_LEN = 56
UNSIGNED_INT_LEN = 4
TABLE_ENTRY_LEN = RESOURCE_NAME_LEN + (2 * UNSIGNED_INT_LEN)

#: Boolean flag that may be changed to disable or enable stderr messages; True
#: by default. Such messages are printed when exceptions are encountered that
#: prevent reading a pak file or processing a resource.
print_err = True


def read_uint(instream):
    """Read an unsigned int from a binary file object.

    Read :const:`UNSIGNED_INT_LEN` bytes from the current position in the file,
    interpret those bytes as an unsigned integer, and return the result.

    :param instream: binary file object to read from
    :type instream:  file

    :returns: unsigned integer read from the file
    :rtype:   int

    """
    packed = instream.read(UNSIGNED_INT_LEN)
    if len(packed) != UNSIGNED_INT_LEN:
        raise IOError(2, "unexpected EOF reading integer")
    return struct.unpack('I', packed)[0]

def read_header(instream):
    """Read pak header info from a binary file object.

    Seek to the beginning of the file. If the first four bytes don't contain the
    :const:`PAK_FILE_SIGNATURE` string then return None. Otherwise continue to
    read the offset and size of the file table. Return the file table offset and
    number of table entries as a tuple.

    :param instream: binary file object to read from
    :type instream:  file

    :returns: tuple of file table offset and number of table entries if the
              given file is a pak file, None otherwise
    :rtype:   tuple(int,int) or None

    """
    instream.seek(0)
    file_id = instream.read(len(PAK_FILE_SIGNATURE))
    # We don't raise IOError on a short read here... IOError is for use after
    # we've determined it's actually a pak file.
    if file_id != PAK_FILE_SIGNATURE:
        return None
    ftable_off = read_uint(instream)
    ftable_len = read_uint(instream)
    num_files = ftable_len / TABLE_ENTRY_LEN
    return (ftable_off, num_files)

def read_filetable(instream, header, targets):
    """Given the header info, extract info on resources contained in a pak file.

    Seek to the pak file table position in the file. Iterate over the file table
    and generate a list of (name, offset, length) tuples for some number of the
    resources in the table. If the ``targets`` argument is None, all discovered
    resources will be included in the list; otherwise the list will be limited
    to resources whose names are in ``targets``.

    :param instream: binary file object to read from
    :type instream:  file
    :param header:   pak header info, containing the file table offset and
                     number of entries
    :type header:    tuple(int,int)
    :param targets:  resource names to limit resource selection, or None to
                     indicate that all resources should be selected
    :type targets:   container(str) or None

    :returns: list of (name, offset, length) tuples for selected resources
    :rtype:   list(tuple(str,int,int))

    """
    target_info = []
    if targets or targets is None:
        (ftable_off, num_files) = header
        instream.seek(ftable_off)
        for f in range(num_files):
            file_name = instream.read(RESOURCE_NAME_LEN)
            if len(file_name) != RESOURCE_NAME_LEN:
                raise IOError(2, "unexpected EOF reading resource name")
            # Terminate the name at the first encountered null character.
            file_name = file_name.partition("\0")[0]
            file_off = read_uint(instream)
            file_len = read_uint(instream)
            if targets and file_name not in targets:
                continue
            target = (file_name, file_off, file_len)
            target_info.append(target)
    return target_info

def get_target_info(instream, targets):
    """Extract info on resources contained in a pak file.

    Read the pak header information from the file. If that succeeds, return the
    result of :func:`read_filetable`; otherwise return None.

    :param instream: binary file object to read from
    :type instream:  file
    :param targets:  resource names to limit resource selection, or None to
                     indicate that all resources should be selected
    :type targets:   container(str) or None

    :returns: list of (name, offset, length) tuples for selected resources if
              the given file is a pak file, None otherwise
    :rtype:   list(tuple(str,int,int)) or None

    """
    header = read_header(instream)
    if header is None:
        return None
    return read_filetable(instream, header, targets)

def process_resources_int(pak_path, converter, targets):
    """Extract and process resources contained in a pak file.

    Implement :func:`process_resources` for a single pak file.

    See :func:`process_resources` for more discussion of the return value
    and the handling of the ``targets`` argument.

    :param pak_path:  file path of the pak file to process
    :type pak_path:   str
    :param converter: used to process each selected resource, as described for
                      :func:`process_resources`
    :type converter:  function(str,str)
    :param targets:   resources to select, as described for
                      :func:`process_resources`; contents may be modified
    :type targets:    dict(str,str) or set(str) or None

    :returns: True if no IOError exception reading the pak file and no
              exception processing any resource, False otherwise
    :rtype:   bool

    """
    try:
        with open(pak_path, 'rb') as instream:
            # Get resources to process and iterate over them.
            target_info = get_target_info(instream, targets)
            if target_info is None:
                if print_err:
                    sys.stderr.write("%s is not a pak file\n" % pak_path)
                return False
            processing_exception = False
            for target in target_info:
                # Get the individual resource info and read its content.
                (file_name, file_off, file_len) = target
                instream.seek(file_off)
                orig_data = instream.read(file_len)
                if len(orig_data) != file_len:
                    raise IOError(2, "unexpected EOF reading resource data")
                # Process the resource using the converter function, in the way
                # indicated by the type of the targets argument.
                try:
                    if targets is None:
                        converter(orig_data, file_name)
                    else:
                        if isinstance(targets, dict):
                            if converter(orig_data, targets[file_name]):
                                del targets[file_name]
                        else:
                            if converter(orig_data, file_name):
                                targets.remove(file_name)
                except:
                    processing_exception = True
                    if print_err:
                        sys.stderr.write("%s exception processing resource %s\n" %
                                         (repr(sys.exc_info()[1]), file_name))
        return True and not processing_exception
    except IOError:
        if print_err:
            sys.stderr.write("%s exception reading pak %s\n" %
                             (repr(sys.exc_info()[1]), pak_path))
        return False

def process_resources(sources, converter, targets=None):
    """Extract and process resources contained in one or more pak files.

    The ``converter`` parameter accepts a function that will be used to process
    each selected resource that is found in a pak file. This converter function
    accepts the resource binary content and a name string as arguments. It
    returns a boolean success status, which indicates whether the resource was
    processed but does not affect the overall return value of process_resources.
    The converter function may also raise any exception to stop processing a
    given resource; this does not immediately interrupt the overall
    process_resources loop, but will cause process_resources to return False
    when it finishes.

    The :func:`nop_converter` function in this module is an example of a simple
    converter function that just writes out the resource content in its original
    form.

    The selected resources, and the name passed to the converter function for
    each, depend on the type and content of the ``targets`` argument:

    * None: Every resource in the pak file is selected. The name passed to the
      converter function is the resource name.

    * set: Resources are selected only if their name is in the set. The name
      passed to the converter function is the resource name.

    * dict: Resources are selected only if their name is a key in the dict. The
      name passed to the converter function is the result of looking up the
      resource name in the dict.

    If the ``targets`` argument is a set or dict, the element corresponding to
    each found and successfully processed resource is removed from it.

    This function will return True if each specified source is a pak file, is
    read without I/O errors, and is processed without converter exceptions.
    False otherwise.

    .. note::

         In the case where ``targets`` is not None, a True result does not
         indicate that all of the resources in ``targets`` were found and
         processed. And if False is returned, some processing may have been
         done. Examining the contents of ``targets`` after the function returns
         is a good idea.

    :param sources:   file path of the pak file to process, or an iterable
                      specifying multiple such paths
    :type sources:    str or iterable(str)
    :param converter: used to process each selected resource, as described above
    :type converter:  function(str,str)
    :param targets:   resources to select, as described above; contents may be
                      modified
    :type targets:    dict(str,str) or set(str) or None

    :returns: True if no IOError exception reading the pak file and no
              exception processing any resource, False otherwise
    :rtype:   bool

    """
    # Handle single-string input for the sources argument.
    if isinstance(sources, basestring):
        return process_resources_int(sources, converter, targets)
    # Handle iterable input for the sources argument.
    all_success = True
    for pak_path in sources:
        success = process_resources_int(pak_path, converter, targets)
        all_success = success and all_success
    return all_success

def nop_converter(orig_data, name):
    """Example converter function that writes out the unmodified resource.

    Treat all but the final path segments of the resource as subdirectories, and
    create them as needed. Then write the extracted resource out into the
    bottom subdirectory, using the final path segment of the resource name as
    the output file name.

    In other words, if the ``name`` argument is "sound/hknight/grunt.wav", then:

    * Ensure that the directory "sound" exists as a subdirectory of the current
      working directory.

    * Ensure that the directory "hknight" exists as a subdirectory of "sound".

    * Write the resource's contents as "grunt.wav" in that "hknight" directory.

    This function will always return True.

    :param orig_data: binary content of the resource
    :type orig_data:  str
    :param name:      resource name
    :type name:       str

    :returns: True
    :rtype:   bool

    """
    real_path = os.path.join(*name.split("/"))
    out_dir = os.path.dirname(real_path)
    if out_dir:
        try:
            os.makedirs(out_dir)
        except OSError, e:
            if e.errno != errno.EEXIST:
                raise
    with open(real_path, 'wb') as outstream:
        outstream.write(orig_data)
    return True

def extract_resources(sources, targets=None):
    """Extract resources contained in one or more pak files.

    Convenience function for invoking :func:`process_resources` with the
    :func:`nop_converter` function as the converter argument.

    See :func:`process_resources` for more discussion of the return value
    and the handling of the ``targets`` argument.

    :param sources: file path of the pak file to process, or an iterable
                    specifying multiple such paths
    :type sources:  str or iterable(str)
    :param targets: resources to select, as described for
                    :func:`process_resources`; contents may be modified
    :type targets:  dict(str,str) or set(str) or None

    :returns: True if no IOError exception reading the pak file and no
              exception extracting any resource, False otherwise
    :rtype:   bool

    """
    return process_resources(sources, nop_converter, targets)

def resource_names_int(pak_path):
    """Return the name of every resource in a pak file.

    Implement :func:`resource_names` for a single pak file.

    :param pak_path: file path of the pak file to read
    :type pak_path:  str

    :returns: set of resource name strings if no read errors, None otherwise
    :rtype:   set(str) or None

    """
    try:
        with open(pak_path, 'rb') as instream:
            target_info = get_target_info(instream, None)
            if target_info is None:
                if print_err:
                    sys.stderr.write("%s is not a pak file\n" % pak_path)
                return None
        # 2.6 COMPAT: "set comprehension" syntax
        return set(t[0] for t in target_info)
    except IOError:
        if print_err:
            sys.stderr.write("%s exception reading pak %s\n" %
                             (repr(sys.exc_info()[1]), pak_path))
        return None

def resource_names(sources):
    """Return the name of every resource in one or more pak files.

    Return a set of resource name strings collected from all of the given pak
    files, if each specified file is a pak file and is read without I/O errors.
    Otherwise return None.

    :param sources: file path of the pak file to read, or an iterable
                    specifying multiple such paths
    :type sources:  str or iterable(str)

    :returns: set of resource name strings if no read errors, None otherwise
    :rtype:   set(str) or None

    """
    # Handle single-string input for the sources argument.
    if isinstance(sources, basestring):
        return resource_names_int(sources)
    # Handle iterable input for the sources argument.
    all_resources = set()
    for pak_path in sources:
        resources = resource_names_int(pak_path)
        if resources is None:
            return None
        all_resources.update(resources)
    return all_resources

def usage():
    """Print the usage message for :func:`simple_expak`.

    """
    script = "simple_expak"
    print("")
    print("To extract all resources from pak files:")
    print("    %s <pak_a.pak> [<pak_b.pak> ...]" % script)
    print("examples:")
    print("    %s pak0.pak pak1.pak" % script)
    print("")
    print("To extract specific resources from pak files:")
    print("    %s <pak_a.pak> [<pak_b.pak> ...] <res_1> [<res_2> ...]" % script)
    print("examples:")
    print("    %s pak1.pak sound/misc/basekey.wav" % script)
    print("    %s pak0.pak pak1.pak maps/e1m1.bsp maps/e2m1.bsp maps/e3m1.bsp" % script)
    print("")

def simple_expak(argv=None):
    """
    Installation of the :mod:`expak` module will also install a
    :program:`simple_expak` utility in your path. This utility exists to
    essentially perform the same kinds of operations as supported by
    :func:`expak.extract_resources`, but with a model better suited for quick
    manual command-line use.

    :program:`simple_expak` accepts any number of command-line arguments. Any
    argument that ends in ".pak" (case-insensitive) is treated as a pak file
    path; any other argument is treated as the name of a resource to extract
    from the pak file(s). Pak file paths and resource names can be freely
    intermingled.

    If one or more pak files are specified, but no resources, then all resources
    are extracted from all of the specified pak files.

    Example of extracting all resources from "pak0.pak" and "pak1.pak":

    .. code-block:: none

        simple_expak pak0.pak pak1.pak

    Examples of extracting specific resources from pak files:

    .. code-block:: none

        simple_expak pak1.pak sound/misc/basekey.wav

        simple_expak pak0.pak pak1.pak maps/e1m1.bsp maps/e2m1.bsp maps/e3m1.bsp

    Whenever a resource is extracted from a pak file, it will be created under
    a directory path relative to the current working directory, determined by
    the resource name as described for the :func:`expak.nop_converter` function.

    If any user-specified resources are not found, or are unable to be
    extracted, then :program:`simple_expak` will print a list of such resources
    once it is done.

    An I/O error during reading a pak file or writing an extracted resource will
    not prevent :program:`simple_expak` from continuing with other pak files or
    resources. Once :program:`simple_expak` is done processing as many
    paks/resources as possible, it will exit with a status of 0 if no such
    exceptions were encountered, or 1 otherwise.

    .. note::

         :program:`python -m expak` behaves identically to
         :program:`simple_expak`.

    """
    # Normal use (when invoked from the utility) passes in None for argv, and
    # arguments are then taken from the command line. For testing however, other
    # arguments can be passed directly to this function.
    if argv is None:
        argv = sys.argv[1:]
    # Print usage message and exit if no arguments given.
    if not argv:
        usage()
        return 0
    # Separate args into pak files and resources.
    pak_paths, targets = set(), set()
    for a in argv:
        if a[-4:].lower() == ".pak":
            pak_paths.add(a)
        else:
            targets.add(a)
    if not targets:
        targets = None
    # Extract those resources from those pak files.
    success = extract_resources(pak_paths, targets)
    # Print any specified resources not found/extracted.
    if targets:
        print("not found (or not successfully extracted):")
        for p in targets:
            print("    %s" % p)
    # All done!
    if success:
        return 0
    else:
        return 1

if __name__ == "__main__":
    sys.exit(simple_expak())
