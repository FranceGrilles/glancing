#! /usr/bin/env python
# -*- coding: utf-8 -*-
# coding: utf-8

from __future__ import print_function

import os
import sys
import uuid
import unittest

from tutils import local_pythonpath, get_local_path

# Setup project-local PYTHONPATH
local_pythonpath('..', '..', 'src')

import utils

class UtilsTestIsIter(unittest.TestCase):

    def test_utils_isiter(self):
        self.assertTrue(utils.is_iter([i for i in range(3)]))
        self.assertTrue(utils.is_iter([]))
        self.assertFalse(utils.is_iter(1))
        self.assertFalse(utils.is_iter(1.0))
        self.assertTrue(utils.is_iter([1]))

class UtilsTestTempdir(unittest.TestCase):

    def test_utils_tempdir(self):
        oldcwd = os.getcwd()
        with utils.tempdir():
            tmp_cwd = os.getcwd()
            self.assertEqual('/tmp', os.path.dirname(tmp_cwd))
        self.assertEqual(os.getcwd(), oldcwd)
        self.assertFalse(os.path.exists(tmp_cwd))

class UtilsTestChdir(unittest.TestCase):

    def test_utils_chdir(self):
        oldcwd = os.getcwd()
        with utils.chdir('/tmp'):
            self.assertEqual(os.getcwd(), '/tmp')
        self.assertEqual(os.getcwd(), oldcwd)
        with self.assertRaises(ValueError):
            with utils.chdir(os.devnull):
                pass # pragma: no cover

