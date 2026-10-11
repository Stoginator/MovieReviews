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

// Logic for photo carousels (supports any number per page)
document.addEventListener('DOMContentLoaded', () => {
  document.querySelectorAll('.carousel-container').forEach(container => {
    const slides = container.querySelector('.carousel-slides');
    const total = container.querySelectorAll('.carousel-slide').length;
    const dotsContainer = container.querySelector('.carousel-dots');
    let index = 0;

    for (let i = 0; i < total; i++) {
      const dot = document.createElement('span');
      dot.className = 'carousel-dot' + (i === 0 ? ' active' : '');
      dotsContainer.appendChild(dot);
    }
    const dots = dotsContainer.querySelectorAll('.carousel-dot');

    function update() {
      slides.style.transform = `translateX(-${index * 100}%)`;
      dots.forEach((d, i) => d.classList.toggle('active', i === index));
    }

    container.querySelector('.carousel-left').onclick = () => {
      index = (index - 1 + total) % total;
      update();
    };
    container.querySelector('.carousel-right').onclick = () => {
      index = (index + 1) % total;
      update();
    };

    // Touch swipe support
    let startX = 0;
    slides.addEventListener('touchstart', e => startX = e.touches[0].clientX);
    slides.addEventListener('touchend', e => {
      const diff = e.changedTouches[0].clientX - startX;
      if (diff > 50) index = (index - 1 + total) % total;
      else if (diff < -50) index = (index + 1) % total;
      update();
    });
  });
});