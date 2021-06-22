#! /usr/bin/env python3
'''
    Safeget downloads and verifies files from online.

    If you would like a simple custom safeget for your app
    which embeds all the parameters usually passed on the
    command line, contact support@denova.com. It's free.
    Your users then run that simple small program to download
    and fully verify your app, without the hassles.

    Learn more at https://denova.com/open/safeget/

    This is intentionally a single file to make it easier
    to verify safeget itself.

    Copyright 2019-2021 DeNova
    Last modified: 2021-06-20
'''

import argparse
import hashlib
import json
import os
import platform
import re
import shlex
import subprocess
import sys

from glob import glob
from http.cookiejar import CookieJar
from random import choice
from shutil import rmtree
from tempfile import mkdtemp
from traceback import format_exc
from urllib.error import HTTPError, URLError
from urllib.parse import urlencode, urlparse
from urllib.request import build_opener, urlopen, HTTPCookieProcessor, ProxyHandler, Request


CURRENT_VERSION = '1.4.9'
COPYRIGHT = 'Copyright 2019-2021 DeNova'
LICENSE = 'GPLv3'

DEFAULT_TRIES = 20 # wget default
# use standard text streams for stdin, stdout and stderr
STD_TEXT_STREAMS = True
TMP_DIR = mkdtemp(prefix='safeget.')

args = None

gpg_path = 'gpg'

system = platform.system()

target_host = None
localpath_hash_cache = {}

testing = False
failed = False


class SafegetException(Exception):
    pass

def main():
    ''' Get dependencies. Get file. Verify file.
        Optionally, install file or run command with file.
    '''

    parse_args()

    if args.version:
        show_version()

    else:
        start_safeget()

def start_safeget():
    ''' Start safeget itself. '''

    try:
        verify_args()

        if 'app' in args:
            notice(f'Safely get {args.app}\n')

        install_dependencies()

        if 'noselfcheck' in args and not args.noselfcheck:
            notice('Check... ')
            verify_safeget_itself()

        if is_url(args.target):

            url = args.target
            local_target = os.path.basename(url)
            notice('Download... ')
            if testing and os.path.exists(local_target):
                pass
            else:
                download(url, local_target)

        else:
            local_target = args.target
            if not os.path.exists(local_target):
                fail(f'file does not exist: {os.path.abspath(local_target)}')

        verify_file(local_target)

        if args.run:
            notice('Run... ')
            kwargs = {'interactive': True}
            safeget_run(*[args.target], **kwargs)
            print('Finished.')

        if args.after:
            run_command_after(args.after)

        if not testing:
            delete_temp_dir()

        more()

    except SafegetException as sgex:
        if args.debug:
            # show the traceback, or allow test to catch the error
            raise

        print(f'\n\n{sgex}\n\n')
        sys.exit(1)

    except KeyboardInterrupt:
        print('stopped by user')
        if args.debug:
            # show the traceback
            # in case the Ctrl-C was to see where the program was stuck
            raise

        sys.exit(2)

def show_version():
    ''' Show the app's name and version if known
        or safeget's version otherwise. '''

    if 'app' in args:
        notice(f'{args.app}\n')
    else:
        details = f'\nSafeget {CURRENT_VERSION}\n{COPYRIGHT}\nLicense: {LICENSE}\n\n'
        notice(details)

def more():
    ''' Let them know where to get more safeget commands. '''

    print('\n')
    print('Find more safegets at https://denova.com/open/safeget/custom/')
    print('\n')

def notice(msg):
    ''' Print short notice message without newline. '''

    print(msg, end='', flush=True)

def verbose(msg):
    ''' Print verbose message. '''

    # args.debug implies args.verbose
    if args.verbose or args.debug:
        print(msg)

def debug(msg):
    ''' Print debug message. '''

    if args is None or args.debug:
        print(msg)

def fail(msg):
    ''' Failure exit. '''

    raise SafegetException(f'Failed: {msg}')

def warn(msg):
    ''' Warn user. '''

    print()
    print(f'Warning: {msg}')

def which(program):
    ''' Return path to command. '''

    def search_path(program):
        path = None

        entries = os.get_exec_path()
        for entry in entries:
            if os.path.exists(os.path.join(entry, program)):
                path = entry
                break

        return path

    if running_on_windows():
        command_args = ['where', program]

    else:
        which_path = '/usr/bin/which'

        if not os.path.exists(which_path):
            which_path = 'which'

        # if no 'which', check for command existence with:
        #     run(program, '--help')
        command_args = [which_path, program]

    try:
        path = run(*command_args)
    except subprocess.CalledProcessError:

        # Windows "where" doesn't look everywhere for an app
        if running_on_windows():
            path = search_path(program)
        else:
            path = None

    if path is not None:
        if not isinstance(path, str):
            path = path.decode()
        path = path.strip()

    return path

def safeget_run(*command_args, **kwargs):
    ''' Run a command line in safeget's environment.

        Check more than our os.command.run() needs to.
        For example, safeget might be in a fresh debian install
        without many commands. Or we might need to be root to do
        something, etc.
    '''

    try:
        run(*command_args, **kwargs)

    except FileNotFoundError:
        fail(f'File not found: {command_args[0]}')