@unittest.skip('FIXME')
class UtilsTestSmallSizeT(unittest.TestCase):

    #@unittest.skip('FIXME')
    def test_utils_ssize_t_repr(self):
        ssize_t = utils.small_size_t

        self.assertEqual(repr(ssize_t(0)), '<small_size_t 0>')
        self.assertEqual(repr(ssize_t(0, 'K')), '<small_size_t 0K>')

        self.assertEqual(repr(ssize_t(0, '', 'm')), '<small_size_t 0>')
        self.assertEqual(repr(ssize_t(0, 'm', 'n')), '<small_size_t 0m>')

        self.assertEqual(repr(ssize_t(1, '', 'm')), '<small_size_t 1m>')
        self.assertEqual(repr(ssize_t(1, 'm', 'n')), '<small_size_t 1nm>')

        self.assertEqual(repr(ssize_t(0.1)), '<small_size_t 0.1>')
        self.assertEqual(repr(ssize_t(0.01, 'T')), '<small_size_t 0.01T>')

        self.assertEqual(repr(ssize_t(0.1, '', 'm')), '<small_size_t 0.1m>')
        self.assertEqual(repr(ssize_t(0.01, 'A', 'n')), '<small_size_t 0.01nA>')

        self.assertEqual(repr(ssize_t(0.001, 'm', '')), '<small_size_t 0.001m>')
        self.assertEqual(repr(ssize_t(0.0001, 'm', '')), '<small_size_t 0.0001m>')

        self.assertEqual(repr(ssize_t(0.2)), '<small_size_t 0.2>')
        self.assertEqual(repr(ssize_t(0.33)), '<small_size_t 0.33>')
        self.assertEqual(repr(ssize_t(0.033, 's')), '<small_size_t 0.033s>')
        self.assertEqual(repr(ssize_t(0.0333333333, 's')), '<small_size_t 0.0333333s>')

        self.assertEqual(repr(ssize_t(0.0066)), '<small_size_t 0.0066>')
        self.assertEqual(repr(ssize_t(0.00066)), '<small_size_t 0.00066>')

        self.assertEqual(repr(ssize_t(0.00001)), '<small_size_t 0.00001>')
        self.assertEqual(repr(ssize_t(0.000001)), '<small_size_t 0.000001>')
        self.assertEqual(repr(ssize_t(0.0000001)), '<small_size_t 0.0000001>')
        self.assertEqual(repr(ssize_t(0.00000001)), '<small_size_t 0.00000001>')
        self.assertEqual(repr(ssize_t(0.000000001)), '<small_size_t 0.000000001>')
        self.assertEqual(repr(ssize_t(0.0000000001)), '<small_size_t 0.0000000001>')
        self.assertEqual(repr(ssize_t(0.0000000000001)), '<small_size_t 0.0000000000001>')
        self.assertEqual(repr(ssize_t(0.0000000000000001)), '<small_size_t 0.0000000000000001>')
        self.assertEqual(repr(ssize_t(0.0000000000000000001)), '<small_size_t 0.0000000000000000001>')

        # FIXME add more cases, like below...

    def test_utils_ssize_t_str(self):
        ssize_t = utils.small_size_t

        self.assertEqual(str(ssize_t(0)), '0')
        self.assertEqual(str(ssize_t(0, 'K')), '0K')

        self.assertEqual(str(ssize_t(0, '', 'm')), '0')
        self.assertEqual(str(ssize_t(0, 'm', 'n')), '0m')

        self.assertEqual(str(ssize_t(1000, 'A', 'n')), '1mA')
        self.assertEqual(str(ssize_t(1, 'm', 'n')), '1nm')

        self.assertEqual(str(ssize_t(0.1)), '100m')
        self.assertEqual(str(ssize_t(0.01)), '10m')
        self.assertEqual(str(ssize_t(0.001)), '1m')

        self.assertEqual(str(ssize_t(0.2)), '200m')
        self.assertEqual(str(ssize_t(0.3)), '300m')
        self.assertEqual(str(ssize_t(0.4)), '400m')
        self.assertEqual(str(ssize_t(0.5)), '500m')
        self.assertEqual(str(ssize_t(0.6)), '600m')
        self.assertEqual(str(ssize_t(0.7)), '700m')
        self.assertEqual(str(ssize_t(0.8)), '800m')
        self.assertEqual(str(ssize_t(0.9)), '900m')

        self.assertEqual(str(ssize_t(0.01, 'T')), '10mT')

        self.assertEqual(str(ssize_t(0.1, '', 'm')), '100μ')
        self.assertEqual(str(ssize_t(0.01, 'A', 'n')), '10pA')

        self.assertEqual(str(ssize_t(0.001, 'm', '')), '1mm')
        self.assertEqual(str(ssize_t(0.0001, 'm', '')), '100μm')

        self.assertEqual(str(ssize_t(0.33)), '330m')
        self.assertEqual(str(ssize_t(0.033, 's')), '33ms')
        self.assertEqual(str(ssize_t(0.0333333333, 's')), '33.3ms')

        self.assertEqual(str(ssize_t(0.0066)), '6.60m')
        self.assertEqual(str(ssize_t(0.00066)), '660μ')
        self.assertEqual(str(ssize_t(0.06060)), '60.6m')

        self.assertEqual(str(ssize_t(0.06001)), '60.0m')
        self.assertEqual(str(ssize_t(0.06002)), '60.0m')
        self.assertEqual(str(ssize_t(0.06003)), '60.0m')
        self.assertEqual(str(ssize_t(0.06004)), '60.0m')
        self.assertEqual(str(ssize_t(0.06005)), '60.0m')
        self.assertEqual(str(ssize_t(0.06006)), '60.1m')
        self.assertEqual(str(ssize_t(0.06007)), '60.1m')
        self.assertEqual(str(ssize_t(0.06008)), '60.1m')
        self.assertEqual(str(ssize_t(0.06009)), '60.1m')

        self.assertEqual(str(ssize_t(0.00001)), '10μ')
        self.assertEqual(str(ssize_t(0.000001)), '1μ')
        self.assertEqual(str(ssize_t(0.0000001)), '100n')
        self.assertEqual(str(ssize_t(0.00000001)), '10n')
        self.assertEqual(str(ssize_t(0.000000001)), '1n')
        self.assertEqual(str(ssize_t(0.0000000001)), '100p')
        self.assertEqual(str(ssize_t(0.0000000000001)), '100f')
        self.assertEqual(str(ssize_t(0.00000000000001)), '10f')
        self.assertEqual(str(ssize_t(0.000000000000001)), '1f')
        self.assertEqual(str(ssize_t(0.0000000000000000)), '0')
        self.assertEqual(str(ssize_t(0.0000000000000001)), '0')
        self.assertEqual(str(ssize_t(0.0000000000000000001)), '0')

