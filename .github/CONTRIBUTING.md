# Contributing
We'd love your help! We want to make contributing to this project as easy and transparent as possible, whether it's:

- Reporting a bug
- Discussing the current state of the code
- Submitting a fix
- Proposing/add new features (like support for a new events source!)

## What to Contribute?!
There's a table of event sources that we need to scrape events data from [here](https://github.com/DataKind-DC/capital-nature-ingest/blob/master/event_sources.md). Use the `Orgs to track (DK Volunteer Assignments)` tab of the sheet.

Each row contains an events source. If there isn't an `owner` in the first column, then we could use your help scraping events from that source! Just be sure to claim that source by adding your name to that column in the sheet.

To learn about how to structure your code and where to add it in the project directory, go [here](https://github.com/DataKind-DC/capital-nature-ingest/blob/master/lambdas/README.md).

To learn about how to use git to make your contributions, read on!

## We Use [Github Flow](https://guides.github.com/introduction/flow/index.html), So All Code Changes Happen Through Pull Requests
Pull requests are the best way to propose changes to the codebase. We use a **Fork and Pull Model**.

## The Fork and Pull Model
### Short Version
Before you start to work on something, fork this repo, clone the repository, and then make a new branch for your feature.

As you implement changes, commit them to your local branch, ideally following our [style guide](https://github.com/DataKind-DC/capital-nature-ingest/blob/master/.github/STYLE-GUIDE.md). When you're ready, push that branch to GitHub and then make a pull request. Then await review and, if necessary, push some more changes.

### Long Version
#### Writing your Code

1. Fork the repository

Go to the project's [homepage](https://github.com/DataKind-DC/capital-nature-ingest) and hit the `Fork` button. This creates a copy of the repository in your GitHub account.

2. `clone` the repository

Now you want to clone the forked repo to your machine.

```bash
git clone https://github.com/your-user-name/capital-nature-ingest.git capital-nature-ingest-yourname
cd capital-nature-ingest-yourname
git remote add upstream https://github.com/DataKind-DC/capital-nature-ingest
```

This creates the directory *capital-nature-ingest-yourname* and connects your repository to the upstream (main project) repository.

3. `checkout` a branch for your feature before doing anything

You want your master branch to reflect only production-ready code, so create a feature branch for making your changes. For example:

```bash
git checkout -b shiny-new-feature
```

This changes your working directory to the shiny-new-feature branch. Keep any changes in this branch specific to one bug/feature so it is clear what the branch brings to capital-nature-ingest.

When creating this branch, make sure your master branch is up to date with the latest upstream master version. To update your local master branch, you can do:

```bash
git checkout master
git pull upstream master --ff-only
```

4. Do some work, see the changes, and stage files you've edited

Once you’ve made changes, you can see them by typing:
```bash
git status
```

If you have created a new file, it is not being tracked by git. Add it by typing:

```bash
git add path/to/file-to-be-added.py
```

Doing ‘git status’ again should give something like:

```bash
# On branch shiny-new-feature
#
#       modified:   /relative/path/to/file-you-added.py
#
```

5. `commit` your changes to your local branch

Once you've added files, you're ready to commit your changes to your local repository with an explanatory message. Use the `-m` flag if you don't want to include a full commit body. See the [style guide](https://github.com/DataKind-DC/capital-nature-ingest/blob/master/.github/STYLE-GUIDE.md) for details on how to format your commit messags.

```bash
git commit -m "ENH: add scraper for awesome new source (#123)"
```

6. When you want your changes to appear publicly on your GitHub page, push your forked feature-branch’s commits

```bash
git push origin shiny-new-feature
```

Above, *origin* is the default name given to your remote repository on GitHub. This will create a shiny-new-feature branch in your origin repository, ie. your repository on GitHub.

You can see the remote repositories:

```bash
git remote -v
```

If you added the upstream repository as described above you will see something like:

```bash
origin  git@github.com:yourname/capital-nature-ingest.git (fetch)
origin  git@github.com:yourname/capital-nature-ingest.git (push)
upstream        git://github.com/capital-nature-ingest.git (fetch)
upstream        git://github.com/capital-nature-ingest.git (push)
```

Once you've pushed your code, your code is on GitHub, but it is not yet a part of the main project. For that to happen, a pull request needs to be submitted on GitHub.
 
#### Reviewing your Code and Submitting a Pull Request
When you’re ready to ask for a code review, file a pull request.

A pull request is how code from a local repository becomes available to the GitHub community and can be looked at and eventually merged into the master version. 

To submit a pull request:

1. Navigate to your repository on GitHub
2. Click on the Pull Request button
3. You can then click on Commits and Files Changed to make sure everything looks okay one last time
4. Write a description of your changes in the Preview Discussion tab
5. Click Send Pull Request.

This request then goes to the repository maintainers, and they will review the code.

#### Updating a Pull Request
Sometimes, you'll need to update your pull request.

If there's a gray bar saying "This pull request cannot be automatically merged.", then you've got some updates to make. That's because the file(s) that your pull request modifies was/were updated in the meantime. To avoid a conflict on the remote, GitHub won't let you automatically merge into master. This means you need to update your Pull Request by merging the upstream's master branch into your feature branch. In short, you need to “merge upstream master” in your branch:

```bash
git checkout shiny-new-feature
git fetch origin
git merge origin/master
```

If there are no conflicts (or if they could be fixed automatically), a file with a default commit message will open, and you can simply save and quit this file.

If there are merge conflicts, you'll need to solve those conflicts. See [this](https://help.github.com/articles/resolving-a-merge-conflict-using-the-command-line/) for an explanation on how to do this. Once the conflicts are fixed and merged and the files where the conflicts were solved are added, you can run `git commit` to save those fixes.

>If you have uncommitted changes at the moment you want to update the branch with master, you will need to stash them prior to updating (see the [stash docs](https://git-scm.com/book/en/v2/Git-Tools-Stashing-and-Cleaning)). This will effectively store your changes and they can be reapplied after updating.

After your feature branch has been updated locally, you can now update your pull request by pushing to the branch on GitHub:
```bash
git push origin shiny-new-feature
```

#### Deleting your Branch (optional)
Once your pull request is accepted, you’ll probably want to get rid of the feature branch. You can do that to the remote master right within the pull request page. To delete the branch locally, you need to first pull the remote master down into your local master. Then git will know it's safe to delete your branch.

```bash
git checkout master
git fetch origin
git merge origin
```

Now that your local master is even with the remote, you can do:

```bash
git branch -d shiny-new-feature
```

> Make sure you use a lower-case -d, or else git won’t warn you if your feature branch has not actually been merged.

## Reporting bugs or making feature requests
We use GitHub issues to track bugs and make feature requests. [Open a new issue](https://github.com/DataKind-DC/capital-nature-ingest/issues) if you've got an idea. An issue template will autopopulate. Feel free to use only those sections of the issue template that you think are relevant.

**Great Bug Reports** tend to have:

- A quick summary and/or background
- Steps to reproduce
  - Be specific!
  - Give sample code if you can. 
- What you expected would happen
- What actually happens
- Notes (possibly including why you think this might be happening, or stuff you tried that didn't work)

People *love* thorough bug reports. I'm not even kidding.

## License
TBD
