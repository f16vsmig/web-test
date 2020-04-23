var orgchart = new getOrgChart(document.getElementById("people"), {
  orientation: getOrgChart.RO_LEFT,
  dataSource: [
    { id: 1, parentId: null, Name: "Amber McKenzie" },
    { id: 2, parentId: 1, Name: "Ava Field" },
    { id: 3, parentId: 1, Name: "Evie Johnson" }
  ]
});
