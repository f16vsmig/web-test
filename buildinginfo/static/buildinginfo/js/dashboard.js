// Load the Visualization API and the corechart package.
google.charts.load("current", { packages: ["corechart"] });

function sortAsc(data) {
  data.sort(function(a, b) {
    return a[1] - b[1];
  });
  return data;
}

function sortDesc(data) {
  data.sort(function(a, b) {
    return b[1] - a[1];
  });
  return data;
}

function findBuildingRowNo(data, name) {
  rowNo = data.findIndex((item, idx) => {
    return item[0] == name;
  });
  return rowNo - 1;
}

function popup() {
  document.body.style.overflow = "hidden";
  var chartContainer = document.createElement("div");
  var chartDiv = document.createElement("div");
  var parent = document.getElementById("wrap");
  parent.appendChild(chartContainer);
  chartContainer.id = "chart-container";
  chartContainer.appendChild(chartDiv);
  chartContainer.style.width = "100vw";
  chartContainer.style.height = "100vh";
  chartContainer.style.position = "fixed";
  chartContainer.style.top = "0";
  chartContainer.style.left = "0";
  chartContainer.style.zIndex = "9999";
  chartContainer.style.background = "rgba(0,0,0,0.7)";
  chartContainer.classList.add("flex-xy-center");
  chartContainer.addEventListener("click", function() {
    chartContainer.remove();
    document.body.style.overflow = "auto";
  });

  chartDiv.id = "popup-chart";
  chartDiv.style.width = "60vw";
  chartDiv.style.height = "60vh";
}

function toBenchmarkData(data, xaxis, yaxis, asc) {
  var result = [];
  result.push([xaxis, yaxis, { role: "style" }]);
  for (var i = 0; i < data.length; i++) {
    var xValue = data[i][xaxis];
    var yValue = data[i][yaxis];
    if (xValue == buildingName) {
      result.push([xValue, yValue, "#E74C3C"]);
    } else {
      result.push([xValue, yValue, "#3498DB"]);
    }
  }
  if (asc == "desc") {
    sortDesc(result);
  } else {
    sortAsc(result);
  }
  console.log(result);
  return result;
}

function drawHistogramChart(xaxis, yaxis, asc) {
  var rawdata = [];
  for (var i = 0; i < buildingIdList.length; i++) {
    var buildingId = buildingIdList[i];
    var url =
      "http://localhost:8000/buildinginfo/annual-data-for-one/" + buildingId + "/?xaxis=" + xaxis + "&yaxis=" + yaxis;
    var json = getJson(url);
    rawdata.push(json);
  }
  var data = toBenchmarkData(rawdata, xaxis, yaxis, asc);
  // var rowNo = findBuildingRowNo(data, buildingName);

  var rowNo = data.findIndex((item, idx) => {
    return item[0] == buildingName;
  });

  var chartData = google.visualization.arrayToDataTable(data);
  var options = {
    title: "전체 빌딩 분포표",
    legend: { position: "none" },
    tooltip: { trigger: "both" },
    colors: ["#3498DB"]
  };
  popup();
  var chart = new google.visualization.Histogram(document.getElementById("popup-chart"));
  chart.draw(chartData, options);
  chart.setSelection([{ row: rowNo - 1, column: 1 }]);
}

function drawBarChart(xaxis, yaxis, asc) {
  var rawdata = [];
  for (var i = 0; i < buildingIdList.length; i++) {
    var buildingId = buildingIdList[i];
    var url =
      "http://localhost:8000/buildinginfo/annual-data-for-one/" + buildingId + "/?xaxis=" + xaxis + "&yaxis=" + yaxis;
    var json = getJson(url);
    rawdata.push(json);
  }
  console.log(rawdata);
  var data = toBenchmarkData(rawdata, xaxis, yaxis, asc);
  var chartData = google.visualization.arrayToDataTable(data);

  // var chartData = google.visualization.arrayToDataTable();

  var options = {
    title: "전체 빌딩 순위",
    legend: { position: "none" },
    tooltip: { trigger: "both" }
  };
  popup();
  var chart = new google.visualization.BarChart(document.getElementById("popup-chart"));
  chart.draw(chartData, options);
}

function toDailyTimeData(data, xaxis, yaxis) {
  var result = [];
  result.push(["xaxis", "yaxis"]);
  for (var i = 0; i < data.length; i++) {
    var xValue = data[i][xaxis];
    var yValue = data[i][yaxis];
    if (i == 0) {
      result.push([xValue, yValue]);
    } else {
      result.push([xValue, yValue]);
    }
  }
  return result;
}