def install_dependencies():
    ''' Install dependencies if any are needed. '''

    global gpg_path

    try:
        # see if we can find the gpg path
        gpg_path = which('gpg')
        is_installed = gpg_path is not None
        if not is_installed and running_on_windows():
            # "where" does not look in the following dir so lets just see if it is already installed
            gpg_path = 'C:\\Program Files (x86)\\GnuPG\\bin\\gpg.exe'
            is_installed = os.path.exists(gpg_path)
    except Exception:
        is_installed = False

    if not is_installed:
        notice('Install dependencies... ')
        install_gpg()

def install_gpg():
    '''
        Verifies signatures.
        Already installed on most Linux and Mac distros.
    '''

    global gpg_path

    gpg_path = install('gpg',
                       # see https://www.gpg4win.org/download.html
                       windows_url='https://files.gpg4win.org/gpg4win-latest.exe',
                       # see https://gpgtools.org/
                       osx_url='https://releases.gpgtools.org/GPG_Suite-2020.2.dmg',
                       is_installer=True)

    debug(f'gpg path: {gpg_path}')

def install(program, windows_url=None, osx_url=None, linux_package=None, is_installer=False):
    ''' If program is not installed, try to install it.

        If is_installer=True, run the file from the url to complete the installation.
        This is not the same as --run, since if we are installing dependencies,
        then this program and not the user decides to run the file.
    '''

    debug(f'install {program}')

    if running_on_windows():
        program_path = windows_install(program, windows_url, is_installer)

    elif running_on_mac():
        program_path = osx_install(program, osx_url, is_installer)

    elif running_on_linux():
        program_path = linux_install(program, linux_package)

    else:
        fail(f'unable to install on {system}')

    return program_path

def windows_install(program, windows_url, is_installer):
    url = windows_url
    verify_source(url)
    if not url:
        fail(f'no install url for {program}')

    verbose(f'install {program}')

    basename = os.path.basename(url)
    program_path = os.path.join(TMP_DIR, basename)

    try:
        download(url, program_path)

    except Exception as e:
        debug(e)
        # !! could be other reasons
        fail(f'rerun this program as admin to install {program}')

    else:
        if is_installer:
            GPG_DIR = 'C:\\Program Files (x86)\\GnuPG'
            # run the installer silently
            safeget_run(*[program_path, '/S', '/D', GPG_DIR])
            gpg_exec = os.path.join(GPG_DIR, 'bin', 'gpg.exe')
            if os.path.exists(gpg_exec):
                program_path = gpg_exec

    return program_path

def osx_install(program, osx_url, is_installer):
    if installed(program):
        already_installed(program)

    else:
        require_root(program)

        url = osx_url
        verify_source(url)
        if not url:
            fail(f'no install url for {program}')

        require_root(program)
        verbose(f'{program} not found. install...')
        program_path = os.path.join('/usr/local/bin', program)
        download(url, program_path)
        program = program_path

        if is_installer:
            safeget_run(*[program_path])

        install_done(program, program_path)

    return program

def linux_install(program, linux_package):
    if installed(program):
        already_installed(program)

    else:
        require_root(program)

        if linux_package is None:
            linux_package = program
        verbose(f'install linux package {linux_package}')
        # !! this assumes debian or close derivative
        # some linuxes, e.g. redhat, are different
        safeget_run(*['apt-get', 'install', linux_package])
        install_done(program, linux_package)

    return program

def require_root(program):
    if not os.geteuid() == 0:
        fail(f'install {program}, or rerun this program as root, so it can install dependencies')

def already_installed(program):
    verbose(f'{program} already installed')

def install_done(program, program_path):
    debug(f'installed {program} to {program_path}')

def installed(program):
    ''' Return True if program installed, else return False.'''

    try:
        is_installed = which(program) is not None

    except Exception:
        is_installed = False

    else:
        is_installed = True

    return is_installed

def download(url, localpath):
    ''' Download url "args.tries". '''

    verbose(f'download {url} to {os.path.abspath(localpath)}')

    # if it's ok to overwrite or user gives permission to write
    if args.overwrite_ok or ok_to_write(localpath):
        verify_source(url)

        ok = False
        reason = None
        max_tries = args.tries

        attempts = 0
        while attempts <  max_tries and not ok:
            ok, reason = download_url(url, localpath)
            attempts += 1

        if not ok:
            fail(get_details_for_failure(url, attempts, reason))

def download_url(url, localpath):
    ''' Download the url contents to localpath.

        Trap any urllib errors and simply return False.
    '''
    BUFFER_SIZE = 10 * 1024 * 1024 # 10 MB

    try:
        with urlopen(url) as data_stream:
            with open(localpath, 'wb') as localfile:

                data = data_stream.read(BUFFER_SIZE)
                while data:
                    localfile.write(data)
                    data = data_stream.read(BUFFER_SIZE)
        ok = True
        reason = None

    except HTTPError as error:
        reason = error.reason
        debug(reason)
        ok = False

    except URLError as error:
        reason = error.reason
        debug(reason)
        ok = False

    return ok, reason

