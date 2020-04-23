// 캘린더 구현

function drawCalendar(id) {
  var target = document.getElementById(id);
  target.innerHTML = htmlCalendar();
  updateCal();
}

function htmlCalendar() {
  var cal = '<table id="calendar" style="font-size: 15px; table-layout:fixed;">';
  cal += "<tbody>";
  cal += '<tr id="toolbar">';
  cal += "<td></td>";
  cal +=
    '<td style="text-align: right;" onclick="prevYear()"><span style="cursor: pointer;"><i class="fas fa-chevron-left"></i><i class="fas fa-chevron-left"></i></span></td>';
  cal += '<td onclick="prevMonth()"><span style="cursor: pointer;"><i class="fas fa-chevron-left"></i></span></td>';
  cal += '<td id="tbCalendarYM" year="yyyy" month="mm" style="font-size: 15px; font-weight: bold;">yyyy년 m월</td>';
  cal += '<td onclick="nextMonth()"><span style="cursor: pointer;"><i class="fas fa-chevron-right"></i></span></td>';
  cal +=
    '<td style="text-align: left;" onclick="nextYear()"><span style="cursor: pointer;"><i class="fas fa-chevron-right"></i><i class="fas fa-chevron-right"></i></span></td>';
  cal += "<td></td>";
  cal += "</tr>";
  cal += "<tr>";
  cal += '<td class="weekday">일</td>';
  cal += "<td>월</td>";
  cal += "<td>화</td>";
  cal += "<td>수</td>";
  cal += "<td>목</td>";
  cal += "<td>금</td>";
  cal += "<td>토</td>";
  cal += "</tr>";
  cal += "</tbody>";
  cal += "</table>";
  return cal;
}

function prevMonth() {
  var tbCalendarYM = document.getElementById("tbCalendarYM");
  var year = tbCalendarYM.getAttribute("year");
  var month = tbCalendarYM.getAttribute("month") - 1;
  var date = new Date(year, month - 1);
  updateCal(date);
}

function prevYear() {
  var tbCalendarYM = document.getElementById("tbCalendarYM");
  var year = tbCalendarYM.getAttribute("year");
  var month = tbCalendarYM.getAttribute("month") - 1;
  var date = new Date(year - 1, month);
  updateCal(date);
}

function nextMonth() {
  var tbCalendarYM = document.getElementById("tbCalendarYM");
  var year = tbCalendarYM.getAttribute("year");
  var month = tbCalendarYM.getAttribute("month") - 1;
  var date = new Date(year, month + 1);
  updateCal(date);
}

function nextYear() {
  var tbCalendarYM = document.getElementById("tbCalendarYM");
  var year = parseInt(tbCalendarYM.getAttribute("year")); //convert string to int
  var month = tbCalendarYM.getAttribute("month") - 1;
  var date = new Date(year + 1, month);
  updateCal(date);
}

function updateCal(date) {
  var date = date || new Date();
  var today = new Date();
  var doMonth = new Date(date.getFullYear(), date.getMonth(), 1);
  var lastDate = new Date(date.getFullYear(), date.getMonth() + 1, 0);
  var prevLastDate = new Date(date.getFullYear(), date.getMonth(), 0);
  var nextFirstDate = new Date(date.getFullYear(), date.getMonth() + 1, 1);
  var tbCalendar = document.getElementById("calendar");
  var tbCalendarYM = document.getElementById("tbCalendarYM");
  tbCalendarYM.innerHTML = date.getFullYear() + "년 " + (date.getMonth() + 1) + "월";
  tbCalendarYM.setAttribute("year", date.getFullYear());
  tbCalendarYM.setAttribute("month", date.getMonth() + 1);

  // 캘린더 갱신시 테이블의 일자 row 삭제
  while (tbCalendar.rows.length > 2) {
    tbCalendar.deleteRow(tbCalendar.rows.length - 1);
  }
  var row = null;
  row = tbCalendar.insertRow();
  row.classList.add("week");
  var cnt = 0;

  // 지난달 일자 채우기
  for (var i = 1; i <= doMonth.getDay(); i++) {
    cell = row.insertCell();
    cell.innerHTML = "<font color=lightgrey>" + (prevLastDate.getDate() - doMonth.getDay() + i);
    cell.classList.add("day");
    cell.setAttribute(
      "date",
      prevLastDate.getFullYear() +
        "-" +
        (prevLastDate.getMonth() + 1) +
        "-" +
        (prevLastDate.getDate() - doMonth.getDay() + i)
    );
    if (cnt == 0) {
      cell.id = "start-day";
    }
    cnt = cnt + 1;
  }

  // 이번달 일자 채우기
  for (var i = 1; i <= lastDate.getDate(); i++) {
    cell = row.insertCell();
    cell.innerHTML = i;
    cell.classList.add("day");
    cell.setAttribute("date", date.getFullYear() + "-" + (date.getMonth() + 1) + "-" + i);
    if (cnt == 0) {
      cell.id = "start-day";
    }
    cnt = cnt + 1;

    // today
    if (date.getFullYear() == today.getFullYear() && date.getMonth() == today.getMonth() && i == today.getDate()) {
      cell.bgColor = "#FAF58C";
    }
    // Sunday
    if (cnt % 7 == 1) {
      cell.innerHTML = "<font color=#F79DC2>" + i + "</font>";
    }
    // Saturday
    if (cnt % 7 == 0) {
      cell.innerHTML = "<font color=skyblue>" + i + "</font>";
      if (i != lastDate.getDate()) {
        row = tbCalendar.insertRow();
        row.classList.add("week");
      }
    }
    // next month
    if (i == lastDate.getDate()) {
      for (var j = 1; j < 7 - lastDate.getDay(); j++) {
        cell = row.insertCell();
        cell.innerHTML = "<font color=lightgrey>" + j + "</font>";
        cell.classList.add("day");
        cell.setAttribute("date", nextFirstDate.getFullYear() + "-" + (nextFirstDate.getMonth() + 1) + "-" + j);
      }
    }
  }
  cell.id = "end-day";
}

function addEventPopup() {
  var cal = document.getElementById("calendar");
  var tds = cal.getElementsByTagName("td");
  for (var i = 0; i < tds.length; i++) {
    var td = tds[i];
    td.addEventListener("click", function() {
      addEventForm();
    });
  }
}

function addEventForm() {
  var el = event.srcElement;
  var url = "/scheduler/event/new/?date=" + el.getAttribute("date");
  fetch(url)
    .then(response => {
      return response.text();
    })
    .then(data => {
      modal();
      var content = document.getElementById("modal-content");
      content.innerHTML = data;
    });
}

// 캘린더 내부에 에너지 사용량 차트 구현
function insertEnergyChart(targetId) {
  var target = document.getElementById(targetId);
}
