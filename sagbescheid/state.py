#!/usr/bin/env python
# coding: utf-8
# Copyright © 2015 Wieland Hoffmann
# License: MIT, see LICENSE for details
import enum


class State(enum.Enum):
    active = 1
    reloading = 2
    inactive = 3
    failed = 4
    activating = 5
    deactivating = 6
    unknown = 7