class UtilsTestSizeT(unittest.TestCase):

    def test_utils_size_t_repr(self):
        size_t = utils.size_t

        self.assertEqual(repr(size_t(0)), '<size_t 0>')
        self.assertEqual(repr(size_t(0, 'B')), '<size_t 0B>')

        self.assertEqual(repr(size_t(2048)), '<size_t 2048>')
        self.assertEqual(repr(size_t(2048, 'B')), '<size_t 2048B>')

    def test_utils_size_t_unit(self):
        size_t = utils.size_t

        self.assertEqual(str(size_t(0, '', 'M')), '0')
        self.assertEqual(str(size_t(0, 'B', 'M')), '0B')

        # Zero is special-case for repr()
        self.assertEqual(repr(size_t(0, '', 'M')), '<size_t 0>')
        self.assertEqual(repr(size_t(0, 'B', 'M')), '<size_t 0B>')

        self.assertEqual(str(size_t(1, '', 'M')), '1M')
        self.assertEqual(str(size_t(1, 'B', 'M')), '1MB')

        self.assertEqual(repr(size_t(1, '', 'M')), '<size_t 1M>')
        self.assertEqual(repr(size_t(1, 'B', 'M')), '<size_t 1MB>')

        self.assertEqual(str(size_t(1024, '', 'M')), '1G')
        self.assertEqual(str(size_t(1024, 'B', 'M')), '1GB')

        self.assertEqual(repr(size_t(1024, '', 'M')), '<size_t 1024M>')
        self.assertEqual(repr(size_t(1024, 'B', 'M')), '<size_t 1024MB>')

    def test_utils_size_t_str(self):
        size_t = utils.size_t

        self.assertEqual(str(size_t(0)), '0')
        self.assertEqual(str(size_t(0, 'B')), '0B')

        self.assertEqual(str(size_t(10)), '10')
        self.assertEqual(str(size_t(10, 'B')), '10B')

        self.assertEqual(str(size_t(666)), '666')
        self.assertEqual(str(size_t(667, 'B')), '667B')

        self.assertEqual(str(size_t(1023)), '1023')
        self.assertEqual(str(size_t(1024)), '1K')
        self.assertEqual(str(size_t(1025)), '1K')

        self.assertEqual(str(size_t(2047)), '1K')
        self.assertEqual(str(size_t(2048)), '2K')
        self.assertEqual(str(size_t(2049)), '2K')

        self.assertEqual(str(size_t(1024 * 1024 - 1)), '1023K')
        self.assertEqual(str(size_t(1024 * 1024 + 0)), '1M')
        self.assertEqual(str(size_t(1024 * 1024 + 1)), '1M')

        self.assertEqual(str(size_t(1024 * 1024 * 1024 - 1)), '1023M')
        self.assertEqual(str(size_t(1024 * 1024 * 1024 + 0)), '1G')
        self.assertEqual(str(size_t(1024 * 1024 * 1024 + 1)), '1G')

        self.assertEqual(str(size_t(1024 * 1024 * 1024 * 1024 - 1)), '1023G')
        self.assertEqual(str(size_t(1024 * 1024 * 1024 * 1024 + 0)), '1T')
        self.assertEqual(str(size_t(1024 * 1024 * 1024 * 1024 + 1)), '1T')

        self.assertEqual(str(size_t(1024 * 1024 * 1024 * 1024 * 1024 + 0)), '1P')
        self.assertEqual(str(size_t(1024 * 1024 * 1024 * 1024 * 1024 + 1)), '1P')

        # FIXME: This last one fail: 0P != 1023T
        #self.assertEqual(str(size_t(1024 * 1024 * 1024 * 1024 * 1024 - 1)), '1023T')

class UtilsVerbosityTest(unittest.TestCase):

    def test_utils_get_verbose_is_boolean(self):
        v = utils.get_verbose()
        self.assertTrue((v is True) or (v is False))

    def test_utils_set_verbose_toggle(self):
        v = utils.get_verbose()
        utils.set_verbose()
        self.assertFalse(v == utils.get_verbose())
        utils.set_verbose()
        self.assertTrue(v == utils.get_verbose())

    def test_utils_set_verbose_value(self):
        v = utils.get_verbose()
        utils.set_verbose(True)
        self.assertTrue(utils.get_verbose() is True)
        utils.set_verbose(False)
        self.assertTrue(utils.get_verbose() is False)
        utils.set_verbose(v)
        self.assertTrue(utils.get_verbose() == v)

    def vprint_verbose(self, verbosity, test_name):
        v = utils.get_verbose()
        utils.set_verbose(verbosity)
        with utils.stringio() as output:
            expected = ''
            if verbosity:
                expected = test_name + ': TOTOTITI\n'
            with utils.redirect('stdout', output):
                utils.vprint('TOTOTITI', test_name)
                self.assertEqual(expected, output.getvalue())
            self.assertEqual(expected, output.getvalue())
        with self.assertRaises(ValueError):
            output.getvalue()
        utils.set_verbose(v)

    def vprint_lines_verbose(self, verbosity, test_name):
        v = utils.get_verbose()
        utils.set_verbose(verbosity)
        with utils.stringio() as output:
            expected = ''
            if verbosity:
                expected = test_name + ': TOTO\n' + test_name + ': TITI\n'
            with utils.redirect('stdout', output):
                utils.vprint_lines('TOTO\nTITI', test_name)
                self.assertEqual(expected, output.getvalue())
            self.assertEqual(expected, output.getvalue())
        with self.assertRaises(ValueError):
            output.getvalue()
        utils.set_verbose(v)

    def test_utils_vprint_verbose(self):
        self.vprint_verbose(True, utils.test_name())

    def test_utils_vprint_silent(self):
        self.vprint_verbose(False, utils.test_name())

    def test_utils_vprint_lines_verbose(self):
        self.vprint_lines_verbose(True, utils.test_name())

    def test_utils_vprint_lines_silent(self):
        self.vprint_lines_verbose(False, utils.test_name())


