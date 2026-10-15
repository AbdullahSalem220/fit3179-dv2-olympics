// Embeds each chart from its own specification file in specs/.
// Specs are added here one at a time in Phase 3.

// Shared look for every chart: page fonts and quiet axes.
// Type scale used across all specs:
//   20 chart title · 16 panel heading · 14 subtitle · 13 axis/legend title
//   12 annotations, direct labels, axis/legend labels · 11 numbers printed on marks
// No left/right padding, so chart titles line up with the page text.
const theme = {
  font: "Barlow",
  background: null,
  padding: { left: 0, right: 0, top: 5, bottom: 5 },
  view: { stroke: null },
  title: {
    font: "Barlow Condensed", fontSize: 20, fontWeight: 600, anchor: "start", color: "#1F2328",
    subtitleFont: "Barlow", subtitleFontSize: 14, subtitleColor: "#5A6169", offset: 12
  },
  header: {
    labelFont: "Barlow Condensed", labelFontSize: 16, labelFontWeight: 700, labelColor: "#1F2328"
  },
  axis: {
    labelFont: "Barlow", labelFontSize: 12, labelColor: "#5A6169",
    titleFont: "Barlow", titleFontSize: 13, titleFontWeight: 500, titleColor: "#5A6169",
    domainColor: "#BFC4C9", tickColor: "#BFC4C9", gridColor: "#E3DFD6"
  },
  legend: {
    labelFont: "Barlow", labelFontSize: 12, labelColor: "#5A6169",
    titleFont: "Barlow", titleFontSize: 13, titleFontWeight: 500, titleColor: "#1F2328"
  },
  text: { font: "Barlow", fontSize: 12, color: "#1F2328" }
};

// [container id, spec path]
const charts = [
  ["chart-waffle", "specs/01-waffle.vl.json"],
  ["chart-world", "specs/02-world-choropleth.vl.json"],
  ["chart-games", "specs/03-medals-by-games.vl.json"],
  ["chart-bump", "specs/04-rank-bump.vl.json"],
  ["chart-hosts", "specs/05-host-cities.vl.json"],
  ["chart-heatmap", "specs/06-sport-heatmap.vl.json"],
  ["chart-treemap", "specs/07-sport-treemap.vg.json"],
  ["chart-gender", "specs/08-gender-diverging.vl.json"],
  ["chart-athletes", "specs/09-top-athletes.vl.json"],
  ["chart-states", "specs/10-state-choropleth.vl.json"],
  ["chart-dots", "specs/11-birthplace-bins.vl.json"],
  ["chart-flow", "specs/12-overseas-flow.vl.json"],
  ["chart-seasons", "specs/13-summer-winter.vl.json"],
];

for (const [id, spec] of charts) {
  vegaEmbed(`#${id}`, spec, { actions: false, config: theme, renderer: "svg" })
    .catch(err => console.error(`Chart ${id} (${spec}) failed to load: ${err.message}`));
}
