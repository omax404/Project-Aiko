const terminal = document.querySelector("#terminal-text");
const lines = [
  "boot://aiko.neural_core",
  "status: link established",
  "memory: episodic + semantic recall online",
  "emotion: affection stable, curiosity rising",
  "voice: local synthesis ready",
  "agency: proactive loop listening",
];

let currentLine = 0;
let currentChar = 0;

function typeTerminal() {
  if (!terminal) return;
  const text = lines
    .slice(0, currentLine)
    .concat(lines[currentLine]?.slice(0, currentChar) || [])
    .join("\n");
  terminal.textContent = `${text}${currentLine < lines.length ? "_" : ""}`;

  if (currentLine >= lines.length) {
    setTimeout(() => {
      currentLine = 0;
      currentChar = 0;
      typeTerminal();
    }, 2600);
    return;
  }

  currentChar += 1;
  if (currentChar > lines[currentLine].length) {
    currentLine += 1;
    currentChar = 0;
    setTimeout(typeTerminal, 360);
    return;
  }

  setTimeout(typeTerminal, 34 + Math.random() * 26);
}

typeTerminal();

const revealObserver = new IntersectionObserver(
  (entries) => {
    entries.forEach((entry) => {
      if (entry.isIntersecting) entry.target.classList.add("is-visible");
    });
  },
  { threshold: 0.16 }
);

document.querySelectorAll(".reveal").forEach((node) => revealObserver.observe(node));

const canvas = document.querySelector("#signal-canvas");
const ctx = canvas?.getContext("2d");
let dots = [];
let width = 0;
let height = 0;
let pointerX = 0;
let pointerY = 0;

function resizeCanvas() {
  if (!canvas || !ctx) return;
  const ratio = Math.min(window.devicePixelRatio || 1, 2);
  width = window.innerWidth;
  height = window.innerHeight;
  canvas.width = Math.floor(width * ratio);
  canvas.height = Math.floor(height * ratio);
  canvas.style.width = `${width}px`;
  canvas.style.height = `${height}px`;
  ctx.setTransform(ratio, 0, 0, ratio, 0, 0);

  const count = Math.min(86, Math.max(44, Math.floor(width / 18)));
  dots = Array.from({ length: count }, (_, index) => ({
    x: Math.random() * width,
    y: Math.random() * height,
    vx: (Math.random() - 0.5) * 0.26,
    vy: (Math.random() - 0.5) * 0.22,
    hue: index % 3,
  }));
}

function renderSignals() {
  if (!ctx) return;
  ctx.clearRect(0, 0, width, height);

  dots.forEach((dot, index) => {
    dot.x += dot.vx;
    dot.y += dot.vy;

    if (dot.x < -20) dot.x = width + 20;
    if (dot.x > width + 20) dot.x = -20;
    if (dot.y < -20) dot.y = height + 20;
    if (dot.y > height + 20) dot.y = -20;

    const dx = dot.x - pointerX;
    const dy = dot.y - pointerY;
    const pointerDistance = Math.hypot(dx, dy);
    if (pointerDistance < 120 && pointerDistance > 0) {
      dot.x += dx / pointerDistance;
      dot.y += dy / pointerDistance;
    }

    for (let j = index + 1; j < dots.length; j += 1) {
      const other = dots[j];
      const distance = Math.hypot(dot.x - other.x, dot.y - other.y);
      if (distance < 128) {
        ctx.strokeStyle = `rgba(255, 139, 189, ${0.11 - distance / 1500})`;
        ctx.lineWidth = 1;
        ctx.beginPath();
        ctx.moveTo(dot.x, dot.y);
        ctx.lineTo(other.x, other.y);
        ctx.stroke();
      }
    }

    const fill =
      dot.hue === 0 ? "rgba(255,79,155,0.75)" : dot.hue === 1 ? "rgba(99,231,255,0.65)" : "rgba(214,255,114,0.55)";
    ctx.fillStyle = fill;
    ctx.fillRect(dot.x, dot.y, 2, 2);
  });

  requestAnimationFrame(renderSignals);
}

window.addEventListener("resize", resizeCanvas);
window.addEventListener("pointermove", (event) => {
  pointerX = event.clientX;
  pointerY = event.clientY;
});

resizeCanvas();
renderSignals();