class UtilsTest(unittest.TestCase):

    def test_utils_test_name(self):
        self.assertEqual(utils.test_name(), 'test_utils_test_name')

    @unittest.skipIf(sys.version_info >= (3,), 'does not work on py3')
    def test_utils_block_read_filename_zero_size(self):
        local_path = get_local_path('..', 'data', 'two_lines.txt')
        self.assertTrue(os.path.exists(local_path))
        with self.assertRaises(IOError):
            utils.block_read_filename(local_path, lambda x: None, block_size=0)

    @unittest.skipIf(sys.version_info >= (3,), 'does not work on py3')
    def test_utils_block_read_filedesc_zero_size(self):
        with open(os.devnull, 'rb') as test_fd:
            with self.assertRaises(IOError):
                utils.block_read_filedesc(test_fd, lambda x: None, block_size=0)

    @unittest.skipIf(sys.version_info >= (3,), 'does not work on py3')
    def test_utils_block_read_filename(self):

        # FIXME: explain why this has to be a list
        status = [False]

        # Very simple callback (not really useful)
        def set_status(x):
            if x == '\n':
                status[0] = True

        # The ../data/one_length.bin file should only contain an empty line
        local_path = get_local_path('..', 'data', 'one_length.bin')
        self.assertTrue(os.path.exists(local_path))
        self.assertFalse(status[0])
        utils.block_read_filename(local_path, set_status)
        self.assertTrue(status[0])

        status[0] = False

        # This file contains multiple lines but eventually an empty one
        local_path = get_local_path('..', 'data', 'two_lines.txt')
        self.assertTrue(os.path.exists(local_path))
        self.assertFalse(status[0])
        # Must read file in one-char-sized blocks for set_status to work
        utils.block_read_filename(local_path, set_status, block_size=1)
        self.assertTrue(status[0])

    @unittest.skipIf(sys.version_info >= (3,), 'does not work on py3')
    def test_utils_block_read_filedesc(self):

        # FIXME: explain why this has to be a list
        called = [False]

        def set_status(_):
            called[0] = True

        # /dev/null is an empty file, no data, so callback must *not* be called
        with open(os.devnull, 'rb') as test_fd:
            utils.block_read_filedesc(test_fd, set_status)
        self.assertFalse(called[0])


class UtilsRunTest(unittest.TestCase):

    def test_utils_run_true(self):
        self.assertTrue(utils.run(['true'])[0])

    def test_utils_run_no_exe(self):
        self.assertFalse(utils.run(['n o t h i n g'])[0])

    def test_utils_run_false(self):
        self.assertFalse(utils.run(['false'])[0])

    def test_utils_run_wrong(self):
        good, retcode, out, err = utils.run(['ls', '--format'], out=True, err=True)
        self.assertFalse(good)
        self.assertFalse(retcode == 0)
        self.assertEqual('', out)
        self.assertEqual(err, "ls: option '--format' requires an argument\nTry 'ls --help' for more information.\n")

    def test_utils_run_wrong_not_quiet(self):
        good, retcode, out, err = utils.run(['ls', '--format'], out=True, err=True, quiet_out=False, quiet_err=False)
        self.assertFalse(good)
        self.assertFalse(retcode == 0)
        self.assertEqual(out, '')
        self.assertEqual(err, "ls: option '--format' requires an argument\nTry 'ls --help' for more information.\n")

    def test_utils_run_not_in_path(self):
        with utils.environ('PATH', ''):
            self.assertFalse(utils.run(['true'])[0])

    def test_utils_run_file(self):
        test_file = '/tmp/' + utils.test_name()
        if os.path.exists(test_file): # pragma: no cover
            os.remove(test_file)
        self.assertTrue(utils.run(['touch', test_file])[0])
        self.assertTrue(os.path.exists(test_file))
        self.assertTrue(utils.run(['rm', test_file])[0])
        self.assertFalse(os.path.exists(test_file))

    def test_utils_run_output_quiet_false(self):
        good, retcode, out, err = utils.run(['echo', '-n', 'TOTO'], out=True, quiet_out=False)
        self.assertTrue(good)
        self.assertTrue(retcode == 0)
        self.assertEqual(out, 'TOTO')
        self.assertIsNone(err)

    def test_utils_run_output_quiet_true(self):
        good, retcode, out, err = utils.run(['echo', '-n', 'TOTO'], out=True, quiet_out=True)
        self.assertTrue(good)
        self.assertTrue(retcode == 0)
        self.assertEqual(out, 'TOTO')
        self.assertIsNone(err)

    def test_utils_run_output(self):
        good, retcode, out, err = utils.run(['echo', '-n', 'TOTO'], out=True)
        self.assertTrue(good)
        self.assertTrue(retcode == 0)
        self.assertEqual(out, 'TOTO')
        self.assertIsNone(err)

class UtilsUUIDTest(unittest.TestCase):

    def test_utils_is_uuid(self):
        self.assertTrue(utils.is_uuid(uuid.uuid4()))
        self.assertTrue(utils.is_uuid(str(uuid.uuid4())))
        self.assertFalse(utils.is_uuid(None))
        self.assertFalse(utils.is_uuid(True))
        self.assertFalse(utils.is_uuid(False))
        self.assertFalse(utils.is_uuid(''))
        self.assertFalse(utils.is_uuid(u''))
        self.assertFalse(utils.is_uuid([]))
        self.assertFalse(utils.is_uuid({}))
        self.assertFalse(utils.is_uuid(set()))
        self.assertFalse(utils.is_uuid(frozenset()))

class UtilsStringioTest(unittest.TestCase):

    def test_utils_stringio_write(self):
        with utils.stringio() as out:
            out.write('TOTO')
            self.assertEqual('TOTO', out.getvalue())
        self.assertTrue(out.closed)

    def test_utils_stringio_read(self):
        with utils.stringio() as out:
            self.assertEqual('', out.getvalue())
            self.assertEqual('', out.read())
            out.write('TOTO')
            self.assertEqual('TOTO', out.getvalue())
            self.assertEqual('', out.read())
            out.seek(0)
            self.assertEqual('TOTO', out.getvalue())
            self.assertEqual('TOTO', out.read())
            out.seek(0, os.SEEK_END)
            out.write('TITI')
            self.assertEqual('TOTOTITI', out.getvalue())
            self.assertEqual('', out.read())
            out.seek(0)
            self.assertEqual('TOTOTITI', out.read())
            out.seek(0)
            out.write('TITI')
            self.assertEqual('TITITITI', out.getvalue())
            self.assertEqual('TITI', out.read())
            out.seek(0)
            self.assertEqual('TITITITI', out.read())
        self.assertTrue(out.closed)

    def test_utils_fileio_read(self):
        test_file = 'test.txt'
        utils.run(['touch', test_file])
        with utils.cleanup(['rm', test_file]):
            with open(test_file, 'w+b') as out:
                self.assertEqual('', out.read())
                out.write('TOTO')
                self.assertEqual('', out.read())
                out.seek(0)
                self.assertEqual('TOTO', out.read())
                out.seek(0, os.SEEK_END)
                out.write('TITI')
                self.assertEqual('', out.read())
                out.seek(0)
                self.assertEqual('TOTOTITI', out.read())
                out.seek(0)
                out.write('TITI')
                self.assertEqual('TITI', out.read())
                out.seek(0)
                self.assertEqual('TITITITI', out.read())
            self.assertTrue(out.closed)

class UtilsRedirectTest(unittest.TestCase):

    def test_utils_redirect_run(self):
        with utils.stringio() as output:
            with utils.redirect('stdout', output):
                utils.run(['echo', 'TOTO'], out=False)
                self.assertEqual('', output.getvalue())

    def test_utils_redirect_run_out(self):
        with utils.stringio() as output:
            with utils.redirect('stdout', output):
                utils.run(['echo', 'TOTO'], out=True)
                self.assertEqual('', output.getvalue())

    def test_utils_redirect_write(self):
        with utils.stringio() as output:
            with utils.redirect('stdout', output):
                sys.stdout.write('TOTO')
                self.assertEqual('TOTO', output.getvalue())

    def test_utils_redirect_print(self):
        with utils.stringio() as output:
            with utils.redirect('stdout', output):
                print('TOTOTITI')
                self.assertEqual('TOTOTITI\n', output.getvalue())
            self.assertEqual('TOTOTITI\n', output.getvalue())
        with self.assertRaises(ValueError):
            output.getvalue()

    def test_utils_redirect_close(self):
        tmp = None
        with utils.redirect('stdout'):
            print('toto')
            print('toto', file=sys.stdout)
            self.assertFalse(sys.stdout.closed)
            tmp = sys.stdout
        self.assertFalse(sys.stdout.closed)
        self.assertTrue(tmp.closed)