def verify_file(local_target):
    ''' Verify local file.

        Network files must be downloaded first.
    '''

    notice('Verify... ')
    verbose(f'verify target file {os.path.abspath(local_target)}')

    if args.signedmsg or args.signedhash or args.sig:
        get_pubkeys()

    # in decreasing order of strength
    verify_signatures(local_target)
    verify_signed_hashes(local_target)
    verify_explicit_hashes(local_target)
    verify_size(local_target)

    if args.after or args.run:
        notice(f'Verified {os.path.basename(local_target)}... ')
    else:
        print(f'Verified {os.path.basename(local_target)}')

def verify_args():
    ''' Verify args. '''

    if not (args.sig or
            args.signedhash or
            args.hash):
        fail('File signature, signed hash, or explicit hash required')

    if args.size and not (args.sig or
                          args.signedhash or
                          args.hash):
        fail('File size alone is not enough verification. File signature, signed hash, or explicit hash required.')

    if args.sig and not args.pubkey:
        fail('Detached signature found, but required PGP public key not found.')

    if args.signedhash and not args.pubkey:
        fail('Signed hash found, but required PGP public key not found.')

    if args.pubkey and not(args.sig or
                           args.signedmsg or
                           args.signedhash):
        fail('PGP public key found. Did you want to include a file signature, or signed message, or signed hash?')

    verify_source(args.target)

def verify_source(source):
    ''' Verify file source.

        Urls must use a secure protocol on a host different than the target file host.

        Local files are considered a trusted source.
    '''

    global target_host

    SAFE_PROTOCOLS = ['https', 'sftp', 'file']

    if is_url(source):
        parts = urlparse(source)
        if parts.scheme not in SAFE_PROTOCOLS:
            protocols = ' or '.join(SAFE_PROTOCOLS)
            fail(f'url does not use a safe protocol ({protocols}): {source}')

        host = parse_host(source)

        if target_host is None:
            # verify_source() assumes first source to verify is target
            if source != args.target:
                fail('safeget error: target source must be verified first')

            target_host = host

        if not args.onehost:
            if source != args.target and target_host == host:
                # this was a fail(), but too many people use one host
                if args.debug:
                    print(f'target: {args.target}')
                warn(f'url is same host as target: {source}. Use --onehost to skip this warning.')
                # fail('url is same host as target: {}'.format(source))

    else:
        if target_host is None:
            # verify_source() assumes first source to verify is target
            target_host = args.target

def verify_safeget_itself():
    '''
        Verify safeget itself by checking the online
        database for original file size and hashes.

        Of course verifying a file using data from the file's host
        exposes a single point of failure. If an attacker cracks
        the host, they control both the file and the verification data.
        But this check has proven very valuable anyway.

        First, safeget makes it easy to do multiple checks automatically.
        Not all are strong. But additional checks increase safety, and they
        are cheap.

        Second, there are many errors and attacks that can cause a file
        mismatch, but do not require a web host crack. For example, some
        browsers cache downloaded files. If a file changes during the
        browser session, the browser reuses the old version. This function
        catches those cases.
    '''

    ok, error_message = check_safeget_itself()
    if not ok:
        fail_message = 'Unable to verify safeget.'
        if error_message is not None:
            fail_message = f'\n{error_message}'
        fail(fail_message)

def check_safeget_itself(host=None, target=None):
    '''
        Check safeget itself by checking the online
        database for original file size and hashes.

        The parameters are only passed for testing.
    '''
    HEADERS = {'User-Agent': 'DeNova Safeget 1.0'}

    ok = True
    error_message = None

    full_api_url, encoded_params, opener = setup_safeget_check(host=host, target=target)
    request = Request(full_api_url, encoded_params, HEADERS)

    handle = opener.open(request)
    page = handle.read().decode().strip()

    # strip out the html
    i = page.find('{')
    if i >= 0:
        page = page[i:]
    i = page.rfind('}')
    if i >= 0:
        page = page[:i+1]

    result = json.loads(page)
    if isinstance(result, bytes):
        result = result.decode()
    if 'quick-query' in result:
        if result['quick-query']['ok']:
            ok, error_message = safeget_ok(result)

        elif 'message' in result['quick-query']:
            ok = False
            error_message = result['quick-query']['message']
    else:
        ok = False
        error_message = f'Unable to verify safeget: {result}'

    if not ok:
        debug(error_message)

    return ok, error_message

def setup_safeget_check(host=None, target=None):
    '''
        Set up to check safeget itself.

        The parameters are only passed for testing.
    '''

    HOST = 'https://denova.com'
    API_URL = 'open/safeget/api/'

    if host is None:
        host = HOST

    if target is None:
        target = args.target

    full_api_url = os.path.join(host, API_URL)
    if args and args.proxy:
        i = args.proxy.find('://')
        if i > 0:
            algo = args.proxy[:i]
            ip_port = args.proxy[i+len('://'):]
            proxy = {algo: ip_port}
        else:
            fail('--proxy must be in the format: https://IP:PORT or http://IP:PORT')

        proxy_handler = ProxyHandler(proxy)
        opener = build_opener(proxy_handler, HTTPCookieProcessor(CookieJar()))
    else:
        opener = build_opener(HTTPCookieProcessor(CookieJar()))

    PARAMS = {'action': 'quick-query', 'api_version': '1.1', 'target': target}
    encoded_params = urlencode(PARAMS).encode()

    return full_api_url, encoded_params, opener

