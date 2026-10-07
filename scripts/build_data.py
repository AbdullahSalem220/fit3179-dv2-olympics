"""Build the trimmed data files in data/ from the raw sources.

Run from the repo root, after scripts/download_raw.py and after unzipping the
Kaggle Olympedia dataset into archive/:

    python scripts/build_data.py

Rules followed here (see README.md, Methodology):
- Medal tallies come from Olympedia's medal table, never from summed athlete rows.
- No value is estimated or invented. Records that cannot be matched are left
  out and counted, and the counts are written to data/coverage.json.
- Every hand-made lookup lives in data/lookups/ so it can be inspected.
"""
import json
import unicodedata
from pathlib import Path

import pandas as pd

ARCHIVE = Path("archive")
RAW = Path("raw")
DATA = Path("data")
LOOKUPS = DATA / "lookups"

STATE_ABBR = {
    "NSW": "New South Wales", "VIC": "Victoria", "QLD": "Queensland",
    "WA": "Western Australia", "SA": "South Australia", "TAS": "Tasmania",
    "NT": "Northern Territory", "ACT": "Australian Capital Territory",
}
GEONAMES_ADMIN1 = {
    "Australian Capital Territory": "01", "New South Wales": "02",
    "Northern Territory": "03", "Queensland": "04", "South Australia": "05",
    "Tasmania": "06", "Victoria": "07", "Western Australia": "08",
}
MEDALS = ["Gold", "Silver", "Bronze"]
CHOROPLETH_FROM = 2000

coverage = {}


def norm(text):
    """Lower-case ASCII form of a name, for exact name matching."""
    text = unicodedata.normalize("NFKD", str(text)).encode("ascii", "ignore").decode()
    return text.lower().replace("saint ", "st ").replace("mount ", "mt ").strip()


def write(df, name):
    path = DATA / name
    df.to_csv(path, index=False)
    print(f"wrote {path} ({len(df)} rows)")


# ---------------------------------------------------------------- load

def load_sources():
    src = {
        "results": pd.read_csv(ARCHIVE / "Olympic_Athlete_Event_Results.csv", encoding="utf-8-sig"),
        "bios": pd.read_csv(ARCHIVE / "Olympic_Athlete_Bio.csv"),
        "tally": pd.read_csv(ARCHIVE / "Olympic_Games_Medal_Tally.csv"),
        "galli": pd.read_csv(RAW / "galli_bios_locs.csv"),
        "p_medals": pd.read_csv(RAW / "paris_medals.csv"),
        "p_medallists": pd.read_csv(RAW / "paris_medallists.csv"),
        "p_total": pd.read_csv(RAW / "paris_medals_total.csv"),
        "p_athletes": pd.read_csv(RAW / "paris_athletes.csv"),
        "codes": pd.read_csv(RAW / "country_codes.csv", keep_default_na=False),
    }
    r = src["results"]
    r["year"] = r.edition.str[:4].astype(int)
    # The 1956 equestrian events were held separately in Stockholm; they belong to the 1956 Summer Games.
    r["season"] = r.edition.str.extract(r"(Summer|Winter|Equestrian)")[0].replace("Equestrian", "Summer")
    src["tally"]["season"] = src["tally"].edition.str.extract(r"(Summer|Winter|Equestrian)")[0].replace("Equestrian", "Summer")
    return src


def aus_summer_medal_rows(src):
    """Athlete rows for Australian Summer medals, excluding mixed-nation teams.

    Olympedia does not credit a medal to Australia when the team mixed athletes
    from different nations (e.g. Teddy Flack's 1896 tennis doubles bronze). It
    records such teams by listing the same athletes under several nations, so a
    row is mixed when its athlete appears under another nation in the same result.
    Shared bronzes (boxing, judo) are different athletes and are kept.
    """
    r = src["results"]
    medals = r[r.medal.notna() & (r.season == "Summer")]
    nocs_per_athlete = medals.groupby(["result_id", "athlete_id"]).country_noc.nunique()
    mixed = set(nocs_per_athlete[nocs_per_athlete > 1].index)
    aus = medals[medals.country_noc == "AUS"].copy()
    is_mixed = [(rid, a) in mixed for rid, a in zip(aus.result_id, aus.athlete_id)]
    coverage["mixed_nation_medal_rows_excluded"] = int(sum(is_mixed))
    return aus[[not x for x in is_mixed]]


