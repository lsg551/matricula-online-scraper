# Matricula Online Scraper

![PyPI - Python Version](https://img.shields.io/pypi/pyversions/matricula-online-scraper?logo=python)
![GitHub License](https://img.shields.io/github/license/lsg551/matricula-online-scraper?logo=pypi)
![PyPI - Version](https://img.shields.io/pypi/v/matricula-online-scraper?logo=pypi)

> :warning: This tool is still under development and is NOT yet feature-complete. Expect breaking changes and bugs. Please report any issues.

[Matricula Online](https://data.matricula-online.eu/) is a website that hosts parish registers from various regions across Europe. This CLI tool allows you to fetch data from it and save the data to a file.

Note that this tool will not format or clean the data in any way. Instead, the data is saved as-is to a file. I mention this because the original data is especially poorly formatted and contains a lot of inconsistencies. It is up to the user to process the data further.

## 🔧 Installation

Make sure to have a recent version of Python installed. You can then install this script via `pip`:

```console
$ pip install --user matricula-online-scraper
```

Nevertheless, you can clone this repository and run the script with [Poetry](https://python-poetry.org).

## 💡 How To Use

```console
$ matricula-online-scraper --help
```

prints available commands and options, including documentation. Same goes for each subcommand, e.g. `matricula-online-scraper fetch --help`.

The `fetch` command is the primary command to fetch any resources from Matricula Online. Its subcommands allow you to scrape different resources, run `matricula-online-scraper fetch --help` to see available subcommands.

### Example 1:

Fetch all available locations and save them to a `.jsonl` file:

```console
$ matricula-online-scraper fetch locations ./output.jsonl
```

This will create a file called `output.jsonl` in your current directory with all available

### Example 2:

## License & Contributing

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

Contributions are welcome! Feel free to open an issue or submit a pull request if you have suggestions, especially bug fixes.
