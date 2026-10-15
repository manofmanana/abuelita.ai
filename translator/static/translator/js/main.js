/* Abuelita.ai front-end.
 *
 * Progressive enhancement: every form works without JavaScript. With JS we
 * submit via fetch, show loading states, and add speech in/out.
 */
(() => {
  "use strict";

  const LANG_TAGS = { en: "en-US", es: "es-MX" };

  // ---------------------------------------------------------------------
  // Helpers
  // ---------------------------------------------------------------------
  const $ = (sel, root = document) => root.querySelector(sel);
  const $$ = (sel, root = document) => Array.from(root.querySelectorAll(sel));
  const pageLang = () => (document.documentElement.lang || "en").slice(0, 2);
  const t = (en, es) => (pageLang() === "es" ? es : en);

  function showToast(message, isError = false) {
    const container = $("#toast-container");
    if (!container || !window.bootstrap) return;
    const el = document.createElement("div");
    el.className = `toast align-items-center border-0 text-bg-${isError ? "danger" : "success"}`;
    el.setAttribute("role", isError ? "alert" : "status");
    el.innerHTML =
      '<div class="d-flex"><div class="toast-body"></div>' +
      '<button type="button" class="btn-close btn-close-white me-2 m-auto" data-bs-dismiss="toast"></button></div>';
    $(".toast-body", el).textContent = message;
    $(".btn-close", el).setAttribute("aria-label", t("Close", "Cerrar"));
    container.appendChild(el);
    el.addEventListener("hidden.bs.toast", () => el.remove());
    new bootstrap.Toast(el, { delay: 3500 }).show();
  }

  function setBusy(button, busy) {
    if (!button) return;
    button.disabled = busy;
    $(".spinner-border", button)?.classList.toggle("d-none", !busy);
  }

  async function postForm(form) {
    const resp = await fetch(form.action || window.location.href, {
      method: "POST",
      body: new FormData(form),
      headers: { "X-Requested-With": "XMLHttpRequest" },
      credentials: "same-origin",
    });
    let data = null;
    try {
      data = await resp.json();
    } catch {
      /* non-JSON (e.g. a proxy error page) */
    }
    if (!data) throw new Error(`HTTP ${resp.status}`);
    return data;
  }

  // ---------------------------------------------------------------------
  // Speech synthesis (Listen buttons)
  // ---------------------------------------------------------------------
  function speak(text, langTag) {
    if (!("speechSynthesis" in window) || !text) {
      showToast(t("Speech isn't supported in this browser.", "Tu navegador no admite voz."), true);
      return;
    }
    const utterance = new SpeechSynthesisUtterance(text);
    utterance.lang = langTag;
    const voices = speechSynthesis.getVoices();
    const voice =
      voices.find((v) => v.lang === langTag) || voices.find((v) => v.lang?.startsWith(langTag.slice(0, 2)));
    if (voice) utterance.voice = voice;
    speechSynthesis.cancel();
    speechSynthesis.speak(utterance);
  }
  // Some browsers load voices lazily; touching the list warms it up.
  if ("speechSynthesis" in window) speechSynthesis.getVoices();

  // ---------------------------------------------------------------------
  // Delegated click handling (works for server- and AJAX-rendered content)
  // ---------------------------------------------------------------------
  document.addEventListener("click", (event) => {
    const target = event.target;

    const toggle = target.closest(".bilingual-toggle");
    if (toggle) {
      const panel = document.getElementById(toggle.getAttribute("aria-controls"));
      if (!panel) return;
      const open = toggle.getAttribute("aria-expanded") !== "true";
      // Accordion: close the other open panels in this lesson.
      const scope = toggle.closest(".lesson") || document;
      $$(".bilingual-toggle[aria-expanded='true']", scope).forEach((other) => {
        if (other === toggle) return;
        other.setAttribute("aria-expanded", "false");
        const otherPanel = document.getElementById(other.getAttribute("aria-controls"));
        if (otherPanel) {
          otherPanel.hidden = true;
          otherPanel.classList.remove("is-open");
        }
      });
      toggle.setAttribute("aria-expanded", String(open));
      panel.hidden = !open;
      panel.classList.toggle("is-open", open);
      return;
    }

    const tab = target.closest(".difficulty-tab");
    if (tab) {
      const scope = tab.closest(".lesson") || document;
      const diff = tab.dataset.diff;
      $$(".difficulty-tab", scope).forEach((btn) => {
        const active = btn === tab;
        btn.classList.toggle("active", active);
        btn.classList.toggle("btn-secondary", active);
        btn.classList.toggle("btn-outline-secondary", !active);
        btn.setAttribute("aria-selected", String(active));
      });
      $$(".difficulty-section", scope).forEach((sec) => {
        sec.hidden = sec.dataset.diff !== diff;
      });
      return;
    }

    const showAnswer = target.closest(".btn-show-answer");
    if (showAnswer) {
      const answer = showAnswer.nextElementSibling;
      if (answer) {
        answer.hidden = !answer.hidden;
        showAnswer.setAttribute("aria-expanded", String(!answer.hidden));
      }
      return;
    }

    const speakBtn = target.closest(".speak-btn");
    if (speakBtn) {
      speak(speakBtn.dataset.speak, speakBtn.dataset.lang || "es-MX");
    }
  });

  // Auto-submit the language switcher.
  document.addEventListener("change", (event) => {
    if (event.target.matches("select[data-autosubmit]")) event.target.form.submit();
  });

  // ---------------------------------------------------------------------
  // Translation hub
  // ---------------------------------------------------------------------
  function initTranslator() {
    const form = $("#translation-form");
    if (!form) return;

    const src = $("#id_source_language");
    const tgt = $("#id_target_language");
    const textarea = $("#id_text_input");
    const counter = $("#char-count");
    const submitBtn = $("#translate-btn");
    const errorBox = $("#translation-error");
    const card = $("#translation-result-card");
    const output = $("#translation-output");
    const download = $(".download-translated");
    const truncatedNote = $("#truncated-note");

    const other = (lang) => (lang === "en" ? "es" : "en");

    $("#swap-languages")?.addEventListener("click", () => {
      [src.value, tgt.value] = [tgt.value, src.value];
      // Swapping should also move the last translation into the input.
      if (output.textContent.trim() && !card.classList.contains("d-none")) {
        textarea.value = output.textContent.trim();
        updateCount();
      }
    });
    src?.addEventListener("change", () => (tgt.value = other(src.value)));
    tgt?.addEventListener("change", () => (src.value = other(tgt.value)));

    function updateCount() {
      if (counter && textarea) counter.textContent = textarea.value.length;
    }
    textarea?.addEventListener("input", updateCount);
    updateCount();

    function showError(message) {
      errorBox.textContent = message;
      errorBox.classList.toggle("d-none", !message);
    }

    form.addEventListener("submit", async (event) => {
      event.preventDefault();
      showError("");
      setBusy(submitBtn, true);
      try {
        const data = await postForm(form);
        if (!data.ok) {
          showError(data.error || t("Something went wrong.", "Algo salió mal."));
          return;
        }
        output.textContent = data.translation_result;
        output.lang = data.target_language || tgt.value;
        card.classList.remove("d-none");
        truncatedNote?.classList.toggle("d-none", !data.truncated);
        if (download) {
          download.classList.toggle("d-none", !data.download_url);
          download.href = data.download_url || "#";
        }
        card.scrollIntoView({ behavior: "smooth", block: "nearest" });
      } catch (err) {
        console.error("Translation request failed", err);
        // Fall back to a normal form post so the server renders the result.
        form.submit();
      } finally {
        setBusy(submitBtn, false);
      }
    });

    $(".copy-btn")?.addEventListener("click", async () => {
      try {
        await navigator.clipboard.writeText(output.textContent.trim());
        showToast(t("Copied to clipboard", "Copiado al portapapeles"));
      } catch {
        showToast(t("Couldn't copy the text.", "No se pudo copiar el texto."), true);
      }
    });

    $(".listen-btn")?.addEventListener("click", () => {
      speak(output.textContent.trim(), LANG_TAGS[output.lang] || LANG_TAGS[tgt.value] || "es-MX");
    });

    initSpeechInput(textarea, src, updateCount);
  }

  // Voice input via the Web Speech API (Chrome, Edge, Safari).
  function initSpeechInput(textarea, src, onChange) {
    const Recognition = window.SpeechRecognition || window.webkitSpeechRecognition;
    const micBtn = $("#mic-btn");
    if (!Recognition || !micBtn || !textarea) return;
    micBtn.classList.remove("d-none");

    let recognition = null;
    const label = $(".mic-label", micBtn);
    const idleLabel = label.textContent;

    function stop() {
      recognition?.stop();
    }

    micBtn.addEventListener("click", () => {
      if (recognition) return stop();
      recognition = new Recognition();
      recognition.lang = LANG_TAGS[src.value] || "en-US";
      recognition.interimResults = false;
      const before = textarea.value ? textarea.value.trimEnd() + " " : "";
      recognition.onresult = (e) => {
        const heard = Array.from(e.results)
          .map((r) => r[0].transcript)
          .join(" ");
        textarea.value = before + heard;
        onChange();
      };
      recognition.onerror = (e) => {
        if (e.error !== "aborted" && e.error !== "no-speech") {
          showToast(t("Microphone error: ", "Error del micrófono: ") + e.error, true);
        }
      };
      recognition.onend = () => {
        recognition = null;
        micBtn.classList.remove("listening");
        micBtn.setAttribute("aria-pressed", "false");
        label.textContent = idleLabel;
      };
      micBtn.classList.add("listening");
      micBtn.setAttribute("aria-pressed", "true");
      label.textContent = t("Listening…", "Escuchando…");
      recognition.start();
    });
  }

  // ---------------------------------------------------------------------
  // Learn page
  // ---------------------------------------------------------------------
  function initLearn() {
    const form = $("#learn-form");
    if (!form) return;
    const input = $("#input_text");
    const submitBtn = $("#learn-btn");
    const resultBody = $("#learn-result-body");

    $$(".topic-chip").forEach((chip) =>
      chip.addEventListener("click", (event) => {
        event.preventDefault();
        input.value = chip.dataset.topic;
        form.requestSubmit();
      })
    );

    form.addEventListener("submit", async (event) => {
      event.preventDefault();
      if (!input.value.trim()) return input.focus();
      setBusy(submitBtn, true);
      try {
        const data = await postForm(form);
        if (!data.ok || !data.html) throw new Error(data.error || "No lesson returned");
        resultBody.innerHTML = data.html; // server-rendered, auto-escaped by Django
        const url = new URL(window.location.href);
        url.searchParams.set("topic", input.value.trim());
        history.replaceState(null, "", url);
      } catch (err) {
        console.error("Learn request failed", err);
        form.submit();
      } finally {
        setBusy(submitBtn, false);
      }
    });
  }

  document.addEventListener("DOMContentLoaded", () => {
    initTranslator();
    initLearn();
  });
})();
