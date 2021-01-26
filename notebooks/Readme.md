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

We use _conda_ to develop Python and recommend it for scientific Python development.
It is assumed that you have already installed it and are familiar with using a Terminal.

In order to run the notebook type the following in a Terminal/Command Line:

```bash
$ conda env create -f environment.yml
# this will produce a lot of output

$ conda activate <created_environment_name>

# start the notebook server in the current folder
$ jupyter notebook --notebook-dir .

# to close the server hit `ctrl + c` in the terminal shut down the server by confirming with `y` 
```
