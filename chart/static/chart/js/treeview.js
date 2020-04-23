function showElement() {
  var eventObj = event.target;
  var targetId = eventObj.getAttribute("target-element");
  var targetEl = document.getElementById(targetId);
  var hide = targetEl.classList.contains("hide");
  if (hide == true) {
    targetEl.classList.remove("hide");
    targetEl.classList.add("show");
    eventObj.classList.remove("fa-folder");
    eventObj.classList.add("fa-folder-open");
  } else if (hide == false) {
    targetEl.classList.remove("show");
    targetEl.classList.add("hide");
    eventObj.classList.remove("fa-folder-open");
    eventObj.classList.add("fa-folder");
  }
}

function closeSideBar() {
  var targetEl = document.getElementById("side-bar");
  var chartArea = document.getElementById("chart-area");
  var thisEl = event.srcElement;
  var icon = thisEl.getElementsByTagName("i")[0] || thisEl;
  console.log(icon);
  if (targetEl.classList.contains("hide")) {
    targetEl.classList.remove("hide");
    targetEl.classList.add("show");
    chartArea.style.maxWidth = "calc(100vw - 250px - 10px)";
    icon.setAttribute("class", "fas fa-caret-left");
  } else {
    targetEl.classList.remove("show");
    targetEl.classList.add("hide");
    chartArea.removeAttribute("style");
    icon.setAttribute("class", "fas fa-caret-right");
  }
  redrawChart();
}

function datapointCheck() {
  var eventObj = event.target;
  var name = eventObj.getAttribute("name");
  var checkPoints = document.getElementsByName(name);

  // branch를 클릭하면 하위의 모든 체크박스가 true 또는 false
  if (eventObj.classList.contains("branch")) {
    if (eventObj.checked == true) {
      for (var i = 0; i < checkPoints.length; i++) {
        var point = checkPoints[i];
        if (point.id.match(eventObj.id)) {
          point.checked = true;
        }
      }
    } else if (eventObj.checked == false) {
      for (var i = 0; i < checkPoints.length; i++) {
        var point = checkPoints[i];
        if (point.id.match(eventObj.id)) {
          point.checked = false;
        }
      }
    }
  }

  // 하위 체크박스 상태에 따라 상위의 체크박스가 true 또는 false가 됨
  var chk = eventObj;
  var depth = chk.getAttribute("depth");
  for (var i = 0; i < depth; i++) {
    if (chk.getAttribute("parent")) {
      var parentName = chk.getAttribute("parent");
      var lenUnchked = document.querySelectorAll('input[parent="' + parentName + '"][type="checkbox"]:not(:checked)')
        .length;
      var parentEl = document.getElementById(parentName);
      if (lenUnchked == 0) {
        parentEl.checked = true;
      } else if (lenUnchked > 0) {
        parentEl.checked = false;
      }
      chk = parentEl;
    }
  }
}
