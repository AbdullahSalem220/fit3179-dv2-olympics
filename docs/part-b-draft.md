# Part B: Domain description (draft)

## Domain
The domain is sport, specifically Australia's performance at the Olympic Games (topic #8, Australia's Olympic Performance). The visualisation covers every Summer Games from Athens 1896 to Paris 2024, plus Winter Games results up to Milano Cortina 2026. It looks at results across Games, medals by sport, athlete and gender, Australia's strongest events, how performance has changed over time, and notable achievements.

## Why and Who
**Who:** the average Australian with no background in statistics. The Olympics are one of the few events most Australians follow, but medal tables only show one Games at a time and favour big countries.
**Why:** to give a clear, engaging picture that a medal table cannot: how a country of 27 million compares per person (8th in the world in Paris), how results collapsed in 1976 and recovered after the Australian Institute of Sport opened in 1981, which sports and athletes deliver the medals, how women now win most medals, and where medallists were born. The page is designed as a story, read top to bottom, with tooltips for detail rather than as an exploration tool.

## What (data)
- **Olympedia** (OlyMADMen), the most authoritative Olympic statistics database: official medal tally per Games, Summer 1896–2024 and Winter 1924–2026.
- **Olympic Historical Dataset from Olympedia.org** (Joseph Cheng, Kaggle, CC0, updated June 2024): athlete-level results and every country's medal table, 1896–2022. Used for sport, gender, athlete and rank charts.
- **Paris 2024 Olympic Summer Games** (Petro Ivaniuk, Kaggle, CC BY-NC-SA 4.0, from the official Paris 2024 results): medals, medallists and athletes, including birthplaces.
- **Olympics-Dataset** (Keith Galli, MIT, scraped from Olympedia): athletes' birthplaces, joined by Olympedia athlete ID.
- **World Bank** population 2024 (CC BY 4.0) and **ABS** state population, March 2026 (CC BY 4.0): to turn counts into per-person rates.
- **GeoNames** (CC BY 4.0) for birthplace coordinates; **Natural Earth** and **world-atlas** for map outlines; **country-codes** (PDDL) to match Olympic country codes to map codes.

How the data was prepared: Python scripts (in the repository) trim the raw files to about 250 KB. Medal tallies always come from the official table, and the scripts check that event-level counts add up to it for every Games. Team medals count once, as in the official table. Birthplaces are placed only when the town name matches exactly one place in that state; 805 of 820 Australian-born medallists (98%) could be placed. Nothing is estimated; unmatched records are left out and counted on the page.

## How (idioms and rationale)
The page has nine sections with 13 charts, including nine advanced charts and four different map idioms:
1. **Waffle chart:** Paris 2024's 53 medals, one square each, grouped by sport (countable and engaging as a hook).
2. **Choropleth map:** Paris medals per million people (a rate per country, Equal Earth projection to keep areas true).
3. **Stacked bar chart:** medals per Games, with annotations for the story's turning points.
4. **Bump chart:** rank against five rival nations (rank is ordinal; shows the 1976 fall and recovery).
5. **Proportional symbol map:** medals by host city, with a Europe inset.
6. **Heat map:** medals by sport and Games (two keys at once; shows swimming's unbroken run since 1948).
7. **Treemap (Vega):** share of all 594 Summer medals by sport (part-to-whole).
8. **Diverging bar chart:** women's versus men's medals per Games.
9. **Dot plot:** top 15 Olympians by gold and total medals.
10. **Choropleth map:** medallists per million by birth state (standardised by population; equal-area projection).
11. **Bin map:** birthplaces counted in 1° squares.
12. **Flow map:** birth country of overseas-born medallists (great-circle lines to Australia).
13. **Small multiples:** Summer and Winter medals per Games.

Design choices: one green hue for Australia and for "more" in every map, a neutral grey for everything else (figure–ground), medal colours that differ in lightness, and purple/orange for women/men to avoid gender stereotypes. Typography uses the Barlow family (condensed for headings and numbers, regular for body text) with lines of about 60 characters. Each chart has a headline title that states its finding, on-chart annotations, a short caption and tooltips.

**Changes from the original plan:**
- **Chart 5 (host-city map):** a Europe inset was added because eight host cities in Europe overlapped on the world map and their circles became unreadable.
- **Chart 11 (birthplaces):** changed from a dot map to a bin map. 126 medallists list Sydney as their birthplace, so one dot per person would have stacked them all on a single point and hidden the concentration. Spreading dots out would have meant inventing positions, so the map counts medallists in 1° squares instead.

Special features: hover highlighting in the bump chart, a Vega treemap, great-circle flow lines computed in the chart specification, and an automated check that every medal count matches the official tally.
