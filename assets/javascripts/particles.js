/**
 * tsParticles 粒子背景配置
 * - 浮动小圆点 + 连线
 * - 跟随深浅主题自动切换颜色
 * - 尊重 prefers-reduced-motion
 */
(function () {
  "use strict";

  /* ── 主题配色 ── */
  var THEMES = {
    "default": {
      dot:    "rgba(15, 118, 110, 0.35)",
      line:   "rgba(15, 118, 110, 0.12)",
      bg:     "transparent"
    },
    "slate": {
      dot:    "rgba(44, 184, 169, 0.30)",
      line:   "rgba(44, 184, 169, 0.10)",
      bg:     "transparent"
    }
  };

  /* ── 获取当前主题 ── */
  function getScheme() {
    var el = document.querySelector("[data-md-color-scheme]");
    return (el && el.getAttribute("data-md-color-scheme")) || "default";
  }

  /* ── 构建配置 ── */
  function buildOptions(scheme) {
    var t = THEMES[scheme] || THEMES["default"];
    return {
      fullScreen: false,
      background: { color: t.bg },
      fpsLimit: 60,
      detectRetina: true,
      particles: {
        number: {
          value: 45,
          density: { enable: true, area: 1200 }
        },
        color: { value: t.dot },
        shape: { type: "circle" },
        opacity: {
          value: { min: 0.15, max: 0.45 },
          animation: {
            enable: true,
            speed: 0.4,
            minimumValue: 0.1,
            sync: false
          }
        },
        size: {
          value: { min: 1.5, max: 3.5 },
          animation: {
            enable: true,
            speed: 1.2,
            minimumValue: 1,
            sync: false
          }
        },
        links: {
          enable: true,
          distance: 150,
          color: t.line,
          opacity: 0.4,
          width: 1
        },
        move: {
          enable: true,
          speed: 0.6,
          direction: "none",
          random: true,
          straight: false,
          outModes: { default: "out" }
        }
      },
      interactivity: {
        events: {
          onHover: {
            enable: true,
            mode: "grab"
          },
          resize: true
        },
        modes: {
          grab: {
            distance: 140,
            links: {
              opacity: 0.35,
              color: t.line
            }
          }
        }
      }
    };
  }

  /* ── 初始化 ── */
  async function init() {
    /* 减弱动效模式：跳过粒子 */
    if (window.matchMedia("(prefers-reduced-motion: reduce)").matches) return;

    var container = document.getElementById("tsparticles");
    if (!container) return;

    /* 加载 slim bundle */
    await loadSlim(tsParticles);

    /* 当前主题 */
    var scheme = getScheme();
    await tsParticles.load({ id: "tsparticles", options: buildOptions(scheme) });

    /* 监听主题切换（Material for MkDocs 通过 data-md-color-scheme 变化触发） */
    var observer = new MutationObserver(function () {
      var newScheme = getScheme();
      tsParticles.load({ id: "tsparticles", options: buildOptions(newScheme) });
    });
    observer.observe(document.documentElement, {
      attributes: true,
      attributeFilter: ["data-md-color-scheme"]
    });

    /* MkDocs Material instant loading：页面切换时重新加载 */
    if (typeof document$ !== "undefined") {
      document$.subscribe(function () {
        var s = getScheme();
        tsParticles.load({ id: "tsparticles", options: buildOptions(s) });
      });
    }
  }

  /* ── 入口 ── */
  if (document.readyState === "loading") {
    document.addEventListener("DOMContentLoaded", init);
  } else {
    init();
  }
})();
