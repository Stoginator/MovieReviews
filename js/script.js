function controlNav() {
  if (document.getElementById("sidebar").className == "sidebar-hidden") {
    document.getElementById("sidebar").className = "sidebar";
  } else {
    document.getElementById("sidebar").className = "sidebar-hidden";
  }
}

function themeToggle() {
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
  const btn = document.getElementById("toggle-btn");
  const currentTheme = localStorage.getItem("theme");
  if (currentTheme == "light") {
    document.body.className = "light-theme";
    btn.innerText = "Toggle Dark Mode";
  } else if (currentTheme == "dark") {
    document.body.className = "";
    btn.innerText = "Toggle Light Mode";
  }
});