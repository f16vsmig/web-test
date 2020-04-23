// json 호출
function getJson(url) {
  var resp = "";
  var xmlHttp;
  xmlHttp = new XMLHttpRequest();
  if (xmlHttp != null) {
    xmlHttp.open("GET", url, false);
    xmlHttp.send(null);
    var response = xmlHttp.responseText;
    console.log(response);
    if (response == "") {
      return alert("응답하지 않습니다.");
    }
    resp = JSON.parse(response);
  }
  if (resp == "") {
    return alert("데이터가 없습니다.");
  }
  return resp;
}

// document.addEventListener(
//   "click",
//   function(e) {
//     e = e || window.event;
//     var target = e.target || e.srcElement,
//       text = target.textContent || target.innerText;
//     console.log(target);
//   },
//   false
// );

function post(el) {
  event.preventDefault();
  var con = confirm("등록할까요?");
  if (con == true) {
    pass;
  } else {
    return false;
  }
  var url = el.action;
  fetch(url, {
    method: "POST",
    body: new URLSearchParams(new FormData(el))
  }).then(location.reload());
}

function modal() {
  document.body.style.overflow = "hidden";
  var parent = document.getElementById("wrap");
  var modal = document.createElement("div");
  parent.appendChild(modal);
  modal.id = "modal";
  modal.style.width = "100vw";
  modal.style.height = "100vh";
  modal.style.position = "fixed";
  modal.style.top = "0";
  modal.style.left = "0";
  modal.style.zIndex = "9999";
  modal.style.background = "rgba(0,0,0,0.7)";
  modal.classList.add("flex-xy-center");

  var container = document.createElement("div");
  container.style.background = "white";
  container.classList.add("p-3");

  var head = document.createElement("div");
  head.style.textAlign = "right";
  head.classList.add("flex-x-between");

  var title = document.createElement("h1");
  title.innerHTML = "등록하기";
  title.classList.add("mt-0");

  var close = document.createElement("a");
  close.href = "javascript:void(0)";
  close.classList = "decoration-none";
  close.innerHTML = '<i class="fas fa-times fa-2x"></i>';
  head.appendChild(title);
  head.appendChild(close);
  container.appendChild(head);

  var content = document.createElement("div");
  content.id = "modal-content";
  // content.style.background = "white";
  // content.style.width = "60vw";
  // content.style.height = "60vh";
  container.appendChild(content);

  modal.appendChild(container);

  close.addEventListener("click", function() {
    modal.remove();
    document.body.style.overflow = "auto";
  });
}

function popupForm() {
  event.preventDefault();

  var url = event.srcElement.href;

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

function postForm() {
  event.preventDefault();
  var thisEl = event.srcElement;
  var form = thisEl.closest("form");
  var url = form.action;
  fetch(url, {
    method: "POST",
    body: new URLSearchParams(new FormData(form))
  }).then(response => {
    if (response.status == 204) {
      location.reload();
    } else {
      alert("오류가 있습니다. 다시 시도하세요.");
    }
  });
}
