function controlNav() {
  if (document.getElementById("sidebar").className == "sidebar-hidden") {
    document.getElementById("sidebar").className = "sidebar";
  } else {
    document.getElementById("sidebar").className = "sidebar-hidden";
  }
}

function toggle() {
  const btn = document.getElementById("toggle-btn");
  if (document.body.className == "light-theme") {
    document.body.className = "";
    btn.innerText = "Toggle Light Mode";
    localStorage.setItem("theme", "dark");
  } else {
    document.body.className = "light-theme";
    localStorage.setItem("theme", "light");
    btn.innerText = "Toggle Dark Mode";
  }
}

window.addEventListener("load", (event) => {
  const currentTheme = localStorage.getItem("theme");
  if (currentTheme == "light") {
    document.body.className = "light-theme";
  } else if (currentTheme == "dark") {
    document.body.className = "";
  }
});