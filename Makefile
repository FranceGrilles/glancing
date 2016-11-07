CRUFT_HERE = .tox src/*.pyc test/src/*.pyc src/__pycache__ test/src/__pycache__ Glancing.egg-info

clean:
	rm -rf $(CRUFT_HERE) $(TEST_FILES)
	find . -type f -name .coverage -print0 | xargs -r -0 rm
	find . -type d -name cover -print0 | xargs -r -0 rm -rf

TEST_FILES = $(TEST_DATA_FILES) $(TEST_IMAGE_FILES) $(TEST_CHECKSUM_FILES) $(TEST_SL_MP_FILES)

test_files: test_data_files test_image_files test_checksum_files test_sl_mp_files

# For test parallelization
NPROC = grep -c ^processor /proc/cpuinfo

# FIXME: some tests are not parallelizable (test/src/test_decompressor.py)
pytests: test_files
	py.test
#	py.test -n `$(NPROC)`

tox: test_files
	tox

# Run all tests
nosetests test: test_files
	nosetests --exe ${NOSE_OPTS}

# Single-file test
test/src/%.py: test_files
	nosetests --exe ${NOSE_OPTS} $@

.PHONY: nosetests test tox pytests

# Download TEST_IMAGE_FILES
TEST_IMAGE_DIR = test/images
TEST_IMAGE_CHKSUMS = cirros-MD5SUMS cirros-SHA1SUMS coreos-MD5SUMS ttylinux-MD5SUMS
TEST_IMAGE_CIRROS = cirros-0.3.4-i386-disk.img cirros-0.3.4-x86_64-disk.img
TEST_IMAGE_FILE_NAMES = ttylinux-16.1-x86_64.img coreos_production_qemu_image.img \
	$(TEST_IMAGE_CIRROS) $(TEST_IMAGE_CHKSUMS)
TEST_IMAGE_FILES = $(foreach IMG,$(TEST_IMAGE_FILE_NAMES),$(TEST_IMAGE_DIR)/$(IMG))
TEST_IMAGE_CIRROS_FILES = $(foreach IMG,$(TEST_IMAGE_CIRROS),$(TEST_IMAGE_DIR)/$(IMG))

test_image_files: $(TEST_IMAGE_FILES)

test/images/ttylinux-16.1-x86_64.img:
	curl http://appliances.stratuslab.eu/images/base/ttylinux-16.1-x86_64-base/1.0/ttylinux-16.1-x86_64.img.gz | gzip -dc > $@

test/images/ttylinux-MD5SUMS: test/images/ttylinux-16.1-x86_64.img
	md5sum test/images/ttylinux-16.1-x86_64.img > $@

test/images/coreos_production_qemu_image.img:
	curl http://stable.release.core-os.net/amd64-usr/current/coreos_production_qemu_image.img.bz2 | bzip2 -dc > $@

test/images/coreos-MD5SUMS: test/images/coreos_production_qemu_image.img
	md5sum test/images/coreos_production_qemu_image.img > $@

test/images/cirros-0.3.4-i386-disk.img:
	curl http://download.cirros-cloud.net/0.3.4/cirros-0.3.4-i386-disk.img > $@

test/images/cirros-0.3.4-x86_64-disk.img:
	curl http://download.cirros-cloud.net/0.3.4/cirros-0.3.4-x86_64-disk.img > $@

test/images/cirros-MD5SUMS:
	curl http://download.cirros-cloud.net/0.3.4/MD5SUMS > $@

test/images/cirros-SHA1SUMS: $(TEST_IMAGE_CIRROS_FILES)
	sha1sum $(TEST_IMAGE_CIRROS_FILES) > $@

# Download SL marketplace test files

SL_MARKETPLACE_URL_BASE = https://marketplace.stratuslab.eu/marketplace/metadata

VMID_LIST = Buh-tYElvOEvst1HDyTq_6v-1si\
	PIDt94ySjKEHKKvWrYijsZtclxU \
	JcqGhHxmTRAEpHMmRF-xhSTM3TO

TEST_SL_MP_FILES_XML = $(foreach vmid,$(VMID_LIST),test/stratuslab/$(vmid).xml)
TEST_SL_MP_FILES_JSON = $(foreach vmid,$(VMID_LIST),test/stratuslab/$(vmid).json)
TEST_SL_MP_FILES = $(TEST_SL_MP_FILES_XML) $(TEST_SL_MP_FILES_JSON)

test_sl_mp_files: $(TEST_SL_MP_FILES)

test/stratuslab/%.xml:
	wget -O $@ $(SL_MARKETPLACE_URL_BASE)/$*?media=xml

test/stratuslab/%.json: test/stratuslab/%.xml
	EMAIL=$$(grep '<email>' $< | sed -e 's/.*<email>\(.*\)<\/email>.*/\1/') ; \
	DATE=$$(grep '<email>' $< | sed -e 's/.*<created xmlns="http:\/\/purl.org\/dc\/terms\/">\(.*\)<\/created>.*/\1/') ; \
	wget -O $@ $(SL_MARKETPLACE_URL_BASE)/$*/$$EMAIL/$$DATE?media=json

