/*
 * Reading-progress favicon for article pages.
 *
 * Draws the site's wave mark with a cyan arc that fills clockwise as you
 * scroll the post. Progressive enhancement: if JS is off or this fails, the
 * static <link rel="icon"> favicons in the <head> are used instead. Only
 * loaded on entry (post) templates.
 */
(function () {
  "use strict";

  var canvas = document.createElement("canvas");
  canvas.width = canvas.height = 32;
  var ctx = canvas.getContext("2d");
  if (!ctx) return; // leave the static favicons in place

  // Take over the icon: drop the static icon links, install one we control.
  var link = document.createElement("link");
  link.rel = "icon";
  link.type = "image/png";
  document.querySelectorAll('link[rel~="icon"]').forEach(function (l) {
    l.parentNode.removeChild(l);
  });
  document.head.appendChild(link);

  function roundRect(x, y, w, h, r) {
    ctx.beginPath();
    ctx.moveTo(x + r, y);
    ctx.arcTo(x + w, y, x + w, y + h, r);
    ctx.arcTo(x + w, y + h, x, y + h, r);
    ctx.arcTo(x, y + h, x, y, r);
    ctx.arcTo(x, y, x + w, y, r);
    ctx.closePath();
  }

  function draw(p) {
    ctx.clearRect(0, 0, 32, 32);
    roundRect(0, 0, 32, 32, 7);
    ctx.fillStyle = "#282a36";
    ctx.fill();

    // JF monogram (Dracula purple), matching favicon.svg.
    ctx.fillStyle = "#bd93f9";
    ctx.font = "700 14px Menlo, 'SF Mono', 'DejaVu Sans Mono', monospace";
    ctx.textAlign = "center";
    ctx.textBaseline = "middle";
    if ("letterSpacing" in ctx) ctx.letterSpacing = "-1.5px";
    ctx.fillText("JF", 16, 17);

    // Progress ring: dim track + cyan arc from 12 o'clock.
    ctx.lineWidth = 2.5;
    ctx.strokeStyle = "#44475a";
    ctx.beginPath();
    ctx.arc(16, 16, 14, 0, Math.PI * 2);
    ctx.stroke();
    if (p > 0) {
      ctx.strokeStyle = "#8be9fd";
      ctx.beginPath();
      ctx.arc(16, 16, 14, -Math.PI / 2, -Math.PI / 2 + p * Math.PI * 2);
      ctx.stroke();
    }

    link.href = canvas.toDataURL("image/png");
  }

  function progress() {
    var doc = document.documentElement;
    var max = doc.scrollHeight - window.innerHeight;
    if (max <= 0) return 0; // post shorter than the viewport
    return Math.min(1, Math.max(0, window.scrollY / max));
  }

  var ticking = false;
  function onScroll() {
    if (ticking) return;
    ticking = true;
    requestAnimationFrame(function () {
      draw(progress());
      ticking = false;
    });
  }

  draw(progress());
  window.addEventListener("scroll", onScroll, { passive: true });
  window.addEventListener("resize", onScroll, { passive: true });
})();
