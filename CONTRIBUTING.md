# Contributing

Thank you for considering contributing to ilastik, we really appreciate it.
The following text equips you with knowledge that makes contributing to ilastik easier.

---

* [Development Environment](#development-environment)
* [Workflow](#workflow)
* [Coding Style](#coding-style)

## Development Environment

1. Download and install [GitHub CLI][github-cli].

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

1. Download and install _the latest 64-bit_ [miniconda][miniconda].

1. Install [conda-build][conda-build] in order to access the [conda develop][conda-develop] command:

   ```
   conda install --name base conda-build
   ```

1. Create a new environment and install dependencies:

   ```
   conda deactivate
   conda env remove --name ilastik
   conda create --name ilastik --channel ilastik-forge --channel conda-forge ilastik-dependencies-no-solvers pre-commit
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

We use [GitHub Flow][github-flow] workflow without the _Deploy_ step.

The whole ilastik project is split into 2 repositories: [ilastik][ilastik] and [volumina][volumina].
Therefore, *for some changes you need to repeat the instructions twice in the corresponding directories*.

1. Make sure that your local and remote _master_ branches are synced with the upstream.

   ```
   git pull --ff-only upstream master:master
   git push origin master
   ```

1. Create a new branch from *master*:

   ```
   git switch --create your-branch-name-here master
   ```

1. Write some code, and, if possible, add tests for your changes.

1. Run the test suite *for all repositories*:

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

   - If you have changes in multiple repositories, create multiple pull requests, and then append the following paragraph to each one:

     ```
     See also: OTHER_PULL_REQUEST_URL_HERE
     ```

   - If your changes require feedback, create a draft pull request (select the type from the dropdown list on the green button).

1. Discuss your work with the other people, and wait for the approval from maintainers.

1. After your pull request has been merged, remove your local branches:

   ```
   git branch --delete your-branch-name-here
   ```

   You can also remove your remote branches by clicking "Delete branch" in the pull request web page, or running the following:

   ```
   git push --delete origin your-branch-name-here
   ```

## Coding style

Many users with different backgrounds have contributed to ilastik in the past.
Code quality and coding styles can be quite different throughout the code-base.

In general, when working on an existing file, please try to deduce the used coding style from what you see there,
and adapt to it while working on this particular file.

For new files, we adhere to the [Google Python style guide][google-style] and [black code style][black].

__Note__: please refrain from including changes by some automatic tools on existing code in your pull requests.
We would like to preserve the history there.
But please run those tools on the code you are contributing :)

[github-cli]: https://cli.github.com/
[miniconda]: https://docs.conda.io/en/latest/miniconda.html
[conda-build]: https://docs.conda.io/projects/conda-build/en/latest/
[conda-develop]: https://docs.conda.io/projects/conda-build/en/latest/resources/commands/conda-develop.html
[ilastik]: https://github.com/ilastik/ilastik
[volumina]: https://github.com/ilastik/volumina
[github-flow]: https://guides.github.com/introduction/flow/
[google-style]: https://github.com/google/styleguide/blob/gh-pages/pyguide.md
[black]: https://github.com/psf/black
