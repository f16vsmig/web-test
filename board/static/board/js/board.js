function postComment(formEl) {
  event.preventDefault();

  if (formEl == undefined) {
    var thisEl = event.srcElement;
    formEl = thisEl.parentElement;
  }

  if (formEl.getElementsByTagName("textarea")[0].value == "") {
    return alert("내용을 입력하세요");
  }

  fetch(formEl.action, {
    method: "POST",
    body: new URLSearchParams(new FormData(formEl))
  }).then(resp => {
    document.location.reload(true);
  });
}

function deleteComment(formEl) {
  event.preventDefault();

  var con = confirm("삭제할까요?");
  if (con == false) {
    return;
  }

  if (formEl == undefined) {
    var thisEl = event.srcElement;
    formEl = thisEl.parentElement;
  }

  fetch(formEl.action, {
    method: "POST",
    body: new URLSearchParams(new FormData(formEl))
  }).then(resp => {
    document.location.reload(true);
  });
}

function createSubCommentForm(target) {
  var subCommentForm = document.getElementById("sub-comment");
  if (subCommentForm != null) {
    var text = subCommentForm.getElementsByTagName("textarea")[0];
    console.log(text.value);
    if (text.value != "") {
      var con = confirm("작성 중인 댓글이 삭제됩니다. 괜찮습니까?");
      if (con == false) {
        return;
      }
    }
    subCommentForm.remove();
  }

  var thisEl = event.srcElement;
  var commentId = thisEl.getAttribute("comment-id");
  var target = document.getElementById(commentId);

  var form = document.createElement("form");
  form.classList.add("flex");
  form.classList.add("m-2");
  form.id = "sub-comment";
  form.method = "POST";
  form.action = "/board/subcomment/new/?id=" + commentId;

  var input = document.createElement("input");
  input.type = "hidden";
  input.name = "csrfmiddlewaretoken";
  input.value = token;

  var textarea = document.createElement("textarea");
  textarea.classList.add("comment-area");
  textarea.name = "subcomment-text";
  textarea.id = "id_subcomment-text";
  textarea.required = true;

  var button = document.createElement("input");
  button.classList.add("comment-button");
  button.type = "submit";
  button.onclick = function() {
    postComment();
  };
  button.value = "대댓글쓰기";

  form.appendChild(input);
  form.appendChild(textarea);
  form.appendChild(button);

  target.append(form);

  textarea.focus();
}

function postDelete(formEl) {
  event.preventDefault();

  var con = confirm("삭제하시겠습니까?");
  if (con == false) {
    return;
  }

  if (formEl == undefined) {
    var thisEl = event.srcElement;
    formEl = thisEl.parentElement;
  }

  fetch(formEl.action, {
    method: "POST",
    body: new URLSearchParams(new FormData(formEl))
  }).then(resp => {
    location.replace(document.referrer);
  });
}