class UtilsDevnullTest(unittest.TestCase):

    @staticmethod
    def _cleanup_files():
        if os.path.exists('test_devnull_out.txt'):
            os.remove('test_devnull_out.txt')
        if os.path.exists('test_devnull_err.txt'):
            os.remove('test_devnull_err.txt')

    def _commit(self):
        self.out.flush()
        self.err.flush()
        os.fsync(self.out.fileno())
        os.fsync(self.err.fileno())

    def setUp(self):
        self._cleanup_files()
        self.out = open('test_devnull_out.txt', 'wb')
        self.err = open('test_devnull_err.txt', 'wb')
        self.old_out = sys.stdout
        self.old_err = sys.stderr
        sys.stdout = self.out
        sys.stderr = self.err

    def tearDown(self):
        sys.stdout = self.old_out
        sys.stderr = self.old_err
        self.out.close()
        self.err.close()
        self._cleanup_files()

    def test_utils_devnull_print(self):

        print('samarche')
        with utils.devnull('stdout'):
            print('sareum')
            print('sonreup', file=sys.stderr)
        print('samarchedenouveau')

        self._commit()

        self.assertEqual(open('test_devnull_err.txt', 'rb').read(), 'sonreup\n')
        self.assertEqual(open('test_devnull_out.txt', 'rb').read(), 'samarche\nsamarchedenouveau\n')

    def test_utils_devnull_print_explicit(self):

        print('samarche', file=sys.stdout)
        with utils.devnull('stdout'):
            print('sareum', file=sys.stdout)
            print('sonreup', file=sys.stderr)
        print('samarchedenouveau', file=sys.stdout)

        self._commit()

        self.assertEqual(open('test_devnull_err.txt', 'rb').read(), 'sonreup\n')
        self.assertEqual(open('test_devnull_out.txt', 'rb').read(), 'samarche\nsamarchedenouveau\n')

    def test_utils_devnull_write(self):

        sys.stdout.write('samarche')
        with utils.devnull('stdout'):
            sys.stdout.write('sareum')
            sys.stderr.write('sonreup')
        sys.stdout.write('samarchedenouveau')

        self._commit()

        self.assertEqual(open('test_devnull_err.txt', 'rb').read(), 'sonreup')
        self.assertEqual(open('test_devnull_out.txt', 'rb').read(), 'samarchesamarchedenouveau')

class UtilsEnvironTest(unittest.TestCase):

    def setUp(self):
        self._old_toto_was_here = False
        if 'TOTO' in os.environ:
            self._old_toto_was_here = True
            self._old_toto_val = os.environ['TOTO']
            del os.environ['TOTO']

    def tearDown(self):
        if self._old_toto_was_here:
            os.environ['TOTO'] = self._old_toto_val

    def test_utils_environ_not_existent_val(self):
        self.assertTrue('TOTO' not in os.environ) # Paranoid
        with utils.environ('TOTO', 'titi'):
            self.assertEqual('titi', os.environ['TOTO'])
        self.assertTrue('TOTO' not in os.environ)

    def test_utils_environ_not_existent_no_val(self):
        self.assertTrue('TOTO' not in os.environ) # Paranoid
        with utils.environ('TOTO'):
            # This is not redundant with the above or below identical lines
            self.assertTrue('TOTO' not in os.environ)
        self.assertTrue('TOTO' not in os.environ)

    def test_utils_environ_not_existent_empty_val(self):
        self.assertTrue('TOTO' not in os.environ) # Paranoid
        with utils.environ('TOTO', ''):
            self.assertEqual('', os.environ['TOTO'])
        self.assertTrue('TOTO' not in os.environ)

    def test_utils_environ_delete_implicit_nonexistent(self):
        self.assertTrue('TOTO' not in os.environ) # Paranoid
        with utils.environ('TOTO'):
            self.assertTrue('TOTO' not in os.environ)
        self.assertTrue('TOTO' not in os.environ)

    def test_utils_environ_delete_implicit(self):
        self.assertTrue('TOTO' not in os.environ) # Paranoid
        os.environ['TOTO'] = 'tutu'
        self.assertEqual('tutu', os.environ['TOTO'])
        with utils.environ('TOTO'):
            self.assertTrue('TOTO' not in os.environ)
        self.assertEqual('tutu', os.environ['TOTO'])

    def test_utils_environ_delete_explicit(self):
        self.assertTrue('TOTO' not in os.environ) # Paranoid
        with utils.environ('TOTO', None):
            # This is not redundant with the above or below identical lines
            self.assertTrue('TOTO' not in os.environ)
        self.assertTrue('TOTO' not in os.environ)

    def test_utils_environ_existent_val(self):
        self.assertTrue('TOTO' not in os.environ) # Paranoid
        os.environ['TOTO'] = 'tutu'
        self.assertEqual('tutu', os.environ['TOTO'])
        with utils.environ('TOTO', 'titi'):
            self.assertEqual('titi', os.environ['TOTO'])
        self.assertEqual('tutu', os.environ['TOTO'])

    def test_utils_environ_existent_empty_val(self):
        self.assertTrue('TOTO' not in os.environ) # Paranoid
        os.environ['TOTO'] = 'tutu'
        self.assertEqual('tutu', os.environ['TOTO'])
        with utils.environ('TOTO', ''):
            self.assertEqual('', os.environ['TOTO'])
        self.assertEqual('tutu', os.environ['TOTO'])

