// Sidebar logic, called by hamburger icon
function controlNav() {
  if (document.getElementById("sidebar").className == "sidebar-hidden") {
    document.getElementById("sidebar").className = "sidebar";
  } else {
    document.getElementById("sidebar").className = "sidebar-hidden";
  }
}

// Toggle dark and light modes, called by theme-btn
function themeToggle() {
  const btn = document.getElementById("toggle-btn");
  if (document.firstElementChild.getAttribute("data-theme") == "light") {
    document.firstElementChild.setAttribute("data-theme", "dark");
    btn.innerText = "Toggle Light Mode";
    localStorage.setItem("theme", "dark");
  } else {
    document.firstElementChild.setAttribute("data-theme", "light");
    btn.innerText = "Toggle Dark Mode";
    localStorage.setItem("theme", "light");
  }
}

// Logic for maintaining OS color theme and overriding theme
// Avoid FOUC by maintaining data-theme attribute on root HTML element
const modeStorageKey = "theme";

const getTheme = () => {
  if (localStorage.getItem(modeStorageKey)) {
    return localStorage.getItem(modeStorageKey);
  } else {
    return window.matchMedia('(prefers-color-scheme: dark)').matches ? 'dark' : 'light';
  }
}

const setTheme = () => {
  document.firstElementChild.setAttribute("data-theme", getTheme());
}

setTheme();