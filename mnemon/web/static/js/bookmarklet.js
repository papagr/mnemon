(function () {
    function callback() {
    	if (!location.href.startsWith("%(home_url)s")) {
	        $.post("%(home_url)s", {
	            url: location.href,
	            token: "%(security_token)s"
	        })
    	}
    }
    var s = document.createElement("script");
    s.src = "%(jquery_url)s";
    if (s.addEventListener) {
        s.addEventListener("load", callback, false)
    } else if (s.readyState) {
        s.onreadystatechange = callback
    }
    document.body.appendChild(s);
})()