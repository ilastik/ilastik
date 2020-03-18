#!/bin/bash

##
## Build the docs and push them to the gh-pages branch so github displays them.
## Notes:
##   - The new gh-pages branch is pushed to 'origin'
##   - The old gh-pages branch is DELETED.
##   - Files .nojeykll and circle.yml are automatically added to the gh-pages branch.
##   - The work is done in a temporary clone of this repo (in /tmp), to avoid
##     accidentally messing up your working directory.

BUILD_DIR=_build # See 'grep BUILDDIR docs/Makefile'

set -e

repo_dir=$(git rev-parse --show-toplevel)

# Build the docs in the user's repo
cd "${repo_dir}"/docs
PYTHONPATH=$repo_dir make html

# Record the current commit, so we can log it in the gh-pages commit message
curr_commit=$(git rev-parse HEAD)

# Read the url of the user's 'origin' remote
origin_details=$(git remote -v | grep "^origin\s")
origin_url=$(echo ${origin_details} | python -c "import sys; print sys.stdin.read().split(' ')[1]") 

REPONAME=$(basename $(git rev-parse --show-toplevel))
TEMP_REPO=/tmp/${REPONAME}

# Clone a copy into /tmp/
rm -rf ${TEMP_REPO}
git clone --depth=1 "file://${repo_dir}" ${TEMP_REPO}

# Completely erase the old gh-pages branch and start it from scratch
cd ${TEMP_REPO}
git branch -D gh-pages || true
git checkout --orphan gh-pages
git reset --hard

# Copy the doc output
cp -r "${repo_dir}"/docs/${BUILD_DIR}/html/* .

# Github's 'jekyll' builder can't handle directories with underscores,
# but we don't need jekyll anyway. Disable it.
touch .nojekyll

# Copy circle.yml so that circle-ci knows not to build this branch.
cp -r ${repo_dir}/circle.yml .

# Commit everything to gh-pages
git add .
git commit -m "Docs built from ${curr_commit}"

# Push to github
git remote add remote-origin ${origin_url}
git push -f remote-origin gh-pages
