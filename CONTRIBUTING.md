# Contributing

Thank you for considering contributing to ilastik, we really appreciate it.
The following text equips you with knowledge that makes contributing to ilastik easier.

## Create a Development Environment

1. Download and install [GitHub CLI](https://cli.github.com/).

1. Fork and clone repositories:
    ```
    gh repo fork --clone=true --remote=true ilastik/volumina
    gh repo fork --clone=true --remote=true ilastik/ilastik
    ```

    If you already forked repositories before, just clone them:
    ```
    gh repo clone volumina
    gh repo clone ilastik
    ```

1. Download and install _the latest 64-bit_ [miniconda](https://docs.conda.io/en/latest/miniconda.html).

1. Install [mamba](https://github.com/mamba-org/mamba) and [conda-develop](https://docs.conda.io/projects/conda-build/en/latest/resources/commands/conda-develop.html):
    ```
    conda install --name base --channel conda-forge mamba
    mamba install --name base conda-develop
    ```

1. Create a new environment and install dependencies:
    ```
    conda deactivate
    conda env remove --name ilastik
    mamba create --name ilastik --channel ilastik-forge --channel conda-forge ilastik-dependencies-no-solvers pre-commit
    ```

1. Install repositories as packages in development mode:
    ```
    conda develop --name ilastik volumina
    conda develop --name ilastik ilastik
    ```

1. Install pre-commit hooks:
    ```
    conda activate ilastik

    cd volumina
    pre-commit install
    cd ..

    cd ilastik
    pre-commit install
    cd ..
    ```

1. Launch ilastik:
    ```
    conda activate ilastik
    cd ilastik
    python ilastik.py
    ```

## Workflow

We use [GitHub Flow](https://guides.github.com/introduction/flow/) workflow without the _Deploy_ step.

1. Sync your local and remote _master_ branches with the upstream.
    ```
    git -C volumina pull --ff-only upstream master:master
    git -C volumina push origin master:master

    git -C ilastik pull --ff-only upstream master:master
    git -C ilastik push origin master:master
    ```

1. Switch to new branches:
    ```
    git -C volumina checkout -b your-branch-name-here master
    git -C ilastik checkout -b your-branch-name-here master
    ```

1. Write some code, and, if possible, add tests for your changes.

1. Run the test suite:
    ```
    cd volumina
    pytest
    cd ..

    cd ilasitk
    pytest --run-legacy-gui
    cd ..
    ```

1. Commit the changes; see https://chris.beams.io/posts/git-commit/ on how to write a good commit message.

1. Create a pull request:
    ```
    gh pr create --web
    ```

    If your changes require feedback, create a draft pull request (select the PR type from the dropdown list on the green button).

1. Discuss your work with the other people, and wait for the approval from maintainers.

1. After your pull request has been merged, remove your local branches:
    ```
    git -C volumina branch --delete your-branch-name-here
    git -C ilastik branch --delete your-branch-name-here
    ```

    You can also remove your remote branches by clicking "Delete branch" in the pull request web page.

### Coding style

Many users with different backgrounds have contributed to ilastik in the past.
Code quality and coding styles can be quite different throughout the code-base.

In general, when working on an existing file, please try to deduce the used coding style from what you see there,
and adapt to it while working on this particular file.

For new files, we adhere to [the google python style guide](https://github.com/google/styleguide/blob/gh-pages/pyguide.md).

__Note__: please refrain from including changes by some automatic tools on existing code in your pull requests.
We would like to preserve the history there.
But please run those tools on the code you are contributing :)
