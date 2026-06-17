.. _plugin_system:

=============
Plugin System
=============

ilastik uses Python entry points to manage plugins.
The functionality is implemented in ``ilastik.plugins``.

-------------
Using plugins
-------------

From the ilastik GUI:
--------------------

All installed plugins are available via the respective GUIs:

* in Object Classification via the Feature Selection step,
* in Tracking when exporting data and configuring the Plugin Export Source.

From code:
----------

Simply import the ilastik plugin manager::

    from ilastik.plugins import plugin_manager

You can get all plugin types for object features, and tracking export plugins::

    plugin_manager.get_object_feature_plugins()

or

    plugin_manager.get_tracking_export_plugins()


The ``ilastik/plugins_default`` directory contains the
official plugins that are distributed with ilastik.
These are listed as entrypoints in ``pyproject.toml``.


----------------
Writing a plugin
----------------

We have a cookiecutter for writing your own plugins.

* object features: `our object feature plugin cookiecutter <https://github.com/ilastik/ilastik-oc-feats-cookiecutter>`_
* tracking export: please get in touch if you are interested in developing tracking export plugins.