# ---------------------------------------------------------------- tallies

def build_medals_by_games(src):
    t = src["tally"]
    aus = t[t.country_noc == "AUS"].groupby(["season", "year"])[["gold", "silver", "bronze"]].sum().reset_index()

    # Games Australia entered but won nothing at are missing from the tally; add them as zeros.
    r = src["results"]
    entered = r[r.country_noc == "AUS"][["season", "year"]].drop_duplicates()
    aus = entered.merge(aus, on=["season", "year"], how="left").fillna(0)

    paris = src["p_total"].query("country_code == 'AUS'").iloc[0]
    extra = pd.read_csv(LOOKUPS / "olympedia_additions.csv")
    rows = [{"season": "Summer", "year": 2024, "gold": paris["Gold Medal"],
             "silver": paris["Silver Medal"], "bronze": paris["Bronze Medal"]}]
    rows += extra[["season", "year", "gold", "silver", "bronze"]].to_dict("records")
    aus = pd.concat([aus, pd.DataFrame(rows)], ignore_index=True)
    aus[["gold", "silver", "bronze"]] = aus[["gold", "silver", "bronze"]].astype(int)
    aus["total"] = aus.gold + aus.silver + aus.bronze

    ranks = build_ranks(src)
    aus = aus.merge(ranks[ranks.noc == "AUS"][["season", "year", "rank"]], on=["season", "year"], how="left")
    aus = aus.sort_values(["season", "year"])
    write(aus, "medals_by_games.csv")

    # Sanity checks against Olympedia (https://www.olympedia.org/countries/AUS).
    s = aus[aus.season == "Summer"].set_index("year")
    assert tuple(s.loc[2024, ["gold", "silver", "bronze"]]) == (18, 19, 16)
    assert tuple(s.loc[2020, ["gold", "silver", "bronze"]]) == (17, 7, 22)
    assert s.loc[2024, "rank"] == 4
    return aus


def build_ranks(src):
    """Medal-table rank per Games, ordered by gold, then silver, then bronze (IOC convention)."""
    t = src["tally"].groupby(["season", "year", "country_noc", "country"])[["gold", "silver", "bronze"]].sum().reset_index()
    p = src["p_total"].rename(columns={"country_code": "country_noc", "Gold Medal": "gold",
                                       "Silver Medal": "silver", "Bronze Medal": "bronze"})
    p = p.assign(season="Summer", year=2024)[["season", "year", "country_noc", "country", "gold", "silver", "bronze"]]
    t = pd.concat([t, p], ignore_index=True)
    key = t.gold * 1_000_000 + t.silver * 1_000 + t.bronze
    t["rank"] = key.groupby([t.season, t.year]).rank(method="min", ascending=False).astype(int)
    t["total"] = t.gold + t.silver + t.bronze
    return t.rename(columns={"country_noc": "noc"})


def build_summer_ranks(src):
    ranks = build_ranks(src)
    ranks = ranks[(ranks.season == "Summer") & (ranks.year >= 1948)]
    write(ranks[["year", "noc", "country", "gold", "silver", "bronze", "total", "rank"]]
          .sort_values(["year", "rank"]), "summer_ranks.csv")


# ---------------------------------------------------------------- sport and gender

def medal_events(src):
    """One row per medal (team medals counted once), Summer 1896-2024."""
    rows = aus_summer_medal_rows(src)
    ev = rows.drop_duplicates(["year", "result_id", "medal"]).copy()
    ev["gender"] = ev.event.str.extract(r", (Men|Women|Mixed|Open)\b")[0]
    ev = ev.rename(columns={"sport": "discipline"})[["year", "discipline", "event", "medal", "gender"]]

    p = src["p_medals"].query("country_code == 'AUS'").copy()
    p["medal"] = p.medal_type.str.replace(" Medal", "")
    p["gender"] = p.gender.map({"W": "Women", "M": "Men", "X": "Mixed", "O": "Open"})
    p = p.assign(year=2024)[["year", "discipline", "event", "medal", "gender"]]

    ev = pd.concat([ev, p], ignore_index=True)
    groups = pd.read_csv(LOOKUPS / "sport_groups.csv")
    ev = ev.merge(groups, on="discipline", how="left")
    assert ev.sport_group.notna().all(), ev[ev.sport_group.isna()].discipline.unique()
    assert ev.gender.notna().all()
    return ev