def hashes_match(original, local, algo):
    ok = original == local
    if not ok:
        debug(f'The {algo} hash does not match the original: {original}')
        debug(f'                                      local: {local}')
    return ok

def safeget_ok(result):

    ok = False
    error_message = None

    full_path = os.path.realpath(os.path.abspath(__file__))
    filename = os.path.basename(full_path)

    original_safeget_bytes = result['quick-query']['message']['safeget-bytes']
    if isinstance(original_safeget_bytes, str):
        original_safeget_bytes = int(original_safeget_bytes.replace(',', ''))
    local_safeget_bytes = os.path.getsize(full_path)
    ok = original_safeget_bytes == local_safeget_bytes
    if ok:
        with open(full_path, 'rb') as input_file:
            lines = input_file.read()

        original_safeget_sha512 = result['quick-query']['message']['safeget-sha512']
        local_safeget_sha512 = hashlib.sha512(lines).hexdigest()
        ok = hashes_match(original_safeget_sha512, local_safeget_sha512, 'SHA512')
        if ok:
            original_safeget_sha256 = result['quick-query']['message']['safeget-sha256']
            local_safeget_sha256 = hashlib.sha256(lines).hexdigest()
            ok = hashes_match(original_safeget_sha256, local_safeget_sha256, 'SHA256')

        # if neither hash is ok, then warn the user
        if not ok:
            error_message = f'The hash of {filename} does not match the original.\n'
    else:
        debug(f'safeget does not match: original: {original_safeget_bytes} local: {local_safeget_bytes}')
        error_message = f'Your local copy of {filename} does not match the original.'

    if error_message is not None:
        error_message += ' IMPORTANT: You should download the safeget installer again.'

    return ok, error_message

def verify_size(localpath):
    ''' Verify file size. '''

    if args.size:
        verbose('verify file size')

        args_size = args.size
        try:
            if isinstance(args_size, str):
                args_size = int(args_size.replace(',', ''))
        except ValueError:
            raise ValueError('size must be an integer')
        else:
            if os.path.getsize(localpath) == args_size:
                debug('verified file size')
            else:
                fail(f'file size is not {args_size}')

def verify_signed_hashes(localpath):
    ''' Verify signed file hashes match localpath.
    '''

    def check_signed_hash_file(localpath,
                               signed_hash_file,
                               algo):

        matched = False
        if clean_gpg_data(signed_hash_file):
            url_content = readfile(signed_hash_file)
            try:
                matched = search_for_hash(localpath, signed_hash_file, algo, url_content)
            except Exception as e:
                debug(e)
                debug(format_exc())

        return matched

    algos_available = hash_algorithms()

    if args.signedhash:
        verbose('verify target file matches signed hashes')

        matched = False
        for signed_hash_arg in args.signedhash:
            algo, source = parse_hash(signed_hash_arg)

            if algo not in algos_available:
                fail(f"{algo} not in available hash algorithms: {' '.join(algos_available)}")

            # verify hashes are in a pgp signed message

            signed_data_files = verify_signed_messages(source)
            debug(f'{len(signed_data_files)} signed data files')

            # just one has to match
            # hashes for other algorithms, file versions will not match
            for signed_hash_file in signed_data_files:
                if not matched:
                    matched = check_signed_hash_file(localpath,
                                                     signed_hash_file,
                                                     algo)

        if not matched:
            fail(f'no matching signed hash found in {args.signedhash}')

def verify_explicit_hashes(localpath):
    ''' Verify explicit file hashes match localpath.
    '''

    algos_available = hash_algorithms()

    if args.hash:
        verbose('verify data file matches explicit hashes')

        # every explicit hash on the command line must match
        for hash_arg in args.hash:
            algo, hash_or_url = parse_hash(hash_arg)

            if algo not in algos_available:
                fail(f"{algo} not in available hash algorithms: {' '.join(algos_available)}")

            matched = False
            if is_url(hash_or_url):
                url = hash_or_url
                verify_source(url)
                hashpath = get_temp_filename()
                download(url, hashpath)
                debug(f'hash url {url} saved in {hashpath}')
                url_content = readfile(hashpath)
                matched = search_for_hash(localpath, hashpath, algo, url_content)

            else:
                expected_hash = hash_or_url
                debug(f'command line arg algo: {algo}, expected_hash: {expected_hash}')
                if algo and expected_hash:
                    actual_hash = hash_data(algo, localpath)
                    matched = compare_hashes(algo, expected_hash, actual_hash)

            if not matched:
                fail(f'{os.path.abspath(localpath)} expected hash did not match actual hash {algo}:{actual_hash}')

