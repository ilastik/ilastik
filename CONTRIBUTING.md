# Contributing

Thank you for considering contributing to ilastik, we really appreciate it.
The following text equips you with knowledge that makes contributing to ilastik easier.

## Overview

* [Setting up a development environment](#setting-up-a-development-environment)
  * [Fork the relevant repositories](#fork-the-relevant-repositories)
  * [Clone ilastik](#clone-ilastik)
  * [Add upstream repositories](#add-upstream-repositories-from-the-ilastik-organization)
  * [Install dependencies via conda](#installing-dependencies-via-conda)
* [Coding](#coding)
  * [Coding style](#coding-style)
  * [Tests](#tests)
  * [Pull requests](#pull-requests)

## Setting up a development environment

For all our repositories, we follow the GitHub Flow.
You can read about it in [this guide on github.com](https://guides.github.com/introduction/flow/).

Contributing to ilastik is a little bit more involved than just cloning the repo and committing.
The main ilastik repository holds a reference to the 5D slice viewer volumina as a submodule.
Furthermore, to be able to run the code, all dependencies have to be installed.
By far the most convenient way for this is to use conda.
The following paragraphs will guide through the process of setting up a working development environment.

### Fork the relevant repositories

You should begin by forking the main ilastik repositories, that make up the ilastik application:

* https://github.com/ilastik/ilastik
* https://github.com/ilastik/volumina (optional)

#### Clone ilastik

Having done that, continue by cloning your `ilastik` fork with:

```bash
# navigate to an appropriate folder, e.g. `~/sources`
git clone https://github.com/<your_github_username>/ilastik
```

initialize the volumina submodule with:

```bash
git submodule update --init --recursive
```

#### Add upstream repository from the ilastik organization

In order to stay up to date with the overall ilastik developments, you need to synchronize your
fork with the upstream repository.
In the current configuration, each of the two main repositories has a single _remote_, called _origin_,
pointing to your forks.

Now add the upstream repository by

```bash
# in ~/sources/ilastik
git remote add upstream https://github.com/ilastik/ilastik
```

# confirm successful addition of the remote
git remote -v
# with the output
origin  https://github.com/<your_githug_usernameur>/ilastik (fetch)
origin  https://github.com/<your_githug_usernameur>/ilastik (push)
upstream    https://github.com/ilastik/ilastik (fetch)
upstream    https://github.com/ilastik/ilastik (push)
```

You can sync your fork with the mother repo by:

```bash
# in ~/sources/ilastik
git checkout master  # make sure you are on the master branch
git fetch upstream master  # get the latest changes from the mother repo
git rebase upstream/master  # rebase your master branch with the mother repo
git push origin master  # push the updated master to your fork
git submodule update --recursive  # make sure volumina is up-to-date, too
```

We recommend making it a habit to stay current with the upstream repository while actively developing.
To make this task a bit easier you could add the following alias to your `.gitconfig` file:

```
[alias]
    sync-fork = !git checkout master && git fetch upstream master && git rebase upstream/master && git push && git submodule update --recursive && git checkout -'"
```

If you invoke this alias from the `ilastik` repository, it will update ilastik and make sure `volumina` is at the right commit, too:

```bash
# in ~/sources/ilastik
git sync-fork
```

#### (Optional) Setup volumina in development mode

Volumina is separated well from ilastik (but not entirely), so some changes to ilastik might involve changing `volumina` as well.
If you need to change parts of `volumina`, we suggest the following workflow:

* rename the ilastik fork to upstream, in order to have a consistent remote naming everywhere
  ```bash
  # navigate to the volumina submodule folder, e.g. ~/sources/ilastik/volumina
  git remote rename origin upstream
  ```
* add your own fork of `volumina` as a remote in the submodule
  ```bash
  # navigate to the volumina submodule folder, e.g. ~/sources/ilastik/volumina
  git remote add origin https://github.com/<your_github_username>/volumina
  git checkout master
  ```

From there you can start branching off, pushing to your `origin` repository and eventually starting a pull request with the upstream repository.

### Installing dependencies via conda

ilastik depends on ~120 packages - some of which pure python packages but also compiled C++ ones.
[Conda](https://conda.io/miniconda.html) allows for isolated python environments and for distribution of pre-build binary packages and a lot of
our dependencies are already built by the community around conda.
The remaining packages we maintain ourselves in our _ilastik-forge_ conda channel.

Install miniconda:

```bash
# Install miniconda to the prefix of your choice, e.g. /home/<myuser>/miniconda3

# LINUX:
wget https://repo.continuum.io/miniconda/Miniconda3-latest-Linux-x86_64.sh
bash Miniconda3-latest-Linux-x86_64.sh

# MAC:
wget https://repo.continuum.io/miniconda/Miniconda3-latest-MacOSX-x86_64.sh
bash Miniconda3-latest-MacOSX-x86_64.sh

# During the installation, conda edits your .bashrc to add its paths
# Either re-open the terminal, or
source ~/.bashrc  # Linux
source ~/.bash_profile  # MAC

# Install conda-build which is needed to correctly setup a development environment:
conda install -n base -c conda-forge conda-build
```

Now create the environment using the `devenv.py` script, starting it from the ilastik source folder:
```bash
# from your ilastik source folder, e.g. ~/sources/ilastik
conda activate base
python scripts/devenv.py create -n idev
```

Once you have created  the environment, make sure everything has worked by trying to import some of the ilastik core packages:

```bash
# activate your conda environment
conda activate idev

# check whether importing ilastik repos works
python -c "import ilastik; import lazyflow; import volumina; import vigra"
```

More information on conda, and building the ilastik packages yourself:
 * [miniconda](https://conda.io/miniconda.html)
 * [conda user guide](https://conda.io/docs/user-guide/index.html)
 * [conda build docs](https://conda.io/docs/commands/build/conda-build.html)
 * [On building ilastik packages with conda-build](https://github.com/ilastik/ilastik-publish-packages)

## Coding

In order to follow the [GitHub Flow](https://guides.github.com/introduction/flow/), please always start from a current master (see the above section on how to sync your forks) and create a feature branch that you will push to your own fork.

### Coding style

Many users with different backgrounds have contributed to ilastik in the past.
Code quality and coding styles can be quite different throughout the code-base.

In general, when working on an existing file, please try to deduce the used coding style from what you see there,
and adapt to it while working on this particular file.

For new files, we adhere to [the google python style guide](https://github.com/google/styleguide/blob/gh-pages/pyguide.md).

__Note__: please refrain from including changes by some automatic tools on existing code in your pull requests.
We would like to preserve the history there.
But please run those tools on the code you are contributing :)

### Tests

After making changes, please confirm that nothing else got broken by running the tests:

 * Changes made in the ilastik repository _ilastik_:
   ```bash
   # in ~/sources/ilastik/
   conda activate idev
   pytest --run-legacy-gui
   ```

 * Changes made in volumina:
   ```bash
   # in ~/sources/ilastik/volumina/
   conda activate idev
   pytest
   ```
   * please also run the ilastik tests (see above)


### Pull requests

In order to get your changes from the feature branch in your fork to the master branch of the upstream repository, you have to open a [pull request (PR)](https://help.github.com/articles/about-pull-requests/).
You can open PRs as early as you want if you want feedback on preliminary work.
In this case, please prefix the title with "[wip]" (for work in progress).
Please try to give the PR a meaningful title and summarize the changes made in your PR, explain the motivation and reference relevant issues that this PR addresses in the message.
At least one of the core developers will have a look and give you feedback.
