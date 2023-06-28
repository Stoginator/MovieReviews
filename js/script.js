function controlNav() {
  if (document.getElementById("sidenav").className == "sidebar-hidden") {
    document.getElementById("sidenav").className = "sidebar";
    document.getElementById("main").className = "push";
  } else {
    document.getElementById("sidenav").className = "sidebar-hidden";
    document.getElementById("main").className = "no-push";
  }
}