def hash_algorithms():
    ''' Return available hash algorithms.

        Make the algos all lower case.

        hashlib's docs do not match its behavior.

        From hashlib.algorithms_available::
            set(['blake2s256', 'BLAKE2s256', 'SHA224', 'SHA1',
                 'SHA384', 'blake2b512', 'MD5-SHA1', 'SHA256',
                 'SHA512', 'MD4', 'md5', 'sha1', 'sha224',
                 'ripemd160', 'MD5', 'BLAKE2b512', 'md4',
                 'sha384', 'md5-sha1', 'sha256', 'sha512',
                 'RIPEMD160', 'whirlpool'])

        This appears to be a representation bug. The
        expression will result in a set of the list elements.

        We can also use openssl:
            # for type in sha sha1 mdc2 ripemd160 sha224 sha256 sha384 sha512 md2 md4 md5 dss1
            for type in sha1 sha256 sha512 md5
            do
                openssl dgst -$type "$@"
            done
    '''

    algos = set()
    for algo in hashlib.algorithms_available:
        algos.add(algo.lower())
    debug(f'hashlib.algorithms_available: {algos}')

    return algos

def hash_data(algo, localpath):
    ''' Hash file with algo.

        Uses cache.

        Returns hex of the file's hash as a bytestring.
    '''

    BUFFER_SIZE = 100000

    source = f'{algo}:{localpath}'
    if source not in localpath_hash_cache:

        h = hashlib.new(algo)
        # read directly from file instead of preloaded bytes so we can
        # hash large data without running out of memory
        # open binary because we hash byte by byte
        with open(localpath, 'rb') as datafile:
            data = datafile.read(BUFFER_SIZE)
            while data:
                h.update(data)
                data = datafile.read(BUFFER_SIZE)

        localpath_hash_cache[source] = h.hexdigest().lower()

    return localpath_hash_cache[source]

def hash_failed(algo, expected_hash, actual_hash):
    debug("only one hash has to match; this one didn't")
    debug(f'    expected {algo} hash: {expected_hash}')
    debug(f'    actual {algo} hash: {actual_hash}')

def search_for_hash(localpath, signed_hash_file, algo, url_content):
    debug(f'search_for_hash {algo}:{signed_hash_file}')

    actual_hash = hash_data(algo, localpath)
    ok = actual_hash in url_content
    if ok:
        debug(f'verfied {algo} hash from url')

    else:
        hash_failed(algo, f'not found in {signed_hash_file}', actual_hash)

    return ok

def compare_hashes(algo, expected_hash, actual_hash):
    debug(f'compare_hashes {algo}:{expected_hash}')

    ok = (expected_hash == actual_hash)
    if ok:
        debug(f'verfied explicit {algo} hash')
    else:
        hash_failed(algo, expected_hash, actual_hash)
    return ok

def get_pubkeys():
    ''' Download and import public keys.

        Because keys servers are slow and unreliable, we don't use them.
    '''

    if args.pubkey:
        verbose('get pubkeys')

        PUBKEY_PATTERN = r'\-+\s*BEGIN PGP PUBLIC KEY BLOCK\s*\-+.*?\-+\s*END PGP PUBLIC KEY BLOCK\s*\-+\s*'
        pubkey_paths, online_pubkeys = save_patterns(PUBKEY_PATTERN, args.pubkey)
        for keypath in pubkey_paths:
            debug(f'pubkey path: {keypath}')
            if clean_gpg_data(keypath):
                safeget_run(*[gpg_path, '--import', keypath])
            debug(f'imported pgp public key from: {keypath}')

        if not args.debug:
            for path in online_pubkeys:
                os.remove(path)

def verify_signed_messages(source):
    ''' Get and verify gpg signed messages.

        A pgp signed message begins with "BEGIN PGP SIGNED MESSAGE"
        and ends with "END PGP SIGNATURE". It contains both the signed
        content and the signature.
    '''

    verbose(f'verify signed message at {source}')

    # get pgp signed messages before pgp file signatures because
    # ideally the sigs are signed
    # we want to know if the sigs are good before we use them
    SIGNED_MESSAGE_PATTERN = r'\-+\s*BEGIN PGP SIGNED MESSAGE\s*\-+.*?\-+\s*END PGP SIGNATURE\s*\-+\s*'
    # save_patterns() wants an iterable, so '[source]'
    signedmsg_paths, online_signed_msgs = save_patterns(SIGNED_MESSAGE_PATTERN, [source])

    verified_signedmsg_paths = []
    for signedmsg_path in signedmsg_paths:
        if clean_gpg_data(signedmsg_path):
            # read as a stream so we can handle big files
            with open(signedmsg_path, 'r') as infile:
                try:
                    kwargs = {'stdin': infile}
                    safeget_run(*[gpg_path, '--verify'], **kwargs)
                except Exception as ex:
                    debug(f'could not verify signed message saved in {signedmsg_path}')
                    debug(ex)
                else:
                    verified_signedmsg_paths.append(signedmsg_path)
                    verbose(f'verified pgp signed message: {signedmsg_path}')

    if not args.debug:
        for path in online_signed_msgs:
            os.remove(path)

    return verified_signedmsg_paths

