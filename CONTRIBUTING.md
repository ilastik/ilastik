# Contributing

Thank you for considering contributing to ilastik, we really appreciate it.
The following text equips you with knowledge that makes contributing to ilastik easier.

## Overview

* [Setting up a development environment](#setting-up-a-development-environment)
  * [Fork the relevant repositories](#fork-the-relevant-repositories)
  * [Clone ilastik-meta](#clone-ilastik-meta)
  * [Initialize the source tree own forks](#initialize-the-source-tree-with-your-own-forks)
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
The three main repositories; ilastik, lazyflow, and volumina are governed by ilastik-meta as submodules.
Furthermore, in order to be able to run the code, all dependencies have to be installed.
By far the most convenient way for this is to use conda.
The following paragraphs will guide through the process of setting up a working development environment.

### Fork the relevant repositories

You should begin by forking the three main ilastik repositories, that make up the ilastik application:

* https://github.com/ilastik/ilastik
* https://github.com/ilastik/lazyflow
* https://github.com/ilastik/volumina

#### Clone ilastik-meta

Having done that, you should clone our `ilastik-meta` repository with:

```bash
# navigate to an appropriate folder, e.g. `~/sources`
git clone https://github.com/ilastik/ilastik-meta
```

#### Initialize the source tree with your own forks

Examining the created folder, e.g. `~/sources/ilastik-meta`, you can find the `.gitmodules` file.
Check out a new branch in ilastik-meta, e.g. `git checkout -b my-forks` and edit the `.gitmodules`
file such that it points to your own forks: replace all occurrences of `https://github.com/ilastik`
with `https://github.com/<your_githug_username>`.

Now it is time to initialize the repository:

```bash
# in ~/sources/ilastik-meta (or wherever you have cloned ilastik-meta to)
git submodule update --init --recursive
git submodule foreach "git checkout master"
```

Your forks are now set as the _origin_ remote for the respective repository.
You can confirm this, e.g. by

```bash
# in ~/sources/ilastik-meta/ilastik
git remote -v

# Which should give you an output like
origin  https://github.com/<your_github_username>/ilastik (fetch)
origin  https://github.com/<your_github_username>/ilastik (push)
```

#### Add upstream repositories from the ilastik organization

In order to stay up to date with the overall ilastik developments, you need to synchronize your
forks with the upstream repositories.
In the current configuration, each of the three main repositories has a single _remote_, called _origin_,
pointing to your forks.

Now add the upstream repository by

```bash
# in ~/sources/ilastik-meta/ilastik
git remote add upstream https://github.com/ilastik/ilastik

# confirm successful addition of the remote
git remote -v
# with the output
origin  https://github.com/<your_githug_usernameur>/ilastik (fetch)
origin  https://github.com/<your_githug_usernameur>/ilastik (push)
upstream    https://github.com/ilastik/ilastik (fetch)
upstream    https://github.com/ilastik/ilastik (push)
```

Do this for each of the remaining two repositories `lazyflow` and `volumina`,adding
`https://github.com/ilastik/lazyflow`, and `https://github.com/ilastik/volumina`, respectively, as
the _upstream_ remote.

You can sync your fork with the mother repo by:

```bash
# in ~/sources/ilastik-meta/ilastik
git checkout master  # make sure you are on the master branch
git fetch upstream master  # get the latest changes from the mother repo
git rebase upstream/master  # rebase your master branch with the mother repo
git push origin master  # push the updated master to your fork
git checkout -  # check out the branch you were previously on
```

You should make it a habit to stay current in all three repository whilst actively developing.
To make this task a bit easier you could add the following alias to your `.gitconfig` file:

```
[alias]
    sync-forks = "submodule foreach 'git checkout master; git fetch upstream master; git rebase upstream/master; git push; git checkout -'"
```

If you invoke this alias from the `ilastik-meta` repository, it will update all three forks:

```bash
# in ~/sources/ilastik-meta
git sync-forks
```

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
```

**Note:** the following steps guide you through the manual process of creating a development environment.
For convenience, there is a script that achieves the same effect located in `ilastik-meta/ilastik/scripts`.
You can create a development environment (given miniconda is installed) by invoking `./create-devenv.sh idev ../../` from within `ilastik-meta/ilastik/scripts`.

Create the ilastik development environment (we assume that the dev-environment will have the name _idev_, but you can, of course choose a name to your liking):
```bash
conda create --name idev -c ilastik-forge -c conda-forge ilastik-dependencies-no-solvers
```

In order to run your own code, you need to link against your sources

```bash
# Define some variables that make the following lines more portable
CONDA_ROOT=`conda info --root`
DEV_PREFIX=${CONDA_ROOT}/envs/idev

# first remote ilastik-meta from the conda environment
conda remove --name idev ilastik-meta

# now link against your own ilastik-meta repository
# navigate to the idev environment root in your conda-folder
cd ${DEV_PREFIX}
ln -s <your_ilastik-meta_source_folder>  # e.g. ~/sources/ilastik-meta

cat > ${DEV_PREFIX}/lib/python3.6/site-packages/ilastik-meta.pth << EOF
../../../ilastik-meta/lazyflow
../../../ilastik-meta/volumina
../../../ilastik-meta/ilastik
EOF
```

Now it might be the time to test whether the installation was successful:
```bash
# activate your conda environment
source activate idev

# check whether importing ilastik repos works
python -c "import ilastik; import lazyflow; import volumina"
```

If there are no errors here, chances are high the development environment was set up correctly.
If the above line already works, you can start ilastik by:

```bash
# in ~/source/ilastik-meta/ilastik
python ilastik.py
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
   # in ~/source/ilastik-meta/ilastik/tests
   source activate idev
   CONTINUE_ON_FAILURE=1 ./run_each_unit_test.sh
   ```
 * Changes made in lazyflow:
   ```bash
   # in ~/source/ilastik-meta/lazyflow
   source activate idev
   nosetests --where=./tests
   ```
   * please also run the ilastik tests (see above)
 * Changes made in volumina:
   ```bash
   # in ~/source/ilastik-meta/volumina/tests
   source activate idev
   ./run-each-until-fail.sh
   ```
   * please also run the ilastik tests (see above)


### Pull requests

In order to get your changes from the feature branch in your fork to the master branch of the upstream repository, you have to open a [pull request (PR)](https://help.github.com/articles/about-pull-requests/).
You can open PRs as early as you want if you want feedback on preliminary work.
In this case, please prefix the title with "[wip]" (for work in progress).
Please try to give the PR a meaningful title and summarize the changes made in your PR, explain the motivation and reference relevant issues that this PR addresses in the message.
At least one of the core developers will have a look and give you feedback.