def build_sport_and_gender(src, games):
    ev = medal_events(src)

    # Check: medals per Games must equal the official tally.
    official = games[games.season == "Summer"].set_index("year")
    counted = ev.groupby(["year", "medal"]).size().unstack(fill_value=0)
    for year, row in counted.iterrows():
        got = (row.get("Gold", 0), row.get("Silver", 0), row.get("Bronze", 0))
        want = tuple(official.loc[year, ["gold", "silver", "bronze"]])
        assert got == want, f"{year}: event rows {got} != tally {want}"

    sport = ev.groupby(["year", "sport_group", "discipline", "medal"]).size().rename("medals").reset_index()
    write(sport, "medals_by_sport_games.csv")

    gender = ev.groupby(["year", "gender", "medal"]).size().rename("medals").reset_index()
    write(gender, "medals_by_gender_games.csv")

    paris = ev[ev.year == 2024][["sport_group", "discipline", "event", "medal", "gender"]]
    paris = paris.assign(medal_order=paris.medal.map({m: i for i, m in enumerate(MEDALS)}))
    write(paris.sort_values(["medal_order", "sport_group"]).drop(columns="medal_order"), "paris2024_aus_medals.csv")


# ---------------------------------------------------------------- people

def match_paris_to_olympedia(src):
    """Link Paris 2024 medallists to Olympedia athlete ids by surname + birth date."""
    pm = src["p_medallists"].query("country_code == 'AUS'")
    people = src["p_athletes"][src["p_athletes"].code.isin(pm.code_athlete)].copy()

    def surname(name):
        return norm(" ".join(t for t in str(name).split() if t.isupper()))

    people["key_surname"] = people.name.map(surname)
    people["birth"] = pd.to_datetime(people.birth_date, errors="coerce").dt.date

    aus_ids = src["results"].query("country_noc == 'AUS'").athlete_id.unique()
    bios = src["bios"][src["bios"].athlete_id.isin(aus_ids)].copy()
    bios["birth"] = pd.to_datetime(bios.born, errors="coerce", format="mixed").dt.date

    matches = []
    for p in people.itertuples():
        cands = bios[(bios.birth == p.birth) & bios.name.map(lambda n: norm(n).endswith(p.key_surname))]
        matches.append({"paris_code": p.code, "paris_name": p.name, "birth_date": p.birth,
                        "olympedia_id": cands.athlete_id.iloc[0] if len(cands) == 1 else None,
                        "olympedia_name": cands.name.iloc[0] if len(cands) == 1 else None,
                        "candidates": len(cands)})
    m = pd.DataFrame(matches)
    m.to_csv(LOOKUPS / "paris_to_olympedia_matches.csv", index=False)
    coverage["paris_medallists"] = len(m)
    coverage["paris_medallists_matched_to_olympedia"] = int(m.olympedia_id.notna().sum())
    return people, m