def verify_signatures(local_target):
    ''' Get and verify gpg detached signatures for a file.

        A pgp detached signature begins with "BEGIN PGP SIGNATURE"
        and ends with "END PGP SIGNATURE". It just contains the
        signature. The signed data is in a separate file.
    '''

    if args.sig:
        verbose('verify pgp detached signature')

        # get pgp detached signatures for a file
        SIG_PATTERN = r'\-+\s*BEGIN PGP SIGNATURE\s*\-+.*?\-+\s*END PGP SIGNATURE\s*\-+\s*'
        sig_paths, online_sigs = save_patterns(SIG_PATTERN, args.sig)
        for sigpath in sig_paths:
            if clean_gpg_data(sigpath):
                try:
                    safeget_run(*[gpg_path, '--verify', sigpath, local_target])
                except Exception as ex:
                    debug(f'could not verify pgp detached signature saved in {sigpath}')
                    debug(ex)
                else:
                    verbose(f'verified pgp detached signature: {args.sig}')

        if not args.debug:
            for path in online_sigs:
                os.remove(path)

def parse_hash(text):
    ''' Text must be:
            hash algorithm
            ':'
            hash or url
    '''

    algo, __, hash_or_url = text.partition(':')
    algo = algo.lower()

    # if a url with no algo was specified, the second component would start with //
    if (not algo) or (not hash_or_url) or (hash_or_url.startswith('//')):
        fail(f'in hash expected "ALGORITHM:..." e.g. "SHA512:D6E8..." or "SHA256:https://...", got {text}')

    if not is_url(hash_or_url):
        # hashes should be lower case with no spaces
        hash_or_url = hash_or_url.lower()
        hash_or_url = re.sub(' ', '', hash_or_url)

    return algo, hash_or_url

def extract_patterns(pattern, localpath):
    ''' Extract all instances of text matching pattern from file '''

    paths = []
    content = readfile(localpath)

    debug(f'extract {pattern} from {localpath}')

    matches = re.findall(pattern, content, flags=re.DOTALL)
    if matches:
        debug(f'matches:\n{matches}')
        for text in matches:
            path = get_temp_filename()
            with open(path, 'w') as keysfile:
                keysfile.write(text)
            paths.append(path)

    else:
        debug(f'pattern not found: {pattern}')

    return paths

def save_patterns(pattern, sources):
    ''' Save text matching patterns found in sources.

        'sources' is an iterable. Each item is either a filepath or url.
        save_patterns() reads the item, then searches the contents for the pattern.

        save_patterns() saves pattern matches to temporary files.

        Returns a list of the temporary file paths.
    '''

    online_paths = []
    paths = []

    for source in sources:
        if is_url(source):
            url = source
            verify_source(url)
            path = get_temp_filename()
            download(url, path)
            debug(f'url {url} saved in {path}')
            online_paths.append(path)

        else:
            path = source
            if not os.path.exists(path):
                fail(f'file not found: {path}')

        try:
            pattern_paths = extract_patterns(pattern, path)
            if not pattern_paths:
                fail(f'no "{pattern}" patterns found: {path}')
            paths.extend(pattern_paths)
        except UnicodeDecodeError:
            pass

    return paths, online_paths

def clean_gpg_data(path):
    ''' Check and clean gpg data file.

        Returns True if data seems ok. Else returns False.

        There are many pubkey and sig pages what looks like a PGP
        formatted data block, with empty content. Example:

            -----BEGIN PGP SIGNED MESSAGE-----
            ...
            -----END PGP SIGNATURE-----

        We extract these examples along with valid pgp data.
        Rightfully gpg throws an error, and we want to ignore the bad data and therefore the error.
    '''

    # very quick check for valid data
    ok = os.path.getsize(path) > 100
    if ok:
        # Some of the sigs, such as from r/bitcoin, have leading spaces.
        #    Some files have '\\n' instead of '\n' etc.

        #    We need to find out why.

        text = readfile(path)

        text = text.replace('^/s*', '')
        text = text.replace('\\n', '\n')
        text = text.replace('\\r', '')
        text = text.replace('<p>', '\n')
        text = text.replace('</p>', '\n')
        text = text.replace('<br>', '\n')
        text = text.replace('<br/>', '\n')

        assert '\\n' not in text
        with open(path, 'w') as outfile:
            outfile.write(text)

    else:
        debug(f'gpg data file too short: {path}')

    return ok

def ok_to_write(path):
    ''' If path exists and has content, ask to overwrite it.

        If no permission, fail.
    '''

    if (os.path.exists(path) and os.path.getsize(path) and not testing):

        verbose(f'{os.path.abspath(path)} already exists')
        prompt = f'\nOk to replace {os.path.abspath(path)}? '
        answer = input(prompt)
        answer = answer.lower()
        debug(f'answered: {answer}')
        ok = answer in ['y', 'yes']
        if not ok:
            fail(f'did not replace {os.path.abspath(path)}')

    else:
        ok = True

    return ok

def readfile(localpath):
    ''' Return contents of localpath as text file. '''

    with open(localpath, 'r') as datafile:
        data = datafile.read()
    return data

