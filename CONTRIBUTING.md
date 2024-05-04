# Contributing Guidelines

Your contributions are always welcome! Feel free to open an issue or a pull request. For breaking or other major changes, please open an issue first to discuss what you would like to change. Despite this, please make sure to follow the few guidelines below. Basically just adhere to good software engineering practices and some project-specific requirements listed below.

### Git pre-commit hooks

Note that some git hooks are required to pass before committing. This is enforced by [pre-commit](https://pre-commit.com). Have a look at the [`.pre-commit-config.yaml`](.pre-commit-config.yaml) file to see which hooks are run. You can also run them manually with `pre-commit run --all-files`.

### Conventional Commits

For commit messages, please adhere to [Conventional Commits](https://www.conventionalcommits.org/en/v1.0.0/) and add verbose commit message bodies where necessary.

### Code Style (Linting and Formatting)

[Ruff](https://docs.astral.sh/ruff/) is used as a code linter and formatter. This is enforced by a pre-commit hook and a github action. You can also run it manually with `ruff`.

### Static Type Checking

Because this project's main dependency – [Scrapy](https://scrapy.org) – is mostly untyped and custom type stubs or elaborated type checks were not added to this project yet, use some kind of static type checker to ensure type safety wherever possible. I recommend [Pyright](https://github.com/microsoft/pyright), this is not enforced though. Also, always use type hints wherever possible!
