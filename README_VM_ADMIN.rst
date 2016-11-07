===================
Image manager tasks
===================

#. Get base image
=================

::

    wget http://download.cirros-cloud.net/0.3.4/cirros-0.3.4-x86_64-disk.img
    wget -O cirros-MD5SUMS http://download.cirros-cloud.net/0.3.4/MD5SUMS
    md5sum -c cirros-MD5SUMS 2>&1 | grep cirros-0.3.4-x86_64-disk.img     
    cirros-0.3.4-x86_64-disk.img: OK

#. Modify it
============

TODO

#. Check it for security
========================

TODO

#. Install StratusLab marketplace CLI tools
===========================================

Official documentation is here: [SLMPCLI]

You only have to this once, either:

* With pip:

::

    [sudo] pip install [--user] stratuslab-client

And change PATH to include the destination directory, which depends on your
usage of the ``--user`` parameter in the previous command.

* Or, use binaries:

::

    wget http://repo.stratuslab.eu:8081/content/repositories/fedora-14-releases/eu/stratuslab/pkgs/stratuslab-cli-user-zip/1.19/stratuslab-cli-user-zip-1.19-cli-user-bundle.tar.gz
    tar -C ${HOME}/bin/sl_cli xf stratuslab-cli-user-zip-1.19-cli-user-bundle.tar.gz
    export PATH=${PATH}:${HOME}/bin/sl_cli/bin
    export PYTHONPATH=${PYTHONPATH}:${HOME}/bin/sl_cli/lib/stratuslab/python

#. Create StratusLab metadata
=============================

Official documentation is here: [SLMP]

Create metadata
---------------

::

    stratus-build-metadata \
      --author='Your Endorser Name' \
      --os=cirros \
      --os-version=0.3.4 \
      --os-arch=x86_64 \
      --image-version=1.0 \
      --title='CirrOS v0.3.4 for x86_64' \
      --location=http://download.cirros-cloud.net/0.3.4/cirros-0.3.4-x86_64-disk.img \
      cirros-0.3.4-x86_64-disk.img

This will create an XML metadata skeleton file for this image, you'll have to
add some things into it.

Edit
----

::

    <dcterms:valid>2017-12-23T08:32:56Z</dcterms:valid>

    <dcterms:description>
        Cloud testing image:
        - minimal functionality
        - minimal size
        - minimal security (widely known password).

        Do not use for production !
    </dcterms:description>

You can also modify the ``<dcterms:valid>`` to extend the lifespan of the image,
but do not make it too long, as images that are not maintained properly should
expire.

Sign & endorse
--------------

Replace the XML metadata file name with the one output from the create step
above.

::

    stratus-sign-metadata \
        --p12-cert /path/to/your/certificate.p12 \
        --output cirros-0.3.4-x86_64-base-.sign.xml \
        cirros-0.3.4-x86_64-base-.xml
        Metadata file successfully signed: cirros-0.3.4-x86_64-base-.sign.xml

Validate
--------

::

    stratus-validate-metadata cirros-0.3.4-x86_64-base-.sign.xml 
    Valid: cirros-0.3.4-x86_64-base-.sign.xml

If the output is not like the one above you have to fix the XML metadata file
and validate it again.

Upload to StratusLab marketplace
--------------------------------

::

    stratus-upload-metadata \
        --marketplace-endpoint=https://marketplace.stratuslab.eu/marketplace/metadata \
        cirros-0.3.4-x86_64-base-.sign.xml

This will output the VMID you can use for the next step. Or you can search it on
the StratusLab marketplace web site.

#. Add to image list
====================

::

    echo 'VMID' >> /path/to/glance-manager/img_list.txt

#. Run glance-manager
=====================

If it has already been setup to run regularly by cron, just wait for the next
run time.

Or you can launch it manually, see README.rst

#. References
=============

[SLMP] http://www.stratuslab.eu/fp7/doku.php/tutorial:marketplace.html
[SLMPCLI] http://www.stratuslab.eu/fp7/doku.php/tutorial:installation.html