def persist(func, *args, **kwargs):
    ''' Retry func until success or KeyboardInterrupt. Report errors.

        This kind of stubborness often defeats DOS attacks.
        Reporting attempted censorship sometimes seems to help.
    '''

    done = False
    retries = 0
    while not done:
        try:
            result = func(*args, **kwargs)

        except Exception as e:
            report(e)
            print(f'{e}; Retry...')
            retries = retries + 1

        else:
            if retries:
                debug(f'Succeeded after {retries} retries')
            done = True

    return result

def report(msg):
    ''' Report if censorship detected. '''

    print(msg)

def is_url(s):
    ''' Returns True if url, else returns False. '''

    return '://' in s

def parse_host(url):
    ''' Returns host of url. '''

    parts = urlparse(url)
    if ':' in parts.netloc:
        host, _ = parts.netloc.split(':')
    else:
        host = parts.netloc

    return host

def parse_args():
    '''
        Return parsed args.

        Do NOT change the "def parse_args():" line above
        without also changing create_custom_safeget.py in the safeget tools dir.
    '''

    global args, testing

    parser = argparse.ArgumentParser(description='Get and verify a file.')

    parser.add_argument('target',
                        # so we can provide a better 'required' message
                        nargs='?', default=None,
                        help='url to get and verify, or file path to verify; must be the first arg on the command line.')

    parser.add_argument('--size', help='file size in bytes') # not an int to allow commas
    parser.add_argument('--hash', nargs='*',
                        help='file hash in form ALGO:HASH, ALGO:URL, or ALGO:FILE. ' +
                        'ALGO is a hash algorithm such as SHA256. HASH is a hex literal. ' +
                        'If URL or FILE, the correct hash must appear in the url or file contents')
    parser.add_argument('--pubkey', nargs='*',
                        help='url or file of pgp signing key')
    parser.add_argument('--sig', nargs='*',
                        help='url or file containing pgp detached signature')
    parser.add_argument('--signedmsg', nargs='*',
                        help='url or file containing pgp signed message')
    parser.add_argument('--signedhash', nargs='*',
                        help='url or file of pgp signed message containing file hashes in form "SHA256:URL_OR_FILE..."')
    parser.add_argument('--after',  nargs='*',
                        help='execute command after downloading and verifying the file; use && to separate commands.')
    parser.add_argument('--run', help='runs the verified file', action='store_true')

    parser.add_argument('--proxy', help='must be in the format: https://IP:PORT or http://IP:PORT', nargs='?', dest='proxy', action='store')
    parser.add_argument('--tries', help='times to retry', type=int, default=DEFAULT_TRIES)
    parser.add_argument('--verbose', help='show more details', action='store_true')
    parser.add_argument('--debug', help='show debug details', action='store_true')
    parser.add_argument('--onehost', help='skip warning when sources are not separate hosts', action='store_true')
    parser.add_argument('--overwrite_ok', help='if file found, overwrite if true', action='store_false')
    parser.add_argument('--version', help='show the product and version number', action='store_true')

    args = parser.parse_args()
    debug(f'args from argsparse: {vars(args)}')

    if args.version:
        pass
    elif 'test' in args and args.test:
        testing = True
    # if target missing, provide a better message
    elif args.target is None:
        print("\nsafeget: error: the first arg must be the url to get and verify, or file path to verify.\n")
        sys.exit(-1)

    return args

def get_details_for_failure(url, attempts, reason):
    '''
        Get the details about the failure.

        >>> url = 'https://denova.com/open/safecopy'
        >>> attempts = DEFAULT_TRIES
        >>> reason = '[Errno 53] Unable to reach server.'
        >>> message = get_details_for_failure(url, attempts, reason)
        Attempted to download 20 time(s)
        >>> 'Unable to safely get https://denova.com/open/safecopy.\\n' in message
        True
        >>> '\\tError: Unable to reach server.\\n' in message
        True
        >>> '\\tSuggestions: Check connections or try again later.' in message
        True
    '''

    debug(f'Attempted to download {attempts} time(s)')
    m = re.match('^\\[Errno \d+\\] (.*)$', str(reason))
    if m:
        reason = f'Error: {m.group(1)}'

    error = f'Unable to safely get {url}.'
    suggestions = 'Suggestions: Check connections or try again later.'
    details = f'{error}\n\t{reason}\n\t{suggestions}'

    return details

