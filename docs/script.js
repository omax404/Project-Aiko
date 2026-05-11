const root = document.documentElement;
const body = document.body;
const cover = document.querySelector("#cover-wrap");
const floatTarget = document.querySelector("[data-float]");
const motionToggle = document.querySelector("#motion-toggle");
const themeToggle = document.querySelector("#theme-toggle");

let motionEnabled = true;

function setMotion(enabled) {
  motionEnabled = enabled;
  body.classList.toggle("no-motion", !enabled);
  motionToggle?.setAttribute("aria-pressed", String(enabled));
}

function setTheme(isDark) {
  root.classList.toggle("light", !isDark);
  themeToggle?.setAttribute("aria-pressed", String(isDark));
  themeToggle?.querySelector("span")?.replaceChildren(document.createTextNode(isDark ? "☾" : "☀"));
}

motionToggle?.addEventListener("click", () => setMotion(!motionEnabled));
themeToggle?.addEventListener("click", () => setTheme(root.classList.contains("light")));

window.addEventListener("pointermove", (event) => {
  if (!motionEnabled || !cover || !floatTarget) return;

  const centerX = window.innerWidth / 2;
  const centerY = window.innerHeight / 2;
  const x = (event.clientX - centerX) / centerX;
  const y = (event.clientY - centerY) / centerY;

  cover.style.setProperty("--parallax-x", `${x * 16}px`);
  cover.style.setProperty("--parallax-y", `${y * -16}px`);
  floatTarget.style.transform = `translate3d(${x * 6}px, ${y * 6}px, 0)`;
});

window.addEventListener("pointerleave", () => {
  if (!cover || !floatTarget) return;
  cover.style.setProperty("--parallax-x", "0px");
  cover.style.setProperty("--parallax-y", "0px");
  floatTarget.style.transform = "translate3d(0, 0, 0)";
});