# Create TEST_DATA_FILES, sizes are in MB (Bigger ones: 100 200 300 400 500 750 1000)
SIZES = 1 5 10 25 50 75
TEST_DATA_FILES_SIZE = $(foreach SIZ,$(SIZES),test/data/random_$(SIZ)M.bin)
TEST_DATA_FILES_COMP = $(foreach ALG,gz bz2 zip,test/data/random_1M_$(ALG).bin.$(ALG)) test/data/random_2files_zip.bin.zip
TEST_DATA_FILES_TINY = test/data/zero_length.bin test/data/one_length.bin test/data/two_lines.txt
TEST_DATA_FILES = $(TEST_DATA_FILES_SIZE) $(TEST_DATA_FILES_COMP) $(TEST_DATA_FILES_TINY) $(TEST_DATA_FILES_SIZE)

test_data_files: $(TEST_DATA_FILES)

test/data/zero_length.bin:
	touch $@

test/data/one_length.bin:
	echo > $@

test/data/two_lines.txt:
	echo '# First line' > $@
	echo >> $@

test/data/random_%M.bin:
	dd if=/dev/urandom of="$@" bs=1M count=$*

test/data/random_1M_gz.bin.gz: test/data/random_1M.bin
	gzip -c < $< > $@

test/data/random_1M_bz2.bin.bz2: test/data/random_1M.bin
	bzip2 -c < $< > $@

test/data/random_1M_zip.bin.zip: test/data/random_1M.bin
	zip - $^ > $@

# Include a second file (ignored when decompressing) for more corner-case test coverage
test/data/random_2files_zip.bin.zip: test/data/random_1M.bin test/data/zero_length.bin
	zip - $^ > $@

# Helper macros : convert string to upper- & lower-case
toupper = $(shell echo "$(1)" | tr -s '[:lower:]' '[:upper:]')
tolower = $(shell echo "$(1)" | tr -s '[:upper:]' '[:lower:]')

# Checksum test files
CHECKSUM_ALGOS = md5 sha1 sha224 sha256 sha384 sha512
CHECKSUM_FILES_MH = $(foreach ALG,$(CHECKSUM_ALGOS),test/data/$(call toupper,$(ALG))SUMS)
CHECKSUM_FILES_SYS = $(foreach CHKSUM_FILE,$(CHECKSUM_FILES_MH),$(CHKSUM_FILE).txt)

TEST_CHECKSUM_FILES = $(CHECKSUM_FILES_MH) $(CHECKSUM_FILES_SYS)

test_checksum_files: $(TEST_CHECKSUM_FILES)

test/data/%SUMS.txt: $(TEST_DATA_FILES)
	$(call tolower,$*)sum $(TEST_DATA_FILES) > $@

test/data/%SUMS: $(TEST_DATA_FILES)
	src/multihash.py -d test/data -f $(TEST_DATA_FILES)

# Check validity against system utilities generated files...
test_data_check: test_checksum_files
	for sum in test/data/*SUMS; do cmp $${sum} $${sum}.txt || exit 42; done

# Nose testing & plugins

PACKAGES = "glancing,glance,glance_manager,multihash,metadata,decompressor,openstack_out,utils,tutils,test_glancing,test_multihash,test_metadata,test_decompressor,test_utils,test_tutils,test_glance,test_openstack_out,test_glance_manager"

COVERAGE_OPTS = --with-coverage --cover-branches --cover-html --cover-inclusive --cover-tests --cover-package=$(PACKAGES)
PROFILE_OPTS = # --with-profile

# Tissue plugin : check code for pep8 compliance
# pip install --user tissue
# I disagree with those errors
TISSUE_IGNORES = --tissue-ignore=E302,E501,E261,E201,E202,E241,E402,E128
TISSUE_OPTS = # --with-tissue --cover-inclusive --tissue-package=${PACKAGES} ${TISSUE_IGNORES}

NOSE_OPTS = $(COVERAGE_OPTS) $(PROFILE_OPTS) $(TISSUE_OPTS)
