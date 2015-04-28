#!/usr/bin/env python
# coding: utf-8
# Copyright © 2015 Wieland Hoffmann
# License: MIT, see LICENSE for details
from argparse import Action


class TestAction(Action):
    def __call__(self, parser, namespace, values, option_string=None):
        if not namespace.unit:
            # Not only does this mean we error out on missing --unit arguments,
            # but also on --all-units because --unit conflicts with it
            parser.error("--test needs at least one --unit")
        else:
            setattr(namespace, self.dest, True)
