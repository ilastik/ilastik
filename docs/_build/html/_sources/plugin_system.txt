.. _plugin_system:

=============
Plugin System
=============

ilastik uses Yapsy (http://yapsy.sourceforge.net/) to manage plugins.
The functionality is implemented in ``ilastik/plugins.py``.

-------------
Using plugins
-------------

Simply import the ilastik plugin manager, which is an instance of
``yapsy.PluginManager``::

    from ilastik.plugins import pluginManager

Now you can do things like list all plugins::

    pluginManager.getAllPlugins()

Or only get plugins of a particular category, such as object feature
plugins::

    pluginManager.getPluginsOfCategory('ObjectFeatures')

For all the capabilities of the plugin manager class, see the Yapsy
documentation: `PluginManager
<http://yapsy.sourceforge.net/PluginManager.HTML>`_.

ilastik must be able to find available plugins. The ``.ilastikrc``
configuration file should contain a line listing all directories to be
searched recursively::

    plugin_directories: ~/.ilastik/plugins,

In addition, the ``plugins_default`` directory, which contains the
official plugins that are distributed with ilastik, is also searched.


-------------------------
Writing a plugin category
-------------------------

Any subclass of ``Yapsy.IPlugin`` may be a plugin category. Remember
to add it to the plugin manager with
``pluginManager.setCategoriesFilter()`` in ``ilastik/plugins.py``. For
more information see the Yapsy documentation: `Make it your own
<http://yapsy.sourceforge.net/#make-it-your-own.>`_.

----------------
Writing a plugin
----------------

See the Yapsy documentation: `Plugin description policy
<http://yapsy.sourceforge.net/PluginManager.html#plugin-description-policy>`_.
