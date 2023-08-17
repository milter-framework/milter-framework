PWD := $(shell pwd)
MODULE_NAME = "milter_framework"
SRC_MODULE_DIR = $(PWD)/src/$(MODULE_NAME)
VERSION_FILE = $(PWD)/src/$(MODULE_NAME)/_version.py
BUILD_DIR = $(PWD)/dist

VERSION := $(shell cat "$(VERSION_FILE)" | cut -d "=" -f 2 | tr -d "'")

PROG := "$(MODULE_NAME)-$(VERSION)-py2.py3-none-any.whl"

.PHONY: all version build clean install

build:
#	python3 setup.py sdist bdist_wheel
	python3 -m pip install -r requirements.txt
	python3 -m pip wheel --no-build-isolation -w "$(BUILD_DIR)" --src "${SRC_MODULE_DIR}" .
	echo "$(PROG)" >> .build_artifacts

install:
	python3 -m pip uninstall -y "$(MODULE_NAME)"
	python3 -m pip install --force-reinstall --upgrade "$(BUILD_DIR)/$(PROG)"


