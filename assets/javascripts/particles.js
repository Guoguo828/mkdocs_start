/**
 * 粒子背景配置（particles.js 兼容模式）
 * - 浮动小圆点 + 连线
 * - 跟随深浅主题自动切换颜色
 * - 尊重 prefers-reduced-motion
 */
(function () {
  "use strict";

  /* ── 主题配色 ── */
  var THEMES = {
    "default": {
      particles:  { color: "#0f766e", opacity: 0.35 },
      lineLinked: { color: "#0f766e", opacity: 0.15 }
    },
    "slate": {
      particles:  { color: "#2cb8a9", opacity: 0.30 },
      lineLinked: { color: "#2cb8a9", opacity: 0.12 }
    }
  };

  /* ── 获取当前主题 ── */
  function getScheme() {
    var el = document.querySelector("[data-md-color-scheme]");
    return (el && el.getAttribute("data-md-color-scheme")) || "default";
  }

  /* ── 构建配置 ── */
  function buildConfig(scheme) {
    var t = THEMES[scheme] || THEMES["default"];
    return {
      particles: {
        number:          { value: 45, density: { enable: true, value_area: 1200 } },
        color:           { value: t.particles.color },
        shape:           { type: "circle" },
        opacity:         { value: t.particles.opacity, random: true, anim: { enable: true, speed: 0.4, opacity_min: 0.1, sync: false } },
        size:            { value: 3, random: true, anim: { enable: true, speed: 1.2, size_min: 1, sync: false } },
        line_linked:     { enable: true, distance: 150, color: t.lineLinked.color, opacity: t.lineLinked.opacity, width: 1 },
        move:            { enable: true, speed: 0.6, direction: "none", random: true, straight: false, out_mode: "out" }
      },
      interactivity: {
        detect_on: "window",
        events:    { onhover: { enable: true, mode: "grab" }, resize: true },
        modes:     { grab: { distance: 140, line_linked: { opacity: 0.35 } } }
      },
      retina_detect: true
    };
  }

  /* ── 初始化 ── */
  function init() {
    if (window.matchMedia("(prefers-reduced-motion: reduce)").matches) return;
    if (typeof particlesJS === "undefined") return;

    var scheme = getScheme();
    particlesJS("tsparticles", buildConfig(scheme));

    /* 监听主题切换 */
    var observer = new MutationObserver(function () {
      var el = document.getElementById("tsparticles");
      if (el) el.innerHTML = "";
      particlesJS("tsparticles", buildConfig(getScheme()));
    });
    observer.observe(document.documentElement, {
      attributes: true,
      attributeFilter: ["data-md-color-scheme"]
    });
  }

  if (document.readyState === "loading") {
    document.addEventListener("DOMContentLoaded", init);
  } else {
    init();
  }
})();
