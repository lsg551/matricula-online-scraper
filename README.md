# Matricula Online Scraper

![PyPI - Python Version](https://img.shields.io/pypi/pyversions/matricula-online-scraper?logo=python)
![GitHub License](https://img.shields.io/github/license/lsg551/matricula-online-scraper?logo=pypi)
![PyPI - Version](https://img.shields.io/pypi/v/matricula-online-scraper?logo=pypi)
[![Publish to PyPi](https://github.com/lsg551/matricula-online-scraper/actions/workflows/publish.yml/badge.svg)](https://github.com/lsg551/matricula-online-scraper/actions/workflows/publish.yml)


[Matricula Online](https://data.matricula-online.eu/) is a website that hosts
digitized parish registers from various regions across Europe. This CLI-based tool allows
you to directly download data from it.

## Installation

Make sure to meet the minimum required version of Python. You can install
this tool via `pip`:

```console
$ pip install -u matricula-online-scraper
```

<details><summary>Build from source</summary>
<p>

If you want to get the latest version or just build from source, you can clone the repository and install it manually,
favorably via [`uv`](https://docs.astral.sh/uv/):

```console
$ git clone git@github.com:lsg551/matricula-online-scraper.git && cd matricula-online-scraper
$ uv venv && uv sync
```

Alternatively, you can always fallback to `pip`:

```console
$ pip install -r requirements.txt
```

</p>
</details>


## Usage

You can use this tool to scrape the three primary entities from Matricula:
1. [Scanned parish registers (→ images of baptism, marriage, and death records)](#1-example-download-a-scanned-parish-register-all-images-of-a-book)
2. [A list of all available parishes (→ location metadata)](#2-example-download-a-huge-list-of-all-available-parishes-on-matricula)
3. [A list for each parish with metadata about its registers, including dates ranges, type etc.](#3-example-download-a-list-about-the-registers-of-a-single-parish)

Most users likely want to scrape the scanned parish registers (1).
The additional metadata (2,3) can be useful for other purposes such as automation,
filtering or searching.

Note that this tool will not format or clean the data in any way. Instead, the
data is saved as-is to a file. Some data might be poorly formatted or inconsistent.

Run the following command to see the available commands and options:

```console
$ matricula-online-scraper --help
```

### (1) Example: Download a scanned parish register (all images of a book)

Imagine you opened a certain parish register on Matricula and want to download the entire book or a single page.
Let's say you want to download the death register of [Bautzen, Germany](https://data.matricula-online.eu/en/deutschland/dresden/bautzen/),
starting from 1661. Copy the URL of the register when you are in the image viewer, this might look like `https://data.matricula-online.eu/en/deutschland/dresden/bautzen/11/?pg=1`.

Then run the following command and paste the URL into the prompt:

```console
$ matricula-online-scraper parish fetch https://data.matricula-online.eu/en/deutschland/dresden/bautzen/11/?pg=1
```

Run `matricula-online-scraper parish fetch --help` to see all available options.

### (2) Example: Download a huge list of all available parishes on Matricula

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


> [!TIP]
> The data only changes rarely. A GitHub workflow automatically executes this command once a week
> and pushes to [`cache/parishes`](https://github.com/lsg551/matricula-online-scraper/tree/cache/parishes).
> This has the advantage that you can download the data without having to run and waiting for the command yourself
> as well as taking some load off the Matricula servers.
>
> Click here to download the entire CSV: 👉 [`parishes.csv`](https://github.com/lsg551/matricula-online-scraper/raw/cache/parishes/parishes.csv.gz) 👈
>
> Or with cURL:
> ```console
> curl -L https://github.com/lsg551/matricula-online-scraper/raw/cache/parishes/parishes.csv.gz | gunzip > parishes.csv
> ```
>
> [![Cache Parishes](https://github.com/lsg551/matricula-online-scraper/actions/workflows/cache-parishes.yml/badge.svg)](https://github.com/lsg551/matricula-online-scraper/actions/workflows/cache-parishes.yml)
> ![GitHub last commit (branch)](https://img.shields.io/github/last-commit/lsg551/matricula-online-scraper/cache%2Fparishes?path=parishes.csv.gz&label=last%20caching&cacheSeconds=43200)


Run `matricula-online-scraper parish list --help` to see all available options.

### (3) Example: Download a list about the registers of a single parish

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

### Example: Combine with other commands and 3rd party tools to download all registers within a certain region.

The following command will download the cached list with all parishes, filter all parishes within the region "Paderborn", and pipe the parish URLs to `matricula-online-scraper parish show` to get the metadata about the registers for each parish. Then, `matricula-online-scraper parish fetch` will be called for all registers of each parish and proceeds to download the images of the registers.

```console
curl -sL https://github.com/lsg551/matricula-online-scraper/raw/cache/parishes/parishes.csv.gz | gunzip | csvgrep -c region -m "Paderborn" | csvcut -c url | csvformat --skip-header | xargs -n 1 -P 4 matricula-online-scraper parish show -o - | jq -r ".url // empty" | matricula-online-scraper parish fetch
```

It uses [`csvkit`](https://csvkit.readthedocs.io/en/latest/index.html) for processing the CSV data. Make sure to install it via `pip install csvkit` or your package manager if you want to replicate this example. Also make sure to have [`jq`](https://stedolan.github.io/jq/) installed, as it is used to parse and manipulate the JSON output of some commands.


## License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file
for details.

You can read more about Matricula Online's terms of use and data licenses
[on their page](https://data.matricula-online.eu/en/nutzungsbedingungen/) or
check out their `robots.txt` file at
[data.matricula-online.eu/robots.txt](https://data.matricula-online.eu/robots.txt)
regarding restrictions of the use of automated tools (as of March 2025, they
have none).