class UtilsCleanupTest(unittest.TestCase):

    def test_utils_cleanup(self):
        test_file = '/tmp/' + utils.test_name()
        self.assertFalse(os.path.exists(test_file))
        with utils.cleanup(['rm', test_file]):
            utils.run(['touch', test_file])
            self.assertTrue(os.path.exists(test_file))
        self.assertFalse(os.path.exists(test_file))

    def test_utils_clean(self):
        test_file = '/tmp/' + utils.test_name()
        self.assertFalse(os.path.exists(test_file))
        utils.run(['touch', test_file])
        self.assertTrue(os.path.exists(test_file))
        with utils.clean(['rm', test_file]):
            self.assertFalse(os.path.exists(test_file))
            utils.run(['touch', test_file])
            self.assertTrue(os.path.exists(test_file))
        self.assertFalse(os.path.exists(test_file))

# Incompatibility with pypy (at least the 2.2.1 version)
zde_msg = 'integer division or modulo by zero'
if 'pypy_version_info' in dir(sys): # pragma: no cover
    zde_msg = 'integer division by zero'
zde = ZeroDivisionError(zde_msg)
ae = ArithmeticError(zde_msg)

class ComparableExcTest(unittest.TestCase):

    def setUp(self):
        try:
            0 / 0
        except Exception as e:
            self.e = e

    def test_utils_cexc_simple_empties(self):

        # Empty iterables
        self.assertNotIn(self.e, [])
        self.assertNotIn(self.e, tuple())
        self.assertNotIn(self.e, set())
        self.assertNotIn(self.e, frozenset())
        self.assertNotIn(self.e, {})

        # containing itself
        self.assertIn(self.e, [self.e])
        self.assertIn(self.e, (self.e,))
        self.assertIn(self.e, set((self.e,)))
        self.assertIn(self.e, set([self.e]))
        self.assertIn(self.e, frozenset((self.e,)))
        self.assertIn(self.e, frozenset([self.e]))
        self.assertIn(self.e, {self.e: 1})
        self.assertNotIn(self.e, {1: self.e})

    def test_utils_cexc_compatible_excs(self):

        # Compatible Exceptions
        self.assertIn(self.e, utils.Exceptions(zde))
        self.assertNotIn(self.e, utils.Exceptions(ae))

        # Those two are equivalent
        self.assertIn(self.e, utils.Exceptions(zde, ae))
        self.assertIn(self.e, utils.Exceptions(
            ZeroDivisionError(zde_msg),
            ArithmeticError(zde_msg),
        ))

    def test_utils_cexc_sets(self):

        to_test_in = [(zde,), [zde], {zde}, (ae, zde), [ae, zde]]
        to_test_not_in = [(ae,), [ae], {ae}]

        for it in to_test_in:
            self.assertIn(self.e, utils.Exceptions(set(it)))
            self.assertIn(self.e, utils.Exceptions(frozenset(it)))

        for it in to_test_not_in:
            self.assertNotIn(self.e, utils.Exceptions(set(it)))
            self.assertNotIn(self.e, utils.Exceptions(frozenset(it)))

    def test_utils_cexc_hashes(self):

        to_test_in = [{zde: 1}, {ae: 1, zde: 2}, {zde: False, None: 0, True: 1, False: 0}]
        to_test_not_in = [{1: zde}, {1: zde, 2: ae}, {ae: False, None: 0, True: 1, False: 0}, {ae: 1}, {1: ae}]

        for it in to_test_in:
            self.assertIn(self.e, utils.Exceptions(it))

        for it in to_test_not_in:
            self.assertNotIn(self.e, utils.Exceptions(it))

