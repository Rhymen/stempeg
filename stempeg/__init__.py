from .read import read_stems
from .read import Info
from .write import write_stems
from .write import write_audio
from .write import check_available_aac_encoders

import re
import os
import subprocess as sp
from os import path as op
import argparse
import pkg_resources
import shutil

__version__ = "0.2.0"


# TODO: decide which check to use
def _check_ffmpeg_install():
    """ Ensure FFMPEG binaries are available.
    :raise OSError: If ffmpeg or ffprobe is not found.
    """
    for binary in ('ffmpeg', 'ffprobe'):
        if shutil.which(binary) is None:
            raise OSError('{} binary not found'.format(binary))


def _check_mp4box_install():
    """ Ensure MP4box binary is available.
    :raise OSError: If mp4box is not found.
    """
    for binary in ('mp4box'):
        if shutil.which(binary) is None:
            raise OSError('{} binary not found'.format(binary))


def cmd_exist(cmd):
    try:
        from shutil import which
        return shutil.which(cmd) is not None
    except ImportError:
        return any(
            os.access(os.path.join(path, cmd), os.X_OK)
            for path in os.environ["PATH"].split(os.pathsep)
        )


def ffmpeg_and_ffprobe_exists():
    return cmd_exist("ffmpeg") and cmd_exist("ffprobe")


if not ffmpeg_and_ffprobe_exists():
    raise RuntimeError('ffmpeg or ffprobe could not be found! '
                       'Please install them before using stempeg. '
                       'See: https://github.com/faroit/stempeg')


def example_stem_path():
    """Get the path to an included stem file.

    Returns
    -------
    filename : str
        Path to the stem file
    """
    return pkg_resources.resource_filename(
        __name__,
        'data/The Easton Ellises - Falcon 69.stem.mp4'
    )


def default_metadata():
    """Get the path to included stems metadata.

    Returns
    -------
    filename : str
        Path to the json file
    """
    return pkg_resources.resource_filename(
        __name__,
        'data/default_metadata.json'
    )


def ffmpeg_version():
    """Returns the available ffmpeg version

    Returns
    ----------
    version : str
        version number as string
    """

    cmd = [
        'ffmpeg',
        '-version'
    ]

    output = sp.check_output(cmd)
    aac_codecs = [
        x for x in
        output.splitlines() if "ffmpeg version " in str(x)
    ][0]
    hay = aac_codecs.decode('ascii')
    match = re.findall(r'ffmpeg version (\d+\.)?(\d+\.)?(\*|\d+)', hay)
    if match:
        return "".join(match[0])
    else:
        return None


def cli(inargs=None):
    """
    Commandline interface for receiving stem files
    """

    parser = argparse.ArgumentParser()

    parser.add_argument(
        '--version', '-V',
        action='version',
        version='%%(prog)s %s' % __version__
    )

    parser.add_argument(
        'filename',
        metavar="filename",
        help="Input STEM file"
    )

    parser.add_argument(
        '--format',
        metavar='format',
        type=str,
        default='wav',
        help="Output format"
    )

    parser.add_argument(
        '--id',
        metavar='id',
        type=int,
        nargs='+',
        help="A list of stem_ids"
    )

    parser.add_argument(
        '-s',
        type=float,
        nargs='?',
        help="start offset in seconds"
    )

    parser.add_argument(
        '-t',
        type=float,
        nargs='?',
        help="read duration"
    )

    parser.add_argument(
        'outdir',
        metavar='outdir',
        nargs='?',
        help="Output folder"
    )

    args = parser.parse_args(inargs)
    stem2files(
        args.filename,
        args.outdir,
        args.format,
        args.id,
        args.s,
        args.t
    )


def stem2files(
    stems_file,
    outdir=None,
    format="wav",
    idx=None,
    start=None,
    duration=None,
):
    info = Info(stems_file)
    S, sr = read_stems(stems_file, stem_id=idx, start=start, duration=duration)

    rootpath, filename = op.split(stems_file)

    basename = op.splitext(filename)[0]
    if ".stem" in basename:
        basename = basename.split(".stem")[0]

    if outdir is not None:
        if not op.exists(outdir):
            os.makedirs(outdir)

        rootpath = outdir

    if len(set(info.title_streams)) == len(info.title_streams):
        # titles contain duplicates
        # lets not use the metadata
        stem_names = info.title_streams
    else:
        stem_names = None

    write_stems(
        op.join(rootpath, basename, "*." + format),
        data=S,
        sample_rate=sr,
        stems_as_files=True,
        stem_names=stem_names
    )
