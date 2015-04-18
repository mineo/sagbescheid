#!/usr/bin/env python
# coding: utf-8
# Copyright © 2015 Wieland Hoffmann
# License: MIT, see LICENSE for details
from .state import State


def is_failure(state):
    return state == State.failed


def is_normal_start(old, new):
    return old in (State.activating, State.inactive) and new == State.active


def is_normal_stop(old, new):
    return old != State.failed and new == State.inactive


def is_ongoing_failure(old, new):
    return old == State.failed and new == State.failed


def is_recovery(old, new):
    return old == State.failed and new == State.active


def is_change_from_unknown(old, new):
    return old == State.unknown and (new == State.inactive or
                                     new == State.active or
                                     new == State.failed)
