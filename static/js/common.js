// json 호출
function getjson(url) {
    var resp = '';
    var xmlHttp ;
    xmlHttp = new XMLHttpRequest();
    if(xmlHttp != null) {
      xmlHttp.open("GET", url, false);
      xmlHttp.send(null);
      resp = JSON.parse(xmlHttp.responseText);
    };
    return resp;
};


