#!/usr/bin/env python3
'''
    Tests safeget.

    Copyright 2019-2021 DeNova
    Last modified: 2021-02-16

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
    from denova.python.log import get_log
except ImportError:
    sys.exit('You need the denova package from PyPI to run the tests')


CURRENT_DIR = os.path.realpath(os.path.abspath(os.path.dirname(__file__)))


SAFEGET_APP = os.path.abspath(os.path.join(CURRENT_DIR, '..', 'safeget'))
TMP_DIR = os.path.join(gettempdir(), 'safeget.test')

# this group of constants must be updated whenever the version changes
BITCOIN_VERSION = '0.21.0'
FILESIZE = 33433481
# explicit hashes
# hash can be a hex string or url, with an algo prefix
HASH1 = 'SHA256:da7766775e3f9c98d7a9145429f2be8297c2672fe5b118fd3dc2411fb48e0032'
HASH2 = 'SHA512:6969cb86bf932c402b5a1cb4ee22c05a8c2cc4c0842b70cbf34a6c2200703731ad2dcdad5b390eee0a8e4dea5340ef6873232be6e9ec209373524369038a92e5'
HASH3 = 'MD5:be2caf516b721248af85e80882edc26b'

# file to verify
# url created below
FILENAME = f'bitcoin-{BITCOIN_VERSION}-x86_64-linux-gnu.tar.gz'

# bitcoin-core public key
BITCOIN_PUBKEY_URL = 'https://bitcoincore.org/keys/laanwj-releases.asc'

# url/file with pgp pubkeys
LOCAL_PUBKEY = 'laanwj-releases.asc'
# url/file to verify
LOCAL_TARGET = os.path.join(TMP_DIR, FILENAME)
# url/file with signed pgp messages containing hashes
LOCAL_SIGNED_HASHES_SOURCE = 'verifying_bitcoin_core'
LOCAL_SIGNED_HASH = 'SHA256:' + LOCAL_SIGNED_HASHES_SOURCE

# url/file with pgp pubkeys
ONLINE_PUBKEY = 'https://raw.githubusercontent.com/bitcoin-core/bitcoincore.org/master/keys/laanwj-releases.asc'
# url/file with signed pgp messages containing hashes
ONLINE_SIGNED_HASHES_SOURCE = 'https://www.reddit.com/r/Bitcoin/wiki/verifying_bitcoin_core'
ONLINE_SIGNED_HASH = 'SHA256:' + ONLINE_SIGNED_HASHES_SOURCE
# url/file to verify
ONLINE_TEMPLATE = 'https://bitcoin.org/bin/bitcoin-core-{version}/{filename}'
ONLINE_TARGET = ONLINE_TEMPLATE.format(version=BITCOIN_VERSION, filename=FILENAME)


log = get_log()

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
        print(f'test dir is {TMP_DIR}')

        # if the local copy exists, then don't keep downloading it
        if os.path.exists(LOCAL_TARGET) and os.path.getsize(LOCAL_TARGET) == FILESIZE:
            pass
        else:
            # get a local copy so we can run all the tests
            cls.verify_success(cls,

                               'online target',

                                ONLINE_TARGET,

                                '--size',
                                FILESIZE,

                                '--pubkey',
                                ONLINE_PUBKEY,

                                '--signedhash',
                                ONLINE_SIGNED_HASH)

    def test_app(self):
        ''' Test the app locally. '''

        self.verify_success('local target',

                             LOCAL_TARGET,

                             '--size',
                             FILESIZE,

                            '--pubkey',
                            ONLINE_PUBKEY,

                            '--signedhash',
                            ONLINE_SIGNED_HASH)

    def test_explicit_hashes(self):
        ''' Test the explicit hashes. '''

        self.verify_success('explicit hashes',

                     # earlier tests should have made LOCAL_TARGET available
                     LOCAL_TARGET,

                     '--hash',
                     HASH1,
                     HASH2,
                     HASH3)

    def test_not_enough_args(self):
        ''' Test when there aren't enough args. '''

        self.verify_failure('not enough args',

                       ONLINE_SIGNED_HASH,

                       '--pubkey',
                       ONLINE_PUBKEY)

    def test_target_missing(self):
        ''' Test when the target arg is missing. '''

        self.verify_failure('target missing',

                     'expected_to_fail_' + ONLINE_TARGET,

                     '--hash',
                     HASH1,
                     HASH2,

                     '--pubkey',
                     ONLINE_PUBKEY,

                     '--signedhash',
                     ONLINE_SIGNED_HASH)

    def test_wrong_hash(self):
        ''' Test when the hash is wrong. '''

        self.verify_failure('wrong hash',

                     LOCAL_TARGET,

                     '--hash',
                     'expected_to_fail_' + HASH1,
                     HASH2,

                     '--pubkey',
                     ONLINE_PUBKEY,

                     '--signedhash',
                     ONLINE_SIGNED_HASH)

    def test_not_enough_args(self):
        ''' Test when the pubkey is wrong. '''

        self.verify_failure('wrong pubkey',

                     LOCAL_TARGET,

                     '--hash',
                     HASH1,
                     HASH2,

                     '--pubkey',
                     'expected_to_fail_' + ONLINE_PUBKEY,

                     '--signedhash',
                     ONLINE_SIGNED_HASH)

    def test_wrong_signed_has(self):
        ''' Test when there aren't enough args. '''

        self.verify_failure('wrong signed hash',

                     LOCAL_TARGET,

                     '--hash',
                     HASH1,
                     HASH2,

                     '--pubkey',
                     ONLINE_PUBKEY,

                     '--signedhash',
                     'expected_to_fail_' + LOCAL_SIGNED_HASHES_SOURCE)

    def test_version(self):
        ''' Test that the version show up. '''

        args = [SAFEGET_APP] + ['--version']

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
                args = [SAFEGET_APP] + list(test_args) + ['--verbose']
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
                args = [SAFEGET_APP] + list(test_args) + ['--verbose']
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