function drawLineChart(buildingId, xaxis, yaxis) {
  popup();
  url = "http://localhost:8000/buildinginfo/trend-data/" + buildingId + "/?xaxis=" + xaxis + "&yaxis=" + yaxis;
  console.log(url);
  json = getJson(url);
  data = toDailyTimeData(json, xaxis, yaxis);

  var options = {
    title: "Age of sugar maples vs. trunk diameter, in inches",
    hAxis: { title: "Diameter" },
    vAxis: { title: "Age" },
    legend: "none",
    tooltip: { trigger: "focus" },
    // Group selections
    // by x-value.
    aggregationTarget: "category"
  };
  var chartData = google.visualization.arrayToDataTable(data);
  var chart = new google.visualization.LineChart(document.getElementById("popup-chart"));
  chart.draw(chartData, options);
}

function toDailyScatterData(data, xaxis, yaxis) {
  var year = new Date().getFullYear();
  var result = [];
  result.push(["xaxis", "yaxis", { role: "tooltip" }, { role: "style" }]);
  for (var i = 0; i < data.length; i++) {
    var xValue = data[i][xaxis];
    var yValue = data[i][yaxis];
    var date = data[i]["date"];
    var tooltip = date + " : (" + xValue.toFixed(1) + "," + yValue + ")";
    if (data[i]["year"] == year) {
      var style = "#E74C3C";
    } else if (data[i]["year"] == year - 1) {
      var style = "#3498DB";
    } else {
      var style = "black";
    }
    result.push([xValue, yValue, tooltip, style]);
  }
  return result;
}

function drawVAxisLine(chart, value) {
  var layout = chart.getChartLayoutInterface();
  var chartArea = layout.getChartAreaBoundingBox();

  var svg = chart.getContainer().getElementsByTagName("svg")[0];
  var xLoc = layout.getXLocation(value);
  svg.appendChild(createLine(xLoc, chartArea.top + chartArea.height, xLoc, chartArea.top, "red", 1)); // axis line
}

function createLine(x1, y1, x2, y2, color, w) {
  var line = document.createElementNS("http://www.w3.org/2000/svg", "line");
  line.setAttribute("x1", x1);
  line.setAttribute("y1", y1);
  line.setAttribute("x2", x2);
  line.setAttribute("y2", y2);
  line.setAttribute("stroke", color);
  line.setAttribute("stroke-width", w);
  return line;
}

function drawDailyScatterChart(buildingId, xaxis, yaxis, start, end) {
  url = "http://localhost:8000/buildinginfo/daily-data/" + buildingId + "/?xaxis=" + xaxis + "&yaxis=" + yaxis;
  if (start != undefined) {
    url += "&start=" + start;
  }
  if (end != undefined) {
    url += "&end=" + end;
  }

  json = getJson(url);
  console.log(json);
  data = toDailyScatterData(json, xaxis, yaxis);
  console.log(data);
  var options = {
    title: "Age of sugar maples vs. trunk diameter, in inches",
    hAxis: { title: "Diameter" },
    vAxis: { title: "Age" },
    legend: "none"
  };
  popup();
  var chartData = google.visualization.arrayToDataTable(data);
  var chart = new google.visualization.ScatterChart(document.getElementById("popup-chart"));
  chart.draw(chartData, options);
  drawVAxisLine(chart, 12);
}

function drawTrendline(buildingId, xaxis, yaxis) {
  url = "http://localhost:8000/buildinginfo/daily-data/" + buildingId + "/?xaxis=" + xaxis + "&yaxis=" + yaxis;
  json = getJson(url);
  console.log(json);
  data = toDailyScatterData(json, xaxis, yaxis);

  var options = {
    title: "Age of sugar maples vs. trunk diameter, in inches",
    hAxis: { title: "Diameter" },
    vAxis: { title: "Age" },
    legend: "none",
    trendlines: {
      0: {
        type: "linear"
      }
    } // Draw a trendline for data series 0.
  };
  popup();
  var chartData = google.visualization.arrayToDataTable(data);
  var chart = new google.visualization.ScatterChart(document.getElementById("popup-chart"));
  chart.draw(chartData, options);
}

function toAnnualScatterData(data, xaxis, yaxis, annotation) {
  var xticks = [];
  var result = [];
  result.push(["xaxis", "yaxis", { role: "tooltip" }, { role: "style" }]);
  for (var i = 0; i < data.length; i++) {
    var x = data[i][xaxis];
    // string일 경우도 같은 x축에 정렬
    if (typeof x == "string" && xticks.indexOf(x) == -1) {
      xticks.push(x);
      var xValue = xticks.length;
    } else if (typeof x == "string" && xticks.indexOf(x) != -1) {
      var xValue = xticks.length;
    } else {
      var xValue = x;
    }
    var yValue = data[i][yaxis];
    var name = data[i]["name"];
    var tooltip = name + " : " + yValue;
    if (data[i][annotation] == buildingName) {
      var style = "#E74C3C";
    } else {
      var style = "#3498DB";
    }
    result.push([xValue, yValue, tooltip, style]);
  }
  console.log(xticks);
  return result;
}