def build_people(src, people, matches):
    """One row per Australian Summer medallist (1896-2024) with medals and birthplace."""
    rows = aus_summer_medal_rows(src)
    hist = rows.groupby("athlete_id").agg(
        gold=("medal", lambda s: (s == "Gold").sum()),
        silver=("medal", lambda s: (s == "Silver").sum()),
        bronze=("medal", lambda s: (s == "Bronze").sum()),
        first_year=("year", "min"), last_year=("year", "max"),
        disciplines=("sport", lambda s: "; ".join(sorted(set(s)))),
    ).reset_index()
    hist["person_id"] = "O" + hist.athlete_id.astype(str)
    hist = hist.merge(src["bios"][["athlete_id", "name", "sex"]], on="athlete_id", how="left")

    g = src["galli"][["athlete_id", "born_city", "born_region", "born_country"]]
    hist = hist.merge(g, on="athlete_id", how="left")
    hist["birth_source"] = hist.born_country.notna().map({True: "Olympedia (via Galli)", False: None})

    # Paris 2024 medals per person.
    pm = src["p_medallists"].query("country_code == 'AUS'").copy()
    pm["medal"] = pm.medal_type.str.replace(" Medal", "")
    pmed = pm.groupby("code_athlete").medal.value_counts().unstack(fill_value=0).reindex(columns=MEDALS, fill_value=0)
    pmed.columns = ["p_gold", "p_silver", "p_bronze"]
    pdisc = pm.groupby("code_athlete").discipline.agg(lambda s: "; ".join(sorted(set(s))))

    ppl = people.set_index("code").join(pmed).join(pdisc.rename("p_disc"))
    ppl = ppl.join(matches.set_index("paris_code")[["olympedia_id"]])

    def paris_birthplace(row):
        place, country = row.birth_place, row.birth_country
        if not isinstance(place, str):
            return None, None, (None if pd.isna(country) else country)
        parts = [x.strip() for x in place.split(",")]
        if parts[-1].upper() in STATE_ABBR:
            city = parts[0] if len(parts) > 1 else None
            return city, STATE_ABBR[parts[-1].upper()], country
        lookup = pd.read_csv(LOOKUPS / "paris_city_to_state.csv").set_index("birth_place").state
        return parts[0], lookup.get(parts[0].upper()), country

    names = pd.read_csv(LOOKUPS / "country_name_to_ioc.csv").set_index("country_name").ioc

    new_rows = []
    for code, p in ppl.iterrows():
        city, state, country = paris_birthplace(p)
        ioc = "AUS" if country == "Australia" else names.get(country) if country else None
        if pd.notna(p.olympedia_id) and (hist.athlete_id == p.olympedia_id).any():
            i = hist.index[hist.athlete_id == p.olympedia_id][0]
            hist.loc[i, ["gold", "silver", "bronze"]] += [p.p_gold, p.p_silver, p.p_bronze]
            hist.loc[i, "last_year"] = 2024
            hist.loc[i, "disciplines"] = "; ".join(sorted(set(hist.loc[i, "disciplines"].split("; ")) | set(p.p_disc.split("; "))))
            if pd.isna(hist.loc[i, "born_country"]) and ioc:
                hist.loc[i, ["born_city", "born_region", "born_country", "birth_source"]] = [city, state, ioc, "Paris 2024 dataset"]
        else:
            # First Olympic medal in Paris. If they competed earlier without a medal,
            # keep their Olympedia id and prefer the Olympedia birthplace.
            row = {"person_id": "P" + str(code), "athlete_id": None, "name": p["name"],
                   "sex": p.gender, "gold": p.p_gold, "silver": p.p_silver, "bronze": p.p_bronze,
                   "first_year": 2024, "last_year": 2024, "disciplines": p.p_disc,
                   "born_city": city, "born_region": state, "born_country": ioc,
                   "birth_source": "Paris 2024 dataset" if ioc else None}
            if pd.notna(p.olympedia_id):
                row["athlete_id"], row["person_id"] = p.olympedia_id, "O" + str(int(p.olympedia_id))
                gb = g[g.athlete_id == p.olympedia_id]
                if len(gb) and pd.notna(gb.born_country.iloc[0]):
                    row.update(born_city=gb.born_city.iloc[0], born_region=gb.born_region.iloc[0],
                               born_country=gb.born_country.iloc[0], birth_source="Olympedia (via Galli)")
            new_rows.append(row)
    allp = pd.concat([hist, pd.DataFrame(new_rows)], ignore_index=True)
    allp[["gold", "silver", "bronze"]] = allp[["gold", "silver", "bronze"]].astype(int)
    allp["total"] = allp.gold + allp.silver + allp.bronze
    allp["born_state"] = allp.born_region.where(allp.born_country == "AUS")
    return allp


def build_top_athletes(people):
    top = people.sort_values(["gold", "total", "silver"], ascending=False).head(30)
    write(top[["name", "sex", "gold", "silver", "bronze", "total", "first_year", "last_year", "disciplines"]],
          "top_athletes.csv")


def geocode_birthplaces(people):
    cols = "geonameid name asciiname alt lat lon fclass fcode cc cc2 a1 a2 a3 a4 pop elev dem tz mod".split()
    g = pd.read_csv(RAW / "AU.txt", sep="\t", names=cols, dtype={"a1": str}, keep_default_na=False, quoting=3)
    g = g[g.fclass == "P"].copy()
    g["key"] = g.asciiname.map(norm)
    groups = g.groupby(["key", "a1"])

    au = people[people.born_country == "AUS"].copy()
    status, lat, lon, gid = [], [], [], []
    for city, state in zip(au.born_city, au.born_state):
        a1 = GEONAMES_ADMIN1.get(state)
        if not isinstance(city, str) or a1 is None:
            status.append("no town recorded"); lat.append(None); lon.append(None); gid.append(None); continue
        key = (norm(city), a1)
        if key not in groups.groups:
            status.append("no match"); lat.append(None); lon.append(None); gid.append(None); continue
        hit = groups.get_group(key)
        if len(hit) > 1:
            status.append("several places with this name"); lat.append(None); lon.append(None); gid.append(None); continue
        status.append("matched"); lat.append(hit.lat.iloc[0]); lon.append(hit.lon.iloc[0]); gid.append(hit.geonameid.iloc[0])
    au["geo_status"], au["lat"], au["lon"], au["geonameid"] = status, lat, lon, gid

    log = (au.groupby(["born_city", "born_state", "geo_status"], dropna=False)
             .agg(people=("person_id", "count"), geonameid=("geonameid", "first"), lat=("lat", "first"), lon=("lon", "first"))
             .reset_index().sort_values(["geo_status", "people"], ascending=[True, False]))
    log.to_csv(LOOKUPS / "birthplace_geocodes.csv", index=False)

    dots = au[au.geo_status == "matched"][["name", "born_city", "born_state", "lat", "lon", "first_year", "last_year", "total"]]
    write(dots.rename(columns={"born_city": "town", "born_state": "state"}), "birthplaces.csv")

    coverage["dot_map"] = {
        "span": "1896-2024",
        "medallists": len(people),
        "born_in_australia": len(au),
        "mapped": int((au.geo_status == "matched").sum()),
        "not_mapped": au[au.geo_status != "matched"].geo_status.value_counts().to_dict(),
        "born_overseas": int((people.born_country.notna() & (people.born_country != "AUS")).sum()),
        "no_birthplace": int(people.born_country.isna().sum()),
    }


def build_state_choropleth(people):
    recent = people[people.last_year >= CHOROPLETH_FROM]
    pop = pd.read_csv(LOOKUPS / "abs_state_population_2026.csv")
    counts = recent.born_state.value_counts().rename("medallists")
    out = pop.set_index("state").join(counts).fillna({"medallists": 0}).reset_index()
    out["medallists"] = out.medallists.astype(int)
    out["per_million"] = (out.medallists / out.population * 1e6).round(1)
    write(out[["state", "abbr", "medallists", "population", "per_million"]], "state_medallists.csv")
    coverage["state_choropleth"] = {
        "span": f"{CHOROPLETH_FROM}-2024",
        "medallists": len(recent),
        "with_known_birth_state": int(recent.born_state.notna().sum()),
        "born_overseas": int((recent.born_country.notna() & (recent.born_country != "AUS")).sum()),
        "no_birthplace": int(recent.born_country.isna().sum()),
        "born_in_australia_state_unknown": int(((recent.born_country == "AUS") & recent.born_state.isna()).sum()),
    }


def ioc_crosswalk(src):
    """IOC code -> (iso3, iso_n3, country), from datasets/country-codes plus visible overrides."""
    codes = src["codes"]
    xw = codes[codes.IOC != ""][["IOC", "ISO3166-1-Alpha-3", "ISO3166-1-numeric", "CLDR display name"]]
    xw.columns = ["ioc", "iso3", "iso_n3", "country"]
    xw = xw.assign(iso_n3=xw.iso_n3.astype(str).str.zfill(3))
    over = pd.read_csv(LOOKUPS / "ioc_overrides.csv", dtype=str)[["ioc", "iso3", "iso_n3", "country"]]
    xw = pd.concat([xw[~xw.ioc.isin(over.ioc)], over], ignore_index=True)
    return xw.set_index("ioc")


