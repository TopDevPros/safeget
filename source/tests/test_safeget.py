#!/usr/bin/env python3
'''
    Tests safeget.

    Copyright 2019-2021 DeNova
    Last modified: 2021-06-16

    Test safeget by running the app.

    Use bitcoin core as a test case. ISOs take too long to download.

    A fake safeget could lie. So users need to check this safeget
    executable file using other means. For example, pgp signed distro
    package, or pgp sig of hash file from trusted site.

    https://www.reddit.com/r/Bitcoin/wiki/verifying_bitcoin_core

    Bitcoin Foundation publishes:
        * their pgp public keys
        * signed pgp messages containing hashes of a release
'''

import os
from subprocess import CalledProcessError
from tempfile import gettempdir
from unittest import TestCase

try:
    from denova.os.command import run, run_verbose
    from denova.os.fs import cd
    from denova.python.log import Log
except ImportError:
    sys.exit('You need the denova package from PyPI to run the tests')


CURRENT_DIR = os.path.realpath(os.path.abspath(os.path.dirname(__file__)))


SAFEGET_APP = os.path.abspath(os.path.join(CURRENT_DIR, '..', 'safeget'))
TMP_DIR = os.path.join(gettempdir(), 'safeget.test')

# this group of constants must be updated whenever the version changes
BITCOIN_VERSION = '0.21.1'
BITCOIN_FILESIZE = 33603596
# explicit hashes
# hash can be a hex string or url, with an algo prefix
BITCOIN_HASH1 = 'SHA256:366eb44a7a0aa5bd342deea215ec19a184a11f2ca22220304ebb20b9c8917e2b'
BITCOIN_HASH2 = 'SHA512:41b23363507ef2890d1adf02598885217d4d31dc75c7f6c89494f24cf633fda51d0545cd4bff1b0284211392280e771162c0f2b21116e217fee70bafa3129676'
BITCOIN_HASH3 = 'MD5:e283a98b5e9f0b58e625e1dde661201d'

# file to verify
# url created below
BITCOIN_FILENAME = f'bitcoin-{BITCOIN_VERSION}-x86_64-linux-gnu.tar.gz'

# bitcoin-core public key
BITCOIN_PUBKEY_URL = 'https://bitcoincore.org/keys/laanwj-releases.asc'

# url/file to verify
BITCOIN_LOCAL_TARGET = os.path.join(TMP_DIR, BITCOIN_FILENAME)
# url/file with signed pgp messages containing hashes
BITCOIN_LOCAL_SIGNED_HASHES_SOURCE = 'verifying_bitcoin_core'
BITCOIN_LOCAL_SIGNED_HASH = 'SHA256:' + BITCOIN_LOCAL_SIGNED_HASHES_SOURCE

# url/file with pgp pubkeys
BITCOIN_ONLINE_PUBKEY = 'https://raw.githubusercontent.com/bitcoin-core/bitcoincore.org/master/keys/laanwj-releases.asc'
# url/file with signed pgp messages containing hashes
BITCOIN_ONLINE_SIGNED_HASHES_SOURCE = f'https://bitcoin.org/bin/bitcoin-core-{BITCOIN_VERSION}/SHA256SUMS.asc'
BITCOIN_ONLINE_SIGNED_HASH = 'SHA256:' + BITCOIN_ONLINE_SIGNED_HASHES_SOURCE
# url/file to verify
BITCOIN_ONLINE_TEMPLATE = 'https://bitcoin.org/bin/bitcoin-core-{version}/{filename}'
BITCOIN_ONLINE_TARGET = BITCOIN_ONLINE_TEMPLATE.format(version=BITCOIN_VERSION, filename=BITCOIN_FILENAME)

# file to verify
# url created below
GPA_FILENAME = f'gpa-0.10.0.tar.bz2'

GPA_FILESIZE = 782455
# explicit hashes
# hash can be a hex string or url, with an algo prefix
GPA_HASH1 = 'SHA256:95dbabe75fa5c8dc47e3acf2df7a51cee096051e5a842b4c9b6d61e40a6177b1'
GPA_HASH2 = 'SHA512:87004fb0806e76012bc194f95afe9ef6044aec890b26e845f45c314e1bd8864f056ba5e32f9ef2e15b24b50840235e6e548a5e3006b255b4f1c20e0fd7710a3b'
GPA_HASH3 = 'MD5:d0ee0086aea0ad1f61f81dae9a71c253'

# url/file to verify
GPA_LOCAL_TARGET = os.path.join(TMP_DIR, GPA_FILENAME)

# url/file with pgp pubkeys
GPA_ONLINE_PUBKEY = 'https://www.gnupg.org/%28en%29/signature_key.html'
# url/file with detached signature
GPA_ONLINE_SIGNATURE = 'https://www.gnupg.org/ftp/gcrypt/gpa/gpa-0.10.0.tar.bz2.sig'
# url/file to verify
GPA_ONLINE_TARGET = f'https://www.gnupg.org/ftp/gcrypt/gpa/{GPA_FILENAME}'


log = Log()


