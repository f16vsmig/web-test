let chartInfo = new Object();

// Load the Visualization API and the corechart package.
google.charts.load("current", { packages: ["corechart"] });

// Set a callback to run when the Google Visualization API is loaded.
// google.charts.setOnLoadCallback(drawLineChart);

function getEndpoints() {
  var checkeds = document.getElementsByClassName("endpoint");
  var result = [];
  for (var i = 0; i < checkeds.length; i++) {
    if (checkeds[i].checked) {
      result.push(checkeds[i].id);
    }
  }
  return result;
}

function getChartData(startDate, endDate, pointsList) {
  var totalJson = {};
  var keys = new Set();
  for (var i = 0; i < pointsList.length; i++) {
    jsonUrl =
      "http://localhost:8000/chart/google-chart-data/?start-day=" +
      startDate +
      "&end-day=" +
      endDate +
      "&datapoint=" +
      pointsList[i];
    json = getJson(jsonUrl);
    totalJson[pointsList[i]] = json;
    Object.keys(json["data"]).forEach(val => keys.add(val));
  }
  return convertJsonforChart(totalJson, keys);
}

function convertJsonforChart(totalJson, dateKeys) {
  var chartJson = {};
  chartJson["cols"] = [{ id: "timestamp", label: "timestamp", type: "datetime" }];
  for (var i = 0; i < Object.keys(totalJson).length; i++) {
    buildingKey = Object.keys(totalJson)[i];
    chartJson["cols"].push(totalJson[buildingKey]["prop"]);
  }
  chartJson["rows"] = [];

  dateKeys.forEach(val => {
    var newRow = { c: [{ v: val }] };
    for (var j = 0; j < Object.keys(totalJson).length; j++) {
      buildingKey = Object.keys(totalJson)[j];

      if (typeof totalJson[buildingKey]["data"][val] != "undefined") {
        newRow["c"].push({ v: totalJson[buildingKey]["data"][val] });
      } else {
        newRow["c"].push({ v: null });
      }
    }
    chartJson["rows"].push(newRow);
  });
  return chartJson;
}

function decodeChartData(chartJson) {
  var totalJson = {};
  // prop add
  chartJson["cols"].slice(1).forEach(val => {
    var id = val["id"];
    var label = val["label"];
    totalJson[id] = {};
    totalJson[id].prop = {};
    totalJson[id].prop.id = id;
    totalJson[id].prop.label = label;
    totalJson[id].prop.type = "number";
    totalJson[id].data = {};
  });
  // data add
  for (var i = 0; i < chartJson["rows"].length; i++) {
    var row = chartJson["rows"][i];
    var datetime = row["c"][0]["v"];
    for (var j = 1; j < row["c"].length; j++) {
      var value = row["c"][j]["v"];
      var id = chartJson["cols"][j]["id"];
      totalJson[id].data[datetime] = value;
    }
  }

  return totalJson;
}

function getChartColors(targetDiv, endpoints) {
  if (targetDiv.getAttribute("colors") == null) {
    var colors = [];
    var letters = "0123456789ABCDEF";
    for (var i = 0; i < endpoints.length; i++) {
      var color = "#";
      for (var j = 0; j < 6; j++) {
        color += letters[Math.floor(Math.random() * 16)];
      }
      colors.push(color);
    }
    targetDiv.setAttribute("colors", colors); // 선택된 컬러를 차트 Div에 속성에 기록
    return colors;
  } else {
    return targetDiv.getAttribute("colors").split(",");
  }
}

function getTicksofHaxis(startDay, endDay) {
  var ticks = [];
  var parsed = startDay.split("-");
  var startTick = new Date(parsed[0], parsed[1] - 1, parsed[2]);
  var parsedEnd = endDay.split("-");
  var endTick = new Date(parsedEnd[0], parsedEnd[1], parsedEnd[2]);
  while (startTick < endTick) {
    var year = startTick.getFullYear();
    var month = startTick.getMonth();
    var date = startTick.getDate();
    var tick = new Date(year, month, date);
    ticks.push(tick);
    startTick.setDate(date + 1);
  }
  console.log(ticks);
  return ticks;
}

