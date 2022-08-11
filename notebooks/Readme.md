## Notebook Examples

In this folder you can find [jupyter notebook](https://jupyter.org/) examples to illustrate how to automate certain aspects of, and around ilastik from Python.

The structure in each folder will follow the same scheme:

```tree
notebooks/
├── subfolder  # for a certain task
│   ├── task.ipynb  # Notebook illustrating how to perform the task
│   └── environment.yml  # conda environment definition needed to run the notebook
├── ...
```

We use _mamba/(conda)_ for Python-based projects and recommend it for scientific Python development.
It is assumed that you have already installed _mamba_ and are familiar with using a Terminal.

In order to run the notebook type the following in a Terminal/Command Line:

Note: mamba has to be configured with [_strict channel priority_](https://conda.io/projects/conda/en/latest/user-guide/tasks/manage-channels.html#strict-channel-priority) in order to produce consistent environments.


```bash
# make sure to use strict channel priority - this setting is global but in general a good idea
mamba config --set channel_priority strict

# create n environment - make sure to choose an appropriate <environment_name>
$ mamba env create -n <environment_name> -f environment.yml
# this will produce a lot of output

$ mamba activate <environment_name>

# start the notebook server in the current folder
$ jupyter notebook --notebook-dir .

# to close the server hit `ctrl + c` in the terminal shut down the server by confirming with `y` 
```