def build_overseas_born(src, people):
    xw = ioc_crosswalk(src)
    ioc_to_iso3, names = xw.iso3.to_dict(), xw.country.to_dict()
    # 1:50m countries include small places (Hong Kong, Singapore) missing at 1:110m.
    ne = json.loads((RAW / "ne_50m_admin_0_countries.geojson").read_text(encoding="utf8"))
    label = {}
    for f in ne["features"]:
        p = f["properties"]
        for k in ("ISO_A3", "ADM0_A3", "ISO_A3_EH"):
            if p.get(k) and p[k] != "-99":
                label.setdefault(p[k], (p["LABEL_Y"], p["LABEL_X"]))

    over = people[people.born_country.notna() & (people.born_country != "AUS")]
    counts = over.born_country.value_counts().rename_axis("ioc").rename("medallists").reset_index()
    counts["iso3"] = counts.ioc.map(ioc_to_iso3)
    counts["country"] = counts.ioc.map(names)
    counts["lat"] = counts.iso3.map(lambda c: label.get(c, (None, None))[0])
    counts["lon"] = counts.iso3.map(lambda c: label.get(c, (None, None))[1])
    unmatched = counts[counts.lat.isna()]
    coverage["flow_map"] = {
        "overseas_born_medallists": int(counts.medallists.sum()),
        "countries": len(counts),
        "countries_without_coordinates": unmatched.ioc.tolist(),
        "medallists_without_coordinates": int(unmatched.medallists.sum()),
    }
    dest_lat, dest_lon = label["AUS"]
    counts = counts.dropna(subset=["lat"]).assign(dest_lat=dest_lat, dest_lon=dest_lon)
    write(counts.sort_values("medallists", ascending=False), "overseas_born.csv")


# ---------------------------------------------------------------- maps: world and host cities

def build_paris_world(src):
    p = src["p_total"].rename(columns={"country_code": "noc", "Gold Medal": "gold",
                                       "Silver Medal": "silver", "Bronze Medal": "bronze", "Total": "total"})
    xw = ioc_crosswalk(src)[["iso3", "iso_n3"]].rename_axis("noc").reset_index()
    p = p.merge(xw, on="noc", how="left")

    wb = json.loads((RAW / "worldbank_population_2024.json").read_text())[1]
    pop = {d["countryiso3code"]: d["value"] for d in wb if d["value"]}
    p["population_2024"] = p.iso3.map(pop)
    p["medals_per_million"] = (p.total / p.population_2024 * 1e6).round(2)
    coverage["world_choropleth"] = {
        "medal_winning_teams": len(p),
        "without_country_code": p[p.iso3.isna()].noc.tolist(),
        "without_population": p[p.iso3.notna() & p.population_2024.isna()].noc.tolist(),
    }
    write(p[["noc", "country", "iso3", "iso_n3", "gold", "silver", "bronze", "total", "population_2024", "medals_per_million"]],
          "paris2024_world.csv")


def build_host_cities(games):
    hc = pd.read_csv(LOOKUPS / "host_cities.csv", keep_default_na=False)
    ne = json.loads((RAW / "ne_10m_populated_places.geojson").read_text(encoding="utf8"))
    where = {(f["properties"]["NAMEASCII"], f["properties"]["ADM0NAME"]): f["geometry"]["coordinates"] for f in ne["features"]}
    hc["lon"] = [where[(n, c)][0] for n, c in zip(hc.ne_nameascii, hc.ne_adm0name)]
    hc["lat"] = [where[(n, c)][1] for n, c in zip(hc.ne_nameascii, hc.ne_adm0name)]
    s = games[games.season == "Summer"][["year", "gold", "silver", "bronze", "total"]]
    hc = hc.merge(s, on="year", how="left")
    write(hc[["year", "city", "country", "lat", "lon", "gold", "silver", "bronze", "total", "note"]], "host_cities.csv")


def main():
    src = load_sources()
    games = build_medals_by_games(src)
    build_summer_ranks(src)
    build_sport_and_gender(src, games)
    people, matches = match_paris_to_olympedia(src)
    allp = build_people(src, people, matches)
    build_top_athletes(allp)
    geocode_birthplaces(allp)
    build_state_choropleth(allp)
    build_overseas_born(src, allp)
    build_paris_world(src)
    build_host_cities(games)
    (DATA / "coverage.json").write_text(json.dumps(coverage, indent=2, default=int))
    print(json.dumps(coverage, indent=2, default=int))


if __name__ == "__main__":
    main()
