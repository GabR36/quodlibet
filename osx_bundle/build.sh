#!/bin/bash

source env.sh

jhbuild bootstrap
jhbuild build python
jhbuild build meta-gtk-osx-bootstrap
jhbuild build quodlibet
