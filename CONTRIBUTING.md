# Contributing

Thank you for considering contributing to ilastik, we really appreciate it.
The following text equips you with knowledge that makes contributing to ilastik easier.

---

* [Development Environment](#development-environment)
* [Workflow](#workflow)
* [Coding Style](#coding-style)

## Development Environment

1. Download and install [Git][git], [GitHub CLI][github-cli], and _the latest 64-bit_ [Mambaforge][mambaforge].
   - Windows: all following commands should be executed in the _Anaconda Prompt_ from the Start Menu.
   - Linux: Git might be already preinstalled, GitHub CLI might be available in your system package manager.
   - macOS: Git is already preinstalled, GitHub CLI is available in [Homebrew][homebrew].

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

1. If you have an existing [Miniconda][miniconda] installation, you can use it for ilastik development, but install [Mamba][mamba] and configure conda to use [strict channel priority][strict-channel-priority]:

   ```
   conda config --set channel_priority strict
   conda install --name base -c conda-forge mamba
   ```

1. Create a new environment and install dependencies:

   ```
   # from within the ilastik folder
   mamba deactivate
   mamba env remove --name ilastik
   mamba env create --name ilastik --file dev/environment-dev.yml
   ```

1. Install repositories as packages in development mode:

   ```
   conda activate ilastik
   # from the folder containing ilastik and volumina
   pip install -e ilastik
   pip install -e volumina
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
   mamba activate ilastik
   cd ilastik
   python ilastik_scripts/ilastik_startup.py
   ```

## Workflow

We use [GitHub Flow][github-flow] workflow without the _Deploy_ step.

The whole ilastik project is split into 2 repositories: [ilastik][ilastik] and [volumina][volumina].
Therefore, *for some changes you need to repeat the instructions twice in the corresponding directories*.

1. Make sure that your local and remote _main_ branches are synced with the upstream.

   ```
   git pull --ff-only upstream main:main
   git push origin main
   ```

1. Create a new branch from *main*:

   ```
   git switch --create your-branch-name-here main
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
     Related: OTHER_PULL_REQUEST_URL_HERE
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

[git]: https://git-scm.com/
[github-cli]: https://cli.github.com/
[miniconda]: https://docs.conda.io/en/latest/miniconda.html
[mambaforge]: https://github.com/conda-forge/miniforge#mambaforge
[homebrew]: https://brew.sh/
[conda-build]: https://docs.conda.io/projects/conda-build/en/latest/
[conda-develop]: https://docs.conda.io/projects/conda-build/en/latest/resources/commands/conda-develop.html
[mamba]: https://mamba.readthedocs.io/en/latest/
[ilastik]: https://github.com/ilastik/ilastik
[volumina]: https://github.com/ilastik/volumina
[github-flow]: https://guides.github.com/introduction/flow/
[google-style]: https://github.com/google/styleguide/blob/gh-pages/pyguide.md
[black]: https://black.readthedocs.io/en/stable/
[strict-channel-priority]: https://conda.io/projects/conda/en/latest/user-guide/tasks/manage-channels.html#strict-channel-priority


## Further notes

* The file `.git-blame-ignore-revs` holds some commits that were generated automatically and only affected code style. These commits can be ignored in `git-blame`:

  ```bash
  git blame --ignore-revs-file .git-blame-ignore-revs <some-file>

  ```
  This setting can also be made permanent for your local repo:

  ```bash
  git config blame.ignoreRevsFile .git-blame-ignore-revs
  ```