def run(*command_args, **kwargs):
    ''' Run a command line.

        Example::

            # 'ls /tmp'
            run('ls', '/tmp')

        Return command stdout and stderr.

        command_args is an iterable of args instead of a string so
        subprocess.check_output can escape args better.
    '''

    debug(f"run \"{' '.join(command_args)}\"")
    result = None

    try:
        proc_args, kwargs = get_run_args(*command_args, **kwargs)

        interactive = 'interactive' in kwargs
        if interactive:
            del kwargs['interactive']
            kwargs.update(dict(stdin=sys.stdin,
                               stdout=sys.stdout,
                               stderr=sys.stderr))

        for output in ['stdout', 'stderr']:
            if output not in kwargs:
                kwargs[output] = subprocess.PIPE
        kwargs['universal_newlines'] = STD_TEXT_STREAMS

        proc = subprocess.Popen(proc_args,
                                **kwargs)

        if args and args.debug:
            # stderr to the console's stdout
            stderr_data = ''
            line = proc.stderr.readline()
            while line:
                stderr_data = stderr_data + line
                # lines already have a newline
                print(line, end='')
                line = proc.stderr.readline()

            # get any stdout from the proc
            stdout_data, _ = proc.communicate()

        else:
            stdout_data, stderr_data = proc.communicate()

        returncode = proc.wait()

        if returncode == 0:
            result = stdout_data

        else:
            raise subprocess.CalledProcessError(returncode, command_args, stdout_data, stderr_data)

    except subprocess.CalledProcessError as cpe:
        debug(cpe)
        if cpe.returncode: debug(f'    returncode: {cpe.returncode}')
        if cpe.stderr: debug(f'    stderr: {cpe.stderr}')
        if cpe.stdout: debug(f'    stdout: {cpe.stdout}')
        raise

    return result

def get_run_args(*command_args, **kwargs):
    '''
        Get the args in list with each item a string.

        >>> from tempfile import gettempdir
        >>> # 'true' ignores args '&& false'
        >>> command_args = ['true', '&&', 'false']
        >>> kwargs = {}
        >>> get_run_args(*command_args, **kwargs)
        (['true', '&&', 'false'], {})

        >>> command_args = ['ls', '-l', gettempdir()]
        >>> kwargs = {}
        >>> get_run_args(*command_args, **kwargs)
        (['ls', '-l', '/tmp'], {})

        >>> # test command line with glob=False
        >>> command_args = ['ls', '-l', f'{gettempdir()}/denova*']
        >>> kwargs = {'glob': False}
        >>> get_run_args(*command_args, **kwargs)
        (['ls', '-l', '/tmp/denova*'], {})
    '''

    if kwargs is None:
        kwargs = {}

    if 'glob' in kwargs:
        globbing = kwargs['glob']
        del kwargs['glob']
    else:
        globbing = True

    # subprocess.run() wants strings
    args = []
    for arg in command_args:
        arg = str(arg)

        # see if the arg contains an inner string so we don't mistake that inner string
        # containing any wildcard chars. e.g., arg = '"this is an * example"'
        encased_str = ((arg.startswith('"') and arg.endswith('"')) or
                       (arg.startswith("'") and arg.endswith("'")))

        if ('*' in arg or '?' in arg):
            if globbing and not encased_str:
                args.extend(glob(arg))
            else:
                args.append(arg)
        else:
            args.append(arg)

    return args, kwargs

def run_command_after(command):
    '''
        Run the command after downloading and verifying file.
    '''

    MULTIPLE_COMMANDS = ' && '

    notice('Install... \n')

    # if there are multiple commands, then split them up
    while command.find(MULTIPLE_COMMANDS) > 0:
        i = command.find(MULTIPLE_COMMANDS)
        command_args = shlex.split(command[:i])
        kwargs = {'interactive': True}
        safeget_run(*command_args, **kwargs)

        command = command[i + len(MULTIPLE_COMMANDS):]

    command_args = shlex.split(command)
    kwargs = {'interactive': True}
    safeget_run(*command_args, **kwargs)

    notice('Installed.')

def running_on_linux():
    '''
        Return True if running on any
        Linux OS. Otherwise, return False.

        >>> running_on_linux()
        True
    '''

    return system == 'Linux'

def running_on_mac():
    '''
        Return True if running on any
        Mac OS. Otherwise, return False.

        >>> running_on_mac()
        False
    '''

    return system == 'Darwin' or system == 'macos' or 'mac os' in system

def running_on_windows():
    '''
        Return True if running on any
        Windows OS. Otherwise, return False.

        >>> running_on_windows()
        False
    '''

    return system == 'Windows'


def get_temp_filename():
    '''
        Return new temporary file path
        that is persistent, but can be
        accessed by other apps than this one.

        >>> path = get_temp_filename()
        >>> os.path.dirname(path) == TMP_DIR
        True
        >>> len(os.path.basename(path)) == 8
        True
    '''

    return os.path.join(TMP_DIR, get_random_string(8))

def delete_temp_dir():
    '''
        Delete the temporary dir created.

        >>> os.path.exists(TMP_DIR)
        True
        >>> delete_temp_dir()
    '''

    if os.path.exists(TMP_DIR):
        rmtree(TMP_DIR, ignore_errors=True)

def get_random_string(digits):
    '''
        Get a random string, digits long
        starting and ending with a letter.

        >>> s = get_random_string(8)
        >>> len(s) == 8
        True
    '''

    Random_Letters = 'ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz'
    Random_Chars = Random_Letters + '0123456789'

    random_string = choice(Random_Letters)
    if digits > 2:
        for __ in range(digits - 2):
            random_string += choice(Random_Chars)
    random_string += choice(Random_Letters)

    return random_string


if __name__ == "__main__":
    main()
