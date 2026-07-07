(function () {
  "use strict";

  function storageKey() {
    return "gxy-site-liked:" + location.pathname;
  }

  function setLikeState(button, liked) {
    var count = document.querySelector("[data-site-like-count]");
    button.setAttribute("aria-pressed", liked ? "true" : "false");
    button.classList.toggle("site-like__button--active", liked);
    if (count) count.textContent = liked ? "1" : "0";
  }

  function burst(button) {
    if (window.matchMedia("(prefers-reduced-motion: reduce)").matches) return;
    for (var i = 0; i < 8; i += 1) {
      var bit = document.createElement("span");
      bit.className = "site-like__burst";
      bit.style.setProperty("--site-like-x", Math.cos((Math.PI * 2 * i) / 8).toFixed(3));
      bit.style.setProperty("--site-like-y", Math.sin((Math.PI * 2 * i) / 8).toFixed(3));
      button.appendChild(bit);
      window.setTimeout(function (node) {
        node.remove();
      }, 650, bit);
    }
  }

  function initLikeButton() {
    var button = document.querySelector("[data-site-like]");
    if (!button || button.dataset.ready === "true") return;

    button.dataset.ready = "true";
    setLikeState(button, localStorage.getItem(storageKey()) === "1");

    button.addEventListener("click", function () {
      var liked = button.getAttribute("aria-pressed") !== "true";
      if (liked) {
        localStorage.setItem(storageKey(), "1");
        burst(button);
      } else {
        localStorage.removeItem(storageKey());
      }
      setLikeState(button, liked);
    });
  }

  function calculateReadingTime() {
    var oldLabel = document.querySelector(".reading-time-label");
    if (oldLabel) oldLabel.remove();

    var article = document.querySelector(".md-content__inner");
    if (!article) return;

    var text = article.innerText || article.textContent || "";
    var cnWords = (text.match(/[一-龥]/g) || []).length;
    var enWords = (text.replace(/[一-龥]/g, "").match(/\b\w+\b/g) || []).length;
    var totalWords = cnWords + enWords;
    if (totalWords <= 20) return;

    var h1 = article.querySelector("h1");
    if (!h1) return;

    var label = document.createElement("p");
    label.className = "reading-time-label";
    label.innerHTML = "预计阅读时长 <b>" + Math.ceil(totalWords / 300) + " 分钟</b> · 约 " + totalWords + " 字";
    h1.parentNode.insertBefore(label, h1.nextSibling);
  }

  /* ── 阅读进度条 ── */
  function initReadingProgress() {
    var bar = document.querySelector(".reading-progress");
    if (!bar) {
      bar = document.createElement("div");
      bar.className = "reading-progress";
      document.body.appendChild(bar);
    }

    function updateProgress() {
      var scrollTop = window.scrollY || document.documentElement.scrollTop;
      var docHeight = document.documentElement.scrollHeight - document.documentElement.clientHeight;
      var progress = docHeight > 0 ? (scrollTop / docHeight) * 100 : 0;
      bar.style.width = progress.toFixed(1) + "%";
    }

    window.addEventListener("scroll", updateProgress, { passive: true });
    updateProgress();
  }

  /* ── 键盘快捷键 ── */
  function initKeyboardShortcuts() {
    document.addEventListener("keydown", function (e) {
      /* / 聚焦搜索（不拦截输入框内的按键） */
      if (e.key === "/" && !isTextInput(e.target)) {
        e.preventDefault();
        var searchInput = document.querySelector(".md-search__input");
        if (searchInput) searchInput.focus();
      }

      /* Esc 关闭搜索 */
      if (e.key === "Escape") {
        var searchInput = document.querySelector(".md-search__input");
        if (searchInput && document.activeElement === searchInput) {
          searchInput.blur();
          var closeBtn = document.querySelector(".md-search__icon");
          if (closeBtn) closeBtn.click();
        }
      }
    });
  }

  function isTextInput(el) {
    var tag = el.tagName;
    return tag === "INPUT" || tag === "TEXTAREA" || tag === "SELECT" || el.isContentEditable;
  }

  /* ── 点击气泡特效 ── */
  function initClickBubbles() {
    if (window.matchMedia("(prefers-reduced-motion: reduce)").matches) return;

    var BUBBLE_COUNT = 6;
    var COLORS_LIGHT = ["#0f9f8f", "#0b7a86", "#2fb9d1", "#55e0ce", "#065d67", "#97f0ff"];
    var COLORS_DARK  = ["#53d9ff", "#55e0ce", "#2cb8a9", "#97f0ff", "#2ca3d2", "#0f9f8f"];

    function getScheme() {
      var el = document.querySelector("[data-md-color-scheme]");
      return (el && el.getAttribute("data-md-color-scheme")) || "default";
    }

    function spawnBubble(x, y) {
      var colors = getScheme() === "slate" ? COLORS_DARK : COLORS_LIGHT;
      for (var i = 0; i < BUBBLE_COUNT; i++) {
        var bubble = document.createElement("div");
        bubble.className = "click-bubble";

        var size = 6 + Math.random() * 10;
        var angle = (Math.PI * 2 * i) / BUBBLE_COUNT + (Math.random() - 0.5) * 0.6;
        var distance = 30 + Math.random() * 50;
        var dx = Math.cos(angle) * distance;
        var dy = Math.sin(angle) * distance - 20; // bias upward

        bubble.style.cssText =
          "left:" + x + "px;top:" + y + "px;" +
          "width:" + size + "px;height:" + size + "px;" +
          "background:" + colors[i % colors.length] + ";" +
          "--bx:" + dx.toFixed(1) + "px;--by:" + dy.toFixed(1) + "px;";

        document.body.appendChild(bubble);
        (function (node) {
          setTimeout(function () { node.remove(); }, 700);
        })(bubble);
      }
    }

    document.addEventListener("click", function (e) {
      /* 只在空白区域触发：排除可交互元素 */
      var tag = e.target.tagName;
      if (tag === "A" || tag === "BUTTON" || tag === "INPUT" || tag === "TEXTAREA" ||
          tag === "SELECT" || tag === "LABEL" || tag === "SUMMARY" ||
          tag === "VIDEO" || tag === "AUDIO" || tag === "IFRAME") return;
      if (e.target.closest("a, button, .md-search, .md-nav__link, .md-tabs, " +
          ".md-footer, .site-like, .grid.cards, details, .admonition, " +
          "pre, code, table, [data-site-like]")) return;

      spawnBubble(e.clientX, e.clientY);
    });
  }

  function replayPageAnimations() {
    [".md-content", ".md-sidebar"].forEach(function (selector) {
      var node = document.querySelector(selector);
      if (!node) return;
      node.style.animation = "none";
      void node.offsetHeight;
      node.style.animation = "";
    });
  }

  function initPage() {
    calculateReadingTime();
    initLikeButton();
  }

  if (document.readyState === "loading") {
    document.addEventListener("DOMContentLoaded", function () {
      initPage();
      initReadingProgress();
      initKeyboardShortcuts();
      initClickBubbles();
    });
  } else {
    initPage();
    initReadingProgress();
    initKeyboardShortcuts();
    initClickBubbles();
  }

  if (typeof document$ !== "undefined") {
    document$.subscribe(function () {
      initPage();
      replayPageAnimations();
    });
  }
})();
