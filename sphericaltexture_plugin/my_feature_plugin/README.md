# my_feature_plugin

A short description on what kind of features the plugin computes.


## TODOs:

- [ ] Add dependencies to `environment.yaml` and `pyproject.toml`
- [ ] Development setup
  - [ ] create conda environment
  - [ ] install package in editable mode
- [ ] test initial plugin setup


## Development setup

### 1. Install dependencies

Add your dependencies to `environment.yaml` file (including all dependencies needed during development).
It is pre-populated with the ilastik dependencies, so you can test/develop with ilastik.

```bash
conda env create -n idev-plugin --file environment.yaml
conda activate idev-plugin
```

### 2. Install your plugin in editable mode

In order to develop your plugin you'll have to install it in editable mode:
Add the dependencies also to `pyproject.toml`.

```
# make sure your environment is activated
pip install --no-deps -e .
```

this makes the plugin available to ilastik via its entrypoint (see [`pyproject.toml`][pyproject]) in case you want to modify it.

### 3. Test development setup

#### Check ilastik "sees" your plugin

```bash
# make sure idev-plugin is active
ilastik
```

The ilastik UI should start up.

You can download and open the following a [sample project][ocex] or [create your own][ocdocs].
Open the project, when clicking on _Select Features_, the **my_feature_plugin** plugin should show up.
Per default the feature _"example_global_feature"_, and "example_local_feature" is implemented.

## Writing your object feature plugin

The `my_feature_plugin` folder holds a template that you can use to implement your feature plugin.
The file `the_module.py` and `the_module.yapsy-plugin` are the only files that you will need to edit.

* `the_module.yapsy-plugin`: this holds the metadata that is used by the plugin manager that is used in ilastik `yapsy`.
* `the_module.py`: The class `MyObjectFeatures` is the template class that you need to edit in order to add your feature.
  These methods have to be implemented: `availableFeatures` and either (or both) `compute_global`, and/or `compute_local`.
  _`compute_global`_ assumes that the computation is done on the whole image at once.
  _`compute_local`_ assumes that the computation will happen per object.


To help with development your source folder already contains a `test` folder.
The contained tests don't test if the computation of your features is correct (you can add such tests yourself).
But these tests make sure that the output of your computations is _valid_ for ilastik.

## Deployment

__How to get your package to other ilastik users.__

There are two options

1. Copy the files to the plugin directory of on the user system (default location is `TODO`).
   This is particularly applicable if you don't need any extra dependencies in addition to the ones that are included in ilastik.
2. Install via conda.
   This repository comes with a conda recipe that can be build using `conda build -c conda-forge -c ilastik-forge conda-recipe`
   This is especially applicable if you need additional dependencies that are not included in the ilastik distribution.


[ocdocs]: https://www.ilastik.org/documentation/objects/objects
[ocex]: https://data.ilastik.org/object_classification_example.zip
[pyproject]: ./pyproject.toml