function drawAnnualScatterChart(xaxis, yaxis, annotation) {
  popup();
  url = "http://localhost:8000/buildinginfo/annual-data/?xaxis=" + xaxis + "&yaxis=" + yaxis;
  if (annotation != undefined) {
    url += "&annotation=" + annotation;
  }
  console.log(url);
  json = getJson(url);
  data = toAnnualScatterData(json, xaxis, yaxis, annotation);
  console.log(data);
  var options = {
    title: "Age of sugar maples vs. trunk diameter, in inches",
    hAxis: {
      title: xaxis,
      ticks: getScatterXticks(json, xaxis)
    },
    vAxis: { title: yaxis },
    legend: "none",
    trendlines: getTrendlineOption(json, xaxis)
  };
  var chartData = google.visualization.arrayToDataTable(data);
  var chart = new google.visualization.ScatterChart(document.getElementById("popup-chart"));
  chart.draw(chartData, options);
}

function getScatterXticks(data, xaxis) {
  if (typeof data[0][xaxis] == "string") {
    var compair = [];
    var xticks = [];
    for (var i = 0; i < data.length; i++) {
      xValue = data[i][xaxis];
      if (compair.indexOf(xValue) == -1) {
        compair.push(xValue);
        xValue = xticks.length + 1;
        xticks.push({ v: xValue, f: data[i][xaxis] });
      }
    }
    return xticks;
  } else {
    return "auto";
  }
}

function getTrendlineOption(data, xaxis) {
  if (typeof data[0][xaxis] == "string") {
    return null;
  } else {
    var option = {
      0: {
        type: "linear"
      }
    };
    return option;
  }
}

function toColumnChartData(data, xaxis, yaxis) {
  var result = [];
  var lable = [];
  yaxis = yaxis.replace(/ /gi, "");
  lable.push(xaxis);
  for (var i = 0; i < yaxis.split(",").length; i++) {
    lable.push(yaxis.split(",")[i]);
  }
  result.push(lable);

  for (var i = 0; i < data.length; i++) {
    var row = [];
    for (var j = 0; j < lable.length; j++) {
      idxName = lable[j];
      row.push(data[i][idxName]);
    }
    result.push(row);
  }
  return result;
}

function drawAnnualColumnChart(xaxis, yaxis, groupBy) {
  popup();
  url = "http://localhost:8000/buildinginfo/annual-data-group-by/?xaxis=" + xaxis + "&yaxis=" + yaxis;
  console.log(url);
  json = getJson(url);
  console.log(json);
  data = toColumnChartData(json, xaxis, yaxis);
  console.log(data);
  var options = {
    title: "차트 보기",
    hAxis: { title: xaxis },
    vAxis: { title: yaxis.replace(",", "+") },
    legend: "none",
    trendlines: {
      0: {
        type: "linear"
      }
    }, // Draw a trendline for data series 0.
    isStacked: true
  };
  var chartData = google.visualization.arrayToDataTable(data);
  var chart = new google.visualization.ColumnChart(document.getElementById("popup-chart"));
  chart.draw(chartData, options);
}

function drawMonthlyColumnChart(buildingId, xaxis, yaxis) {
  popup();
  url = "http://localhost:8000/buildinginfo/monthly-data/" + buildingId + "/?xaxis=" + xaxis + "&yaxis=" + yaxis;
  json = getJson(url);
  data = toColumnChartData(json, xaxis, yaxis);
  console.log(data);
  var options = {
    title: "연간 현황 차트",
    hAxis: { title: xaxis },
    vAxis: { title: yaxis.replace(",", " +") },
    legend: "none",
    trendlines: {
      0: {
        type: "linear"
      }
    }, // Draw a trendline for data series 0.
    isStacked: true
  };
  var chartData = google.visualization.arrayToDataTable(data);
  var chart = new google.visualization.ColumnChart(document.getElementById("popup-chart"));
  chart.draw(chartData, options);
}

function toPieChartData(data, yaxis) {
  var result = [];
  result.push(["lable", "value"]);
  yaxis = yaxis.replace(/ /gi, ""); // 모든 공백 제거
  for (var i = 0; i < yaxis.split(",").length; i++) {
    lable = yaxis.split(",")[i];
    value = data[0][lable];
    result.push([lable, value]);
  }
  return result;
}

function drawPieChart(buildingId, yaxis) {
  popup();
  url = "http://localhost:8000/buildinginfo/pie-data/" + buildingId + "/?yaxis=" + yaxis;
  json = getJson(url);
  console.log(json);
  data = toPieChartData(json, yaxis);
  console.log(data);
  var options = {
    title: "연간 현황 차트",
    vAxis: { title: yaxis },
    legend: "none",
    trendlines: {
      0: {
        type: "linear"
      }
    }, // Draw a trendline for data series 0.
    isStacked: true
  };
  var chartData = google.visualization.arrayToDataTable(data);
  var chart = new google.visualization.PieChart(document.getElementById("popup-chart"));
  chart.draw(chartData, options);
}
