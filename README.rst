#. What is this
===============

Those are a few helper scripts to ease importing VM images into an
OpenStack glance service. It can handle various kinds of VM image
source metadata, as well as work directly with local files or URIs.

#. Features
===========

- Import images from: local file, download from an URL, use an image JSON
  metadata file from the StratusLab marketplace, or directly download the
  metadata from a given ID for that marketplace.

- Check image with multiple message digest algorithms to ensure no
  tampering with them has happened.

- Backup previous versions of an image when importing the new version

#. How to run glance_manager.py
===============================

The tool is self documented:

::

    glance_manager.py --help

It should be used with an OpenStack account that has sufficient privileges to be
able to upload images into the glance registry. There's no need for a full
OpenStack administrator account. See the `_environmentVars` section below
to setup the needed environment variables.

As this tool uses the `glance` and eventually `keystone` OpenStack command line
clients, they should be located somewhere accessible from the PATH environment
variable.

You have to create the image list file, with each line containing an image ID
from the StratusLab marketplace (https://marketplace.stratuslab.eu/marketplace)

For example, the "FG_Cloud" project image selection (`stack` unix user account):

::

    cat > /home/stack/glancing/img_list.txt << EOF
    #  Temporary list of images to download
    # FG_Cloud-Ubuntu-14.04-x86_64
    LHfKVPoHcv4oMirHU0KuOQc-TvI
    # FG_Cloud-Ubuntu-12.04-x86_64
    IU_CzEdDeCe5Vbs11ZODPAgox8n
    # FG-Cloud Official Ubuntu 12.04 Cloud Image
    IzEOzeHK8-zpgSyAkhNiZujL4nZ
    # FG_Cloud-CentOS-6-x86_64
    JXlXluzZXUYG8ugkYUX5lPPcO9E
    EOF

Then you use it like so:

::

    glance_manager.py --verbose --vmlist /path/to/img_list.txt

The default value for the market place base url option (--url) should be OK, no
need to use that except for testing purpose.

If the previous run, like above worked OK, you can automate the tool running a
few times a day to keep the images up-to-date. You can use cron to do so.

For example, using the `stack` unix user account, running at 4h intervals,
verbosely logging to a local file:

::

    cat > /etc/cron.d/glance_manager.cron << EOF
    SHELL=/bin/bash
    PATH=/sbin:/bin:/usr/sbin:/usr/bin
    MAILTO=root
    PYTHONPATH=/home/stack/glancing/src
    0 */4 * * * stack ( date --iso-8601=seconds ; source /home/stack/glancing/fg-cloud-openrc.sh ; /home/stack/glancing/src/glance_manager.py -v -l /home/stack/glancing/img_list.txt ) >> /home/stack/glancing/img_list.log 

This is assuming the OpenStack `_environmentVars` are exported from the script
file : ``/home/stack/glancing/fg-cloud-openrc.sh``.

#. How to run glancing.py
=========================

The following is assuming your environment contains the appropriate variables &
values for connecting to a glance service, see the `_environmentVars` section
below.

- Import local image file, without checksum verification:

::

    ./src/glancing.py /tmp/cirros-0.3.4-i386-disk.img

- Download image from URL, check given MD5 message digest

::

    ./src/glancing.py http://download.cirros-cloud.net/0.3.4/cirros-0.3.4-i386-disk.img -s 79b4436412283bb63c2cba4ac796bcd9

- Download XML metadata from StatusLab marketplace, get the URL from this
  metadata, then get the image from the URL, and verify all the checksums
  that are available in the metadata.

  This one is for a CentOS v7 image...

::

    ./src/glancing.py KqU_1EZFVGCDEhX9Kos9ckOaNjB

- You have browsed the StratusLab marketplace, and found the right image
  for your project, downloaded its JSON metadata locally, then want to
  get the corresponding VM image:

::

    $ ./src/glancing.py /tmp/KqU_1EZFVGCDEhX9Kos9ckOaNjB.json

You can use the "-d" or "--dry-run" CLI parameter to only download the VM
image file, verify the checksum(s) but not do the final import into glance
registry.

::

    ./src/glancing.py -d /tmp/cirros-0.3.4-i386-disk.img -s 79b4436412283bb63c2cba4ac796bcd9

#. Get Help
===========

The ./src/glancing.py script CLI options are documented in-line, please
run it like the following to see the help:

::

    ./src/glancing.py --help

#. Automated Testing
====================

Be extra careful, automated tests are intended for developpers only, not for
site administrators. The tests can have bugs, so never run the test suite in a
production tenant, as it could destroy image(s) there (and also valuable
snapshots). This actually happened once, you have been warned.

Both ``nose`` & ``py.test`` can be used to run the test suite

You'll need to install the ``python-nose`` package first (should work on debian &
redhat based distributions), ``pytest`` (redhat) or ``python-pytest`` (debian) in
order to launch the test suite.

In order to launch all the automated tests, just use the following command,
which use ``nose`` to collect the tests to run:

::

    make test

or just use:

::

    py.test

Or you can select only a single test to be run manually:

::

    nosetests test/src/test_utils.py:UtilsRunTest.test_utils_run_true

First you give the test module test_XXX.py file, a colon, then the test class,
a dot, then the test method from that class.

The py.test way of doing manual test selection:

::

    py.test test/src/test_utils.py::UtilsRunTest::test_utils_run_true

Or you can use make to run a single test file with code coverage 

::

    make test test/src/test_utils.py

The tests check for reachability of a glance registry service to test
images uploading. Just populate the traditionnal OpenStack variables,
see environmentVars_.

You can further extend the coverage of the test suite, by modifying the
following lines from ./test/src/test_glancing.py file. They enable more
tests, but will download a lot of big (huge, 100s of MBs or even GBs) image
files...

::

    _HEAVY_TESTS = False
    _HUGE_TESTS = False

In the Makefile you can also configure the usage of nose test plugins
for code coverage, pep8 conformance checking and profiling.

Display code coverage results will be located, after a test run, in:

::

    firefox ./cover/index.html

#. Environment variables
========================
.. _environmentVars:

You can set those to configure access to your local OpenStack Glance VM
image registry sevice:

    export OS_TENANT_NAME=
    export OS_USERNAME=
    export OS_PASSWORD=
    export OS_AUTH_URL=
    export OS_REGION_NAME=
    export OS_CACERT="/path/to/CACERT.pem"
    export OS_TENANT_ID=

OS_TENANT_ID is used by glance_manager.py, but is not mandatory. If given, it
avoids using keystone to get from OS_TENANT_NAME to OS_TENANT_ID.
