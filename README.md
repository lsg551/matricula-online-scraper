# Matricula Online Scraper

![PyPI - Python Version](https://img.shields.io/pypi/pyversions/matricula-online-scraper?logo=python)
![GitHub License](https://img.shields.io/github/license/lsg551/matricula-online-scraper?logo=pypi)
![PyPI - Version](https://img.shields.io/pypi/v/matricula-online-scraper?logo=pypi)
[![Publish to PyPi](https://github.com/lsg551/matricula-online-scraper/actions/workflows/publish.yml/badge.svg)](https://github.com/lsg551/matricula-online-scraper/actions/workflows/publish.yml)


[Matricula Online](https://data.matricula-online.eu/) is a non-profit initiative that digitizes parish records in Central Europe and hosts them for free on their website. `matricula-online-scraper` is a command-line interface (CLI) tool that enables you to download data directly from it.

This includes the scanned parish registers (scanned books about baptism, marriage, death records etc.) as well as metadata about the parishes and their registers. Data can be downloaded in CSV or JSON, images are generally provided as PNG files.

## Installation

Make sure to meet the minimum required version of Python. You can install
this tool via `pip`:

```console
$ pip install -u matricula-online-scraper
```

<details><summary>Or build from source</summary>
<p>

If you want to get the latest version or just build from source, you can clone the repository and install it manually,
favorably via [`uv`](https://docs.astral.sh/uv/):

```console
$ git clone https://github.com/lsg551/matricula-online-scraper.git
$ cd matricula-online-scraper
$ uv venv && uv sync
```

If you do not have `uv` installed, you can install it via `pip`:

```console
$ pip install -r requirements.txt
```

</p>
</details>

## Usage

Once installed, you can can append the `--help` flag to any command to see its usage and options.

```
$ matricula-online-scraper --help

 Usage: matricula-online-scraper [OPTIONS] COMMAND [ARGS]...                         
                                                                                                    
 Command Line Interface (CLI) for scraping Matricula Online https://data.matricula-online.eu.       
                                                                                                    
 You can use this tool to scrape the three primary entities from Matricula:                         
 1. Scanned parish registers (→ images of baptism, marriage, and death records)                     
 2. A list of all available parishes (→ location metadata)                                          
 3. A list for each parish with metadata about its registers, including dates ranges, type etc.     
                                                                                                    
╭─ Options ────────────────────────────────────────────────────────────────────────────────────────╮
│ --verbose,--debug     -v        Enable verbose logging (DEBUG).                                  │
│ --quiet               -q        Suppress all output (CRITICAL).                                  │
│ --version                       Show the CLI's version.                                          │
│ --install-completion            Install completion for the current shell.                        │
│ --show-completion               Show completion for the current shell, to copy it or customize   │
│                                 the installation.                                                │
│ --help                          Show this message and exit.                                      │
╰──────────────────────────────────────────────────────────────────────────────────────────────────╯
╭─ Commands ───────────────────────────────────────────────────────────────────────────────────────╮
│ parish     Scrape parish registers (1), a list with all available parishes (2) or a list of the  │
│            available registers in a parish (3).                                                  │
│ newsfeed   Scrape Matricula Online's Newsfeed.                                                   │
╰──────────────────────────────────────────────────────────────────────────────────────────────────╯
                                                                                                    
 Attach the --help flag to any subcommand for further help and to see its options. Press CTRL+C to  
 exit at any time.
 See https://github.com/lsg551/matricula-online-scraper for more information.
```


## Examples

<details><summary><b>(1) Download a scanned parish register (i.e. images)</b></summary>
<p>

Imagine you opened a certain parish register on Matricula and want to download the entire book or a single page.
Let's say you want to download the death register of [Bautzen, Germany](https://data.matricula-online.eu/en/deutschland/dresden/bautzen/),
starting from 1661. Copy the URL of the register when you are in the image viewer, this might look like `https://data.matricula-online.eu/en/deutschland/dresden/bautzen/11/?pg=1`.

Then run the following command and paste the URL into the prompt:

```console
$ matricula-online-scraper parish fetch https://data.matricula-online.eu/en/deutschland/dresden/bautzen/11/?pg=1
```

Run `matricula-online-scraper parish fetch --help` to see all available options.

</p>
</details>

<details><summary><b>(2) List all available parishes on Matricula</b></summary>
<p>

```console
$ matricula-online-scraper parish list
```

This command will fetch all parishes from Matricula Online, effectively scraping the entire ["Fonds" page](https://data.matricula-online.eu/en/bestande/).
The resulting data looks like:

```csv
country    , region                          , name                 , url                                                                          , longitude         , latitude
Deutschland, "Passau, rk. Bistum"            , Arbing-bei-Neuoetting, https://data.matricula-online.eu/en/deutschland/passau/arbing-bei-neuoetting/, 12.7081934381511  , 48.32953342002908
Österreich , Oberösterreich: Rk. Diözese Linz, Eberschwang          , https://data.matricula-online.eu/en/oesterreich/oberoesterreich/eberschwang/ , 13.5620985        , 48.15550995
Polen      , "Breslau/Wroclaw, Staatsarchiv" , Hermsdorf            , https://data.matricula-online.eu/en/polen/breslau/hermsdorf/                 , 15.642741683666767, 50.84699257482722
```

It may take a few minutes to complete and will yield a few thousand rows. Each `url` value leads to the main page of the parish
and can bepiped into the next command (3) to fetch metadata about the parish's registers.

Run `matricula-online-scraper parish list --help` to see all available options.

---

[![Cache Parishes](https://github.com/lsg551/matricula-online-scraper/actions/workflows/cache-parishes.yml/badge.svg)](https://github.com/lsg551/matricula-online-scraper/actions/workflows/cache-parishes.yml)
![GitHub last commit (branch)](https://img.shields.io/github/last-commit/lsg551/matricula-online-scraper/cache%2Fparishes?path=parishes.csv.gz&label=last%20caching&cacheSeconds=43200)

<b>NOTE</b>: The data only changes rarely. A GitHub workflow automatically executes this command once a week
and pushes to [`cache/parishes`](https://github.com/lsg551/matricula-online-scraper/tree/cache/parishes).
This has the advantage that you can download the data without having to run and waiting for the command yourself
as well as taking some load off the Matricula servers.

Click here to download the entire CSV: 👉 [`parishes.csv`](https://github.com/lsg551/matricula-online-scraper/raw/cache/parishes/parishes.csv.gz) 👈

Or with cURL:
```console
curl -L https://github.com/lsg551/matricula-online-scraper/raw/cache/parishes/parishes.csv.gz | gunzip > parishes.csv
```

</p>
</details>

<details><summary><b>(3) List all registers available in a specific parish</b></summary>
<p>

This command will download a list of all available registers for a single parish, including certain metadata such as
the type of register, the date range, and the URL to the register itself etc.

```console
$ matricula-online-scraper parish show https://data.matricula-online.eu/en/deutschland/muenster/muenster-st-martini/
```

A sample from the output (here _JSON Lines_) looks like this:

```json
{
    "name": "Taufen",
    "url": "https://data.matricula-online.eu/en/deutschland/muenster/muenster-st-martini/KB001/",
    "accession_number": "KB001",
    "date": "1715 - 1800",
    "register_type": "Taufen",
    "date_range_start": "Jan. 1, 1715",
    "date_range_end": "Dec. 31, 1800"
}
```

Run `matricula-online-scraper parish show --help` to see all available options.

</p>
</details>

<details><summary><b>(4) Combine and chain these commands to download all registers within a certain region.</b></summary>
<p>

The three examples above only highlight a single command for different data types each. However, this data is not unconnected and can be linked together. The CLI is designed with this in mind, so you can easily combine commands, pipe data around, and chain them together to achieve more complex tasks.

For example, after you have obtained a complete list of all parishes (2), you can filter that list to only include parishes within a certain region, such as "Paderborn" in Germany, and then pipe these parish URLs from that list into the next command to download a list for each parish with metadata about its registers (3). Finally, you can pipe the URLs of the registers into the next command to download the images of the registers (1).

The following command will download the cached list with all parishes (2) (faster than `matricula-online-scraper parish list`), filter all parishes within the region "Paderborn", and pipe the parish URLs to `matricula-online-scraper parish show` to get the metadata about the registers for each parish (3). Then, `matricula-online-scraper parish fetch` will be called for all registers of each parish and proceeds to download the images of the registers (1).

<!-- TODO: `xargs` in `xargs -n 1 -P 4 matricula-online-scraper parish show -o -` is no longer needed, because `parish show` soon allows lists to be piped to STDIN  -->

```console
curl -sL https://github.com/lsg551/matricula-online-scraper/raw/cache/parishes/parishes.csv.gz \
    | gunzip \
    | csvgrep -c region -m "Paderborn" \
    | csvcut -c url \
    | csvformat --skip-header \
    | xargs -n 1 -P 4 matricula-online-scraper parish show -o - \
    | jq -r ".url // empty" \
    | matricula-online-scraper parish fetch
```

It uses [`csvkit`](https://csvkit.readthedocs.io/en/latest/index.html) for processing the CSV data. Make sure to install it via `pip install csvkit` or your package manager of choice if you want to replicate this example. Also make sure to have [`jq`](https://stedolan.github.io/jq/) installed, as it is used to parse and manipulate the JSON output of some commands.

</p>
</details>

These examples are obviously not exhaustive, but they should give you an idea of how to use the CLI tool and how to combine commands to achieve more complex tasks. With the data from Matricula Online, `matricula-online-scraper` and 3rd party tools like `csvkit` and `jq`, you could build geolocation searches form the coordinates provided for each parish, filter the parishes within a certain data range and region, narrow down the registers to a specific type (e.g. only baptism records), regularly backup your most important parish registers, and so on.




## License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file
for details.

You can read more about Matricula Online's terms of use and data licenses
[on their page](https://data.matricula-online.eu/en/nutzungsbedingungen/) or
check out their `robots.txt` file at
[data.matricula-online.eu/robots.txt](https://data.matricula-online.eu/robots.txt)
regarding restrictions of the use of automated tools (as of March 2025, they
have none).
