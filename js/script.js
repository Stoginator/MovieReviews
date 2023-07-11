function controlNav() {
  if (document.getElementById("sidebar").className == "sidebar-hidden") {
    document.getElementById("sidebar").className = "sidebar";
  } else {
    document.getElementById("sidebar").className = "sidebar-hidden";
  }
}

function toggle() {
  console.log("HERE");
  if (document.body.className == "light-theme") {
    document.body.className = "";
  } else {
    document.body.className = "light-theme";
  }
}