function drawLineChart(targetDiv, startDay, endDay, endpoints) {
  var jsonData = getChartData(startDay, endDay, endpoints);
  var colors = getChartColors(targetDiv, endpoints);
  var options = {
    chartArea: {
      top: 30,
      right: 200,
      left: 60,
      bottom: 30
    },
    legend: {
      textStyle: {
        fontSize: 14
      }
    },
    tooltip: {
      isHtml: true,
      trigger: "both" // focus/selection/both/none. 마우스오버로 커스텀 하기 위해 none 설정
    },
    interpolateNulls: false, // boolean, 중간에 빈 데이터 자동 지정
    focusTarget: "category",
    // aggregationTarget: "series",
    crosshair: {
      trigger: "both",
      orientation: "vertical"
    },
    explorer: {
      actions: ["dragToZoom", "rightClickToReset"],
      axis: "horizontal",
      keepInBounds: true,
      maxZoomIn: 0.01
      // zoomDelta: 0.1
    },
    colors: colors,
    fontSize: 12,
    hAxis: {
      format: "M/d",
      slantedText: true,
      gridlines: { count: 3 },
      ticks: getTicksofHaxis(startDay, endDay),
      viewWindowMode: "maximized"
    },
    enableInteractivity: true

    // sort: "event",
    // sortColumn: 0,
    // sortAscending: true
  };

  // 건물이 다르면 대시 옵션 변경
  var series = { 0: { lineDashStyle: [5, 0] } };
  for (var i = 1; i < endpoints.length; i++) {
    var buildingId = endpoints[i].split("-")[0];
    var preBuildingId = endpoints[i - 1].split("-")[0];
    if (buildingId != preBuildingId) {
      var addDash = [2, 2];
      var newDash = series[i - 1]["lineDashStyle"].concat(addDash);
      series[i] = { lineDashStyle: newDash };
    } else {
      series[i] = series[i - 1];
    }
  }
  options["series"] = series;

  // json을 dataTable 변환
  var data = new google.visualization.DataTable(jsonData);
  // timestamp를 오름차순으로 정렬
  data.sort({ column: 0 });
  // tooltip의 date format 변경
  var date_formatter = new google.visualization.DateFormat({
    pattern: "yyyy/MM/dd, HH:mm"
  });
  date_formatter.format(data, 0); // Where 0 is the index of the column
  // 차트 그리기
  var chart = new google.visualization.LineChart(targetDiv);
  chart.draw(data, options);

  // 차트 정보를 data를 전역변수 globalChartData에 저장
  var chartId = targetDiv.getAttribute("id");
  chartInfo[chartId] = {
    chart: chart,
    data: data,
    options: options,
    endpoints: endpoints
  };
}

function appendChart() {
  var eventObj = event.target;
  var targetDiv = eventObj.parentElement;

  var startDay = document.getElementById("startDay").value;
  var endDay = document.getElementById("endDay").value;
  var endpoints = getEndpoints();
  if (startDay == "") {
    alert("시작일을 지정하세요.");
  } else if (endDay == "") {
    alert("최종일을 지정하세요.");
  } else if (endpoints == "") {
    alert("데이터포인트를 선택하세요.");
  } else {
    drawLineChart(targetDiv, startDay, endDay, endpoints);
  }
}

function redrawChart() {
  Object.values(chartInfo).forEach(val => {
    var chart = val["chart"];
    var data = val["data"];
    var option = val["options"];
    chart.draw(data, option);
  });
}

function updateCharts() {
  var startDay = document.getElementById("startDay").value;
  var endDay = document.getElementById("endDay").value;
  Object.values(chartInfo).forEach(val => {
    var chart = val["chart"];
    var jsonData = getChartData(startDay, endDay, val["endpoints"]);
    var data = new google.visualization.DataTable(jsonData);
    var options = val["options"];
    chart.draw(data, options);
  });
}

function addChartDiv() {
  var chartDiv = document.createElement("div");
  chartDiv.setAttribute("class", "chart item-flex-1-1-0 flex-xy-center");

  var exChartDivs = document.getElementsByClassName("chart");
  var newChartDivId = function() {
    var lastChartDiv = exChartDivs[exChartDivs.length - 1];
    var newIdNo = Number(lastChartDiv.getAttribute("id").split("-")[1]) + 1;
    return "chart-" + newIdNo;
  };
  chartDiv.setAttribute("id", newChartDivId());

  var draw = document.createElement("a");
  draw.setAttribute("class", "draw-chart fas fa-plus-circle fa-2x decoration-none");
  draw.setAttribute("href", "javascript:void(0)");
  draw.setAttribute("onclick", "appendChart()");

  chartDiv.appendChild(draw);

  var container = document.getElementById("charts-container");
  container.appendChild(chartDiv);

  redrawChart(); // 차트 추가시 redraw
}

function selectToday() {
  var today = new Date();
  document.getElementById("startDay").value = today.toISOString().slice(0, 10); // yyyy-mm-dd
  document.getElementById("endDay").value = today.toISOString().slice(0, 10);
}

function selectPeriod(months) {
  var today = new Date();
  var startDay = new Date();
  startDay.setMonth(today.getMonth() + months);
  document.getElementById("endDay").value = today.toISOString().slice(0, 10);
  document.getElementById("startDay").value = startDay.toISOString().slice(0, 10);
}

function syncCharts() {
  var eventObj = event.target;
  if (eventObj.classList.contains("active")) {
    eventObj.classList.remove("active");
    Object.values(chartInfo).forEach(val => {
      var chart = val["chart"];
      google.visualization.events.removeAllListeners(chart);
    });
  } else {
    eventObj.classList.add("active");
    Object.values(chartInfo).forEach(val => {
      var chart = val["chart"];
      // var chartData = val["data"];
      google.visualization.events.removeAllListeners(chart);
      Object.values(chartInfo).forEach(valT => {
        var toChart = valT["chart"];
        // var toChartData = valT["data"];
        if (chart != toChart) {
          google.visualization.events.addListener(chart, "onmouseover", function(properties) {
            toChart.setSelection([properties]);
          });
          google.visualization.events.addListener(chart, "onmouseout", function() {
            chart.setSelection();
            toChart.setSelection();
          });
        }
      });
    });
    syncChartData();
    redrawChart();
  }
}

function convertDateFormat(dateString) {
  var datetime = new Date(Date.parse(dateString));
  var year = datetime.getFullYear();
  var month = datetime.getMonth();
  var day = datetime.getDate();
  var hour = datetime.getHours();
  var minute = datetime.getMinutes();
  var seconds = datetime.getSeconds();
  return "Date(" + year + ", " + month + ", " + day + ", " + hour + ", " + minute + ", " + seconds + ")";
}

function dataTableToJson(dataTable) {
  var json = {};
  // prop add
  dataTable.data.vg.slice(1).forEach(val => {
    var id = val["id"];
    var label = val["label"];
    var type = val["type"];
    json[id] = {};
    json[id].data = {}; // 다음 루프에서 추가할 데이터의 공간을 만든다.
    json[id].prop = {};
    json[id].prop.id = id;
    json[id].prop.label = label;
    json[id].prop.type = type;
  });

  // data add
  dataTable.data.wg.forEach(val => {
    var key = convertDateFormat(val.c[0].v);
    for (var i = 1; i < val.c.length; i++) {
      var value = val.c[i].v;
      var id = dataTable.data.vg[i].id;
      json[id].data[key] = value;
    }
  });
  // for (var i = 0; i < dataTable.data.wg.length; i++) {
  //   var row = dataTable.data.wg[i];
  //   var key = convertDateFormat(row.c[0].v);
  //   for (var j = 1; j < row.c.length; j++) {
  //     var value = row.c[j].v;
  //     var id = dataTable.data.vg[j].id;
  //     json[id].data[key] = value;
  //   }
  // }
  return json;
}

function syncChartData() {
  //
  var totalJson = {};
  Object.entries(chartInfo).forEach(([key, val]) => {
    totalJson[key] = dataTableToJson(val);
  });
  //
  var keys = new Set();
  Object.values(totalJson).forEach(val => {
    Object.values(val).forEach(v => {
      Object.keys(v.data).forEach(v_ => {
        keys.add(v_);
      });
    });
  });
  var keysSorted = Array.from(keys);
  Object.entries(totalJson).forEach(([key, val]) => {
    var newChartJson = convertJsonforChart(val, keysSorted);
    var dataTable = new google.visualization.DataTable(newChartJson);
    dataTable.sort({ column: 0 });
    chartInfo[key].data = dataTable;
  });
}

// 브라우저 창 크기가 바뀌면 차트 redraw 이벤트 등록
window.onresize = function() {
  redrawChart();
};