class ExceptionsTest(unittest.TestCase):

    excs = (
        Exception,
        Exception(None),
        Exception(True),
        Exception(False),
        Exception(''),
        Exception('Yo'),
        NotImplementedError(),
        NotImplementedError(''),
        NotImplementedError('n i m b y'),
        ValueError('n i m b y'),
        ValueError('Yo'),

        # Containers: keep their content different, or they'll match each other
        Exception(dict()),
        Exception(tuple()),
        Exception(list()),
        Exception(set()),
        Exception(frozenset([None])),
        Exception({0: 2}),
        Exception(tuple([0])),
        Exception([0]),
        Exception(set([0])),
        Exception(frozenset([1])),
        Exception({2}),
        None,
    )

    def test_utils_loop(self):

        for exc in self.excs:
            try:
                if isinstance(exc, Exception):
                    # Should not raise e directly, make a copy
                    raise exc.__class__(*exc.args)
                elif type(exc) == type(Exception):
                    raise exc
                else:
                    self.assertTrue(exc is None)
            except Exception as e:
                self.assertFalse(e is exc)
                self.assertIn(e, utils.Exceptions(self.excs))
                a = list(self.excs)
                a.remove(exc)
                self.assertNotIn(e, utils.Exceptions(a))

class AlmostRawFormatterTest(unittest.TestCase):

    def test_split_lines(self):
        rf = utils.AlmostRawFormatter('prog_name')
        with self.assertRaises(ValueError):
            rf._split_lines('', 0)
        test_vals = (
            ('', [], []),
            ('toto', ['toto'], ['toto']),
            ('toto\ntiti', ['toto', 'titi'], ['toto', 'titi']),
            ('toto\ntiti\n', ['toto', 'titi'], ['toto', 'titi']),
            ('toto\n\ntiti\n', ['toto', 'titi'], ['toto', '', 'titi']),
            ('toto\n\n\ttiti\n', ['toto', 'titi'], ['toto', '', '\ttiti']),
        )
        for (test_val, expected, expected_pref) in test_vals:
            self.assertEqual(expected, rf._split_lines(test_val, 7))
            self.assertEqual(expected_pref, rf._split_lines(rf._PREFIX + test_val, 7))

class OutputTest(unittest.TestCase):

    def test_utils_output(self):
        import subprocess
        self.assertIsNone(utils.output(False, False))
        self.assertEqual(subprocess.PIPE, utils.output(True, False))
        self.assertEqual(subprocess.PIPE, utils.output(True, True))
        self.assertEqual(subprocess.DEVNULL, utils.output(False, True))

class AlphaNumSortTest(unittest.TestCase):

    def test_alphanum_sort(self):
        a = ['aze42rty', 'azerty', 'aze1rty', 'aze01rty', 'aze100rty', 'aze10rty', 'aze1.0rty', 'aze00rty', 'aze0rty']
        expected = ['azerty', 'aze0rty', 'aze00rty', 'aze1rty', 'aze01rty', 'aze1.0rty', 'aze10rty', 'aze42rty', 'aze100rty', ]
        alnum_sorted, bad = utils.alphanum_sort(a, 'aze', 'rty')
        self.assertEqual(expected, alnum_sorted)
        self.assertEqual(bad, [])

    def test_alphanum_sort_bad_elem(self):
        a = ['aze42rty', 'azerty', 'aze1rty', 'aze01rty', 'BADELEM1', 'aze100rty', 'aze10rty', 'aze1.0rty', 'BADELEM2', 'aze00rty', 'aze0rty']
        expected = ['azerty', 'aze0rty', 'aze00rty', 'aze1rty', 'aze01rty', 'aze1.0rty', 'aze10rty', 'aze42rty', 'aze100rty', ]
        alnum_sorted, bad = utils.alphanum_sort(a, 'aze', 'rty')
        self.assertEqual(expected, alnum_sorted)
        self.assertEqual(bad, ['BADELEM1', 'BADELEM2'])

class TRSTest(unittest.TestCase):

    def test_tr_s(self):
        self.assertEqual('', utils.tr_s(''))
        self.assertEqual('a', utils.tr_s('a'))
        self.assertEqual('a', utils.tr_s('aa'))
        self.assertEqual('a a', utils.tr_s('aa aa'))
        self.assertEqual('abababa', utils.tr_s('abababa'))
        self.assertEqual('a b c', utils.tr_s('aa bbb c'))
        self.assertEqual('a', utils.tr_s('a' * 4096))
        self.assertEqual('a', utils.tr_s('a' * 4097))

if __name__ == '__main__': # pragma: no cover
    import pytest
    pytest.main(['-x', '--pdb', __file__])