class TestSafeget(TestCase):

    @classmethod
    def setUpClass(cls):

        # test in a temp dir
        if os.path.exists(TMP_DIR):
            if not os.path.isdir(TMP_DIR):
                os.remove(TMP_DIR)
                os.mkdir(TMP_DIR)
        else:
            os.mkdir(TMP_DIR)

        # if the local copy exists, then don't keep downloading it
        if os.path.exists(BITCOIN_LOCAL_TARGET) and os.path.getsize(BITCOIN_LOCAL_TARGET) == BITCOIN_FILESIZE:
            pass
        else:
            # get a local copy so we can run all the tests
            cls.verify_success(cls,

                               'online target',

                                BITCOIN_ONLINE_TARGET,

                                '--size',
                                BITCOIN_FILESIZE,

                                '--pubkey',
                                BITCOIN_ONLINE_PUBKEY,

                                '--signedhash',
                                BITCOIN_ONLINE_SIGNED_HASH)

    def test_app(self):
        ''' Test the app locally. '''

        self.verify_success('local target',

                             BITCOIN_LOCAL_TARGET,

                             '--size',
                             BITCOIN_FILESIZE,

                            '--pubkey',
                            BITCOIN_ONLINE_PUBKEY,

                            '--signedhash',
                            BITCOIN_ONLINE_SIGNED_HASH)

    def test_explicit_hashes(self):
        ''' Test the explicit hashes. '''

        self.verify_success('explicit hashes',

                     # earlier tests should have made BITCOIN_LOCAL_TARGET available
                     BITCOIN_LOCAL_TARGET,

                     '--hash',
                     BITCOIN_HASH1,
                     BITCOIN_HASH2,
                     BITCOIN_HASH3)

    def test_not_enough_args(self):
        ''' Test when there aren't enough args. '''

        self.verify_failure('not enough args',

                       BITCOIN_ONLINE_SIGNED_HASH,

                       '--pubkey',
                       BITCOIN_ONLINE_PUBKEY)

    def test_target_missing(self):
        ''' Test when the target arg is missing. '''

        self.verify_failure('target missing',

                     'expected_to_fail_' + BITCOIN_ONLINE_TARGET,

                     '--hash',
                     BITCOIN_HASH1,
                     BITCOIN_HASH2,

                     '--pubkey',
                     BITCOIN_ONLINE_PUBKEY,

                     '--signedhash',
                     BITCOIN_ONLINE_SIGNED_HASH)

    def test_wrong_hash(self):
        ''' Test when the hash is wrong. '''

        self.verify_failure('wrong hash',

                     BITCOIN_LOCAL_TARGET,

                     '--hash',
                     'expected_to_fail_' + BITCOIN_HASH1,
                     BITCOIN_HASH2,

                     '--pubkey',
                     BITCOIN_ONLINE_PUBKEY,

                     '--signedhash',
                     BITCOIN_ONLINE_SIGNED_HASH)

    def test_not_enough_args(self):
        ''' Test when the pubkey is wrong. '''

        self.verify_failure('wrong pubkey',

                     BITCOIN_LOCAL_TARGET,

                     '--hash',
                     BITCOIN_HASH1,
                     BITCOIN_HASH2,

                     '--pubkey',
                     'expected_to_fail_' + BITCOIN_ONLINE_PUBKEY,

                     '--signedhash',
                     BITCOIN_ONLINE_SIGNED_HASH)

    def test_wrong_signed_has(self):
        ''' Test when there aren't enough args. '''

        self.verify_failure('wrong signed hash',

                     BITCOIN_LOCAL_TARGET,

                     '--hash',
                     BITCOIN_HASH1,
                     BITCOIN_HASH2,

                     '--pubkey',
                     BITCOIN_ONLINE_PUBKEY,

                     '--signedhash',
                     'expected_to_fail_' + BITCOIN_LOCAL_SIGNED_HASHES_SOURCE)

    def test_version(self):
        ''' Test that the version show up. '''

        args = ['python3', SAFEGET_APP] + ['--version']

        results = run(*args)
        self.assertEqual(results.returncode, 0)
        self.assertIn('Safeget', results.stdout)
        self.assertIn('Copyright', results.stdout)
        self.assertIn('GPLv3', results.stdout)

    def verify_success(self, description, *test_args):
        ''' This test should succeed. '''

        log(f'Test {description}\n\t')
        log(f'args: {test_args}')

        with cd(TMP_DIR):

            try:
                args = ['python3', SAFEGET_APP] + list(test_args) + ['--verbose']
                log(f'{description} args: {args}')

                run_verbose(*args)

            except CalledProcessError as cpe:
                log(cpe)
                raise(cpe)

            except Exception:
                log('Error in test')
                raise('Error in test')

            else:
                log(f'Passed {description}')

    def verify_failure(self, description, *test_args):
        # this test should fail

        log(f'Test {description}\n\t')

        with cd(TMP_DIR):

            try:
                args = ['python3', SAFEGET_APP] + list(test_args) + ['--verbose']
                log(f'{description} args: {args}')

                run(*args)

            except CalledProcessError as cpe:
                log(cpe)
                log('Passed: Test of failure condition failed as expected')

            except Exception:
                log('Error in test')
                self.assertFalse()

            else:
                log('Failed: Test of failure condition incorrectly succeeded')
                self.assertFalse()
