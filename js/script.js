function controlNav() {
  if (document.getElementById("sidebar").className == "sidebar-hidden") {
    document.getElementById("sidebar").className = "sidebar";
    document.getElementById("main").className = "push";
  } else {
    document.getElementById("sidebar").className = "sidebar-hidden";
    document.getElementById("main").className = "no-push";
  }
}