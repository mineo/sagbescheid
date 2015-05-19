Usage
=====

systemd
-------

Sagbescheid ships with a systemd unit to start it. By default, it logs all
events for all units on standard output, which is not really useful. To modify
the behaviour, simply edit the :ref:`options <cli>` in
``/etc/conf.d/sagbescheid``.

.. _cli:

Command line options
--------------------

.. autoprogram:: sagbescheid.sagbescheid:build_arg_parser()
   :prog: sagbescheid
