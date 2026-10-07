// Embeds each chart from its own specification file in specs/.
// Specs are added here one at a time in Phase 3.

// Shared look for every chart: page fonts and quiet axes.
const theme = {
  font: "Barlow",
  background: null,
  view: { stroke: null },
  title: { font: "Barlow Condensed", fontSize: 20, fontWeight: 600, anchor: "start", color: "#1F2328" },
  axis: {
    labelFont: "Barlow", labelFontSize: 12, labelColor: "#5A6169",
    titleFont: "Barlow", titleFontSize: 13, titleFontWeight: 500, titleColor: "#5A6169",
    domainColor: "#BFC4C9", tickColor: "#BFC4C9", gridColor: "#E3DFD6"
  },
  legend: {
    labelFont: "Barlow", labelFontSize: 12, labelColor: "#5A6169",
    titleFont: "Barlow", titleFontSize: 13, titleFontWeight: 500, titleColor: "#1F2328"
  },
  text: { font: "Barlow", color: "#1F2328" }
};

// [container id, spec path]
const charts = [
  ["chart-waffle", "specs/01-waffle.vl.json"],
  ["chart-world", "specs/02-world-choropleth.vl.json"],
];

for (const [id, spec] of charts) {
  vegaEmbed(`#${id}`, spec, { actions: false, config: theme, renderer: "svg" })
    .catch(err => console.error(`Chart ${id} (${spec}) failed to load:`, err));
}
