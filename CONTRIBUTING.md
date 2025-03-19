# Contributing Guidelines

Your contributions are always welcome! Feel free to open an issue or a pull
request. For breaking or other major changes, please open an issue first to
discuss what you would like to change. Despite this, please make sure to follow
the few guidelines below.

### Git pre-commit hooks

Note that some git hooks are required to pass before committing. This is
enforced by [pre-commit](https://pre-commit.com). Have a look at the
[`.pre-commit-config.yaml`](.pre-commit-config.yaml) file to see which hooks are
run. You can also run them manually with `uvx pre-commit run --all-files`.

To install the git hooks in your local development environment, run:

```bash
$ uvx pre-commit install
```

### Conventional Commits

For commit messages, please adhere to
[Conventional Commits](https://www.conventionalcommits.org/en/v1.0.0/) and add
verbose commit message bodies where necessary. Especially for breaking changes
or other major changes, please add a detailed description of the changes.

### Code Style (Linting and Formatting)

[Ruff](https://docs.astral.sh/ruff/) is used as a code linter and formatter.
This is enforced by a pre-commit hook and a github action. You can also run it
manually with `ruff`.

### Static Type Checking

Because this project's main dependency – [Scrapy](https://scrapy.org) – is
mostly untyped and custom type stubs or elaborated type checks were not added to
this project yet, use some kind of static type checker to ensure type safety
wherever possible. I recommend [Pyright](https://github.com/microsoft/pyright),
this is not enforced though. Also, always use type hints wherever possible!

### Release Workflow

After merging a pull request into the main branch, create a new release with a
detailed description as well as a tag. This tag ref will trigger a workflow to
build and publish the package to PyPi.

Do NOT forget to bump the verison number in the `pyproject.toml` file before!
