# Green and Gold: Australia at the Olympics

A one-page data story about Australia's Olympic performance, from Athens 1896 to Paris 2024 and Milano Cortina 2026.

- **Author:** Abdullah Salem
- **Unit:** FIT3179 Data Visualisation, Monash University, Semester 2 2026 (Data Visualisation 2, topic #8)
- **Live page:** https://abdullahsalem220.github.io/fit3179-dv2-olympics/
- **Charts:** [Vega-Lite](https://vega.github.io/vega-lite/) and [Vega](https://vega.github.io/vega/). Each chart's specification is its own file in [`specs/`](specs/).

## Repository layout

| Path | Contents |
|---|---|
| `index.html` | The page: story sections, narrative text and chart containers |
| `css/style.css` | Layout, typography and colour |
| `js/main.js` | Loads each chart from `specs/` with vega-embed |
| `specs/` | One indented JSON specification per chart |
| `data/` | Trimmed data used by the charts (about 270 KB in total) |
| `data/geo/` | TopoJSON map outlines |
| `data/lookups/` | Hand-made lookups and match logs, kept visible for checking |
| `data/coverage.json` | How many records each chart covers and why others are left out |
| `scripts/` | Python scripts that rebuild `data/` from the raw sources |
| `sketch/` | The hand-drawn sketch (PDF) |

## Data sources

| Source | Licence | Covers | Used for |
|---|---|---|---|
| [Olympedia](https://www.olympedia.org/countries/AUS), OlyMADMen | © OlyMADMen, cited | Summer 1896–2024, Winter 1924–2026 | Medal tallies; Milano Cortina 2026 tally |
| [Olympic Historical Dataset from Olympedia.org](https://www.kaggle.com/datasets/josephcheng123456/olympic-historical-dataset-from-olympediaorg), Joseph Cheng (Kaggle) | CC0 | 1896–2022 | Athlete results, medal tables, ranks |
| [Paris 2024 Olympic Summer Games](https://www.kaggle.com/datasets/piterfm/paris-2024-olympic-summer-games), Petro Ivaniuk (Kaggle) | CC BY-NC-SA 4.0 | Paris 2024 | Medals, medallists, athletes, birthplaces, world medal table |
| [Olympics-Dataset](https://github.com/KeithGalli/Olympics-Dataset), Keith Galli | MIT | 1896–2022 | Birthplaces (city, state, country) |
| [Australia at the Olympics](https://en.wikipedia.org/wiki/Australia_at_the_Olympics), Wikipedia | CC BY-SA 4.0 | 1896–2024 | Cross-check of tallies and ranks |
| [Population, total (SP.POP.TOTL)](https://data.worldbank.org/indicator/SP.POP.TOTL), World Bank ([CSV](https://api.worldbank.org/v2/en/indicator/SP.POP.TOTL?downloadformat=csv), [licence](https://datacatalog.worldbank.org/public-licenses)) | CC BY 4.0 | 2024 | Country populations |
| [National, state and territory population, March 2026](https://www.abs.gov.au/statistics/people/population/national-state-and-territory-population/latest-release), ABS | CC BY 4.0 | 31 Mar 2026 | State populations |
| [GeoNames AU gazetteer](https://download.geonames.org/export/dump/AU.zip) | CC BY 4.0 | Downloaded Oct 2026 | Birthplace coordinates |
| [world-atlas 2.0.2](https://github.com/topojson/world-atlas) | ISC (Natural Earth data: public domain) | — | World outlines |
| [Natural Earth](https://www.naturalearthdata.com/) admin-1, admin-0 (1:50m) and populated places | Public domain | — | State outlines, country label points, host-city locations |
| [country-codes](https://github.com/datasets/country-codes), datasets.io | PDDL | — | Olympic (IOC) to ISO country codes |

The Paris 2024 files are fetched from an unmodified public copy on GitHub ([simjoshi/Olympic_Data_Analysis](https://github.com/simjoshi/Olympic_Data_Analysis)) because Kaggle needs a login. Their Paris 2024 totals match Olympedia (18 gold, 19 silver, 16 bronze).

## Methodology

**Tallies.** Medal counts per Games come from Olympedia's medal table, not from adding up athlete rows. Summer 1896–2020 and Winter 1924–2022 come from the Kaggle Olympedia dataset; Paris 2024 from the Paris 2024 dataset; Milano Cortina 2026 (3 gold, 2 silver, 1 bronze) from Olympedia's Australia page ([`olympedia_additions.csv`](data/lookups/olympedia_additions.csv)). The Summer tallies match Wikipedia at every Games.

**Australasia.** In 1908 and 1912 Australia competed with New Zealand as "Australasia". Neither Olympedia nor the IOC credits those medals to Australia, so they are not counted.

**Team medals** count once per event, as in the official medal table. Medals won by mixed-nation teams are not credited to Australia, following Olympedia (one case: Teddy Flack's 1896 tennis doubles bronze with a British partner).

**Rank** is the medal-table position, ordered by gold, then silver, then bronze. Computed ranks match Wikipedia.

**Sports.** Disciplines are grouped into sports with [`sport_groups.csv`](data/lookups/sport_groups.csv) (for example, track, road and BMX cycling become Cycling).

**Gender** of a medal is the event's category: women's, men's, mixed or open.

**Linking Paris 2024 to earlier Games.** Paris medallists are matched to Olympedia athletes by surname and exact birth date. 55 of 95 matched exactly one earlier Australian Olympian, and none matched more than one. See [`paris_to_olympedia_matches.csv`](data/lookups/paris_to_olympedia_matches.csv).

**Birthplaces** come from Olympedia (via the Galli dataset) and, for Paris 2024 medallists missing there, from the Paris 2024 dataset. Six Paris records list only a city; their state is assigned in [`paris_city_to_state.csv`](data/lookups/paris_city_to_state.csv). Birth state is where an athlete was born, not where they trained or live.

**Birthplace coordinates.** A town is placed on the map only when its exact name matches exactly one populated place in that state in GeoNames. No position is estimated. Towns with no match, or with several places of the same name in the state, are left off and counted. See [`birthplace_geocodes.csv`](data/lookups/birthplace_geocodes.csv).

**Each person counts once** on every map.

### Coverage (from [`data/coverage.json`](data/coverage.json))

| Chart | Covers | Left out |
|---|---|---|
| Bin map of birthplaces, 1896–2024 (counts per 1° grid square; a dot map would stack the 126 medallists born in Sydney on one point) | 805 of 820 Australian-born medallists (98%) | 6 town names shared by several places, 5 with no match, 4 with no town recorded. Also 77 born overseas and 108 with no birthplace |
| State choropleth, 2000–2024 (medallists with at least one medal at Sydney 2000 or later) | 530 of 610 medallists | 55 born overseas, 22 with no birthplace, 3 born in Australia with no state |
| Flow map, birth country of medallists born overseas (not migration) | 77 medallists from 30 countries | none |
| World choropleth, Paris 2024 medals per million people | 92 medal-winning teams | Individual Neutral Athletes and the Refugee Olympic Team (no country); Chinese Taipei (no World Bank population) |

Small populations make rates unstable: the Northern Territory's rate rests on 10 people and the ACT's on 8.

## Rebuilding the data

1. Download the [Kaggle Olympedia dataset](https://www.kaggle.com/datasets/josephcheng123456/olympic-historical-dataset-from-olympediaorg) and unzip it into `archive/` (gitignored).
2. `python scripts/download_raw.py` downloads the other sources into `raw/` (gitignored).
3. `python scripts/build_data.py` writes the CSV files in `data/` and checks medal counts against the official tallies.
4. `python scripts/build_geo.py` writes the TopoJSON files in `data/geo/` (needs Node.js for mapshaper).

Requires Python 3 with pandas.

## Use of generative AI

Generative AI (Claude, by Anthropic) was used to help write the data-preparation scripts and chart specifications, to suggest layout and wording, and to check grammar. All data comes from the sources listed above, and every number, chart and sentence was checked by the author.
