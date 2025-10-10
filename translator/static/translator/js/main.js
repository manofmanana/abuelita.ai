(function () {
  document.addEventListener("DOMContentLoaded", function () {
    const src = document.getElementById("id_source_language");
    const tgt = document.getElementById("id_target_language");
    const swapBtn = document.getElementById("swap-languages");
    const copyBtn = document.querySelector(".copy-btn");
    const listenBtn = document.querySelector(".listen-btn");
    const outEl = document.getElementById("translation-output");

    // Swap languages
    if (swapBtn && src && tgt) {
      swapBtn.addEventListener("click", function () {
        const srcVal = src.value;
        src.value = tgt.value;
        tgt.value = srcVal;
      });
    }

    // Enforce sensible defaults: if source is 'en' then target should be 'es' and vice versa
    function enforceLanguagePairing() {
      if (!src || !tgt) return;
      const s = String(src.value || '').toLowerCase();
      const t = String(tgt.value || '').toLowerCase();
      if (s === 'en' && t !== 'es') {
        tgt.value = 'es';
      } else if (s === 'es' && t !== 'en') {
        tgt.value = 'en';
      }
    }
    if (src && tgt) {
      src.addEventListener('change', enforceLanguagePairing);
      tgt.addEventListener('change', function () {
        // If user changes target to same as source, flip intelligently
        if (tgt.value === src.value) {
          if (tgt.value === 'en') src.value = 'es'; else src.value = 'en';
        }
      });
      // Run once on load to enforce sensible defaults
      try { enforceLanguagePairing(); } catch (e) {}
    }

    // Copy to clipboard
    if (copyBtn && outEl) {
      copyBtn.addEventListener("click", async function () {
        try {
          await navigator.clipboard.writeText(outEl.innerText.trim());
          copyBtn.innerHTML = '<i class="bi bi-check2"></i> Copied';
          setTimeout(() => (copyBtn.innerHTML = '<i class="bi bi-clipboard"></i> Copy'), 1500);
        } catch (e) {
          console.error("Copy failed:", e);
        }
      });
    }

    // Text-to-speech
    function pickLangCode(valOrText) {
      const v = String(valOrText || "").toLowerCase();
      if (v.includes("es") || v.includes("spanish") || v.includes("español")) return "es-ES";
      return "en-US";
    }

    function getVoiceFor(langCode) {
      const voices = window.speechSynthesis.getVoices ? speechSynthesis.getVoices() : [];
      const exact = voices.find(v => v.lang === langCode);
      if (exact) return exact;
      const prefix = voices.find(v => v.lang && v.lang.startsWith(langCode.slice(0,2)));
      return prefix || voices[0] || null;
    }

    // Small helper to escape HTML when injecting text into templates
    function escapeHtml(str) {
      return String(str || '').replace(/&/g, '&amp;').replace(/"/g, '&quot;').replace(/</g, '&lt;').replace(/>/g, '&gt;');
    }

    // Normalize text for comparison: remove diacritics, lower-case, trim
    function normalizeText(t) {
      if (t == null) return '';
      try {
        return String(t).normalize('NFD').replace(/[\u0300-\u036f]/g, '').toLowerCase().trim();
      } catch (e) {
        return String(t).toLowerCase().trim();
      }
    }

    if (listenBtn && outEl && "speechSynthesis" in window) {
      // Make sure voices are loaded (Safari/Chrome quirk)
      window.speechSynthesis.onvoiceschanged = () => {};
      listenBtn.addEventListener("click", function () {
        const text = outEl.innerText.trim();
        if (!text) return;
        const targetText = tgt ? (tgt.value || tgt.options[tgt.selectedIndex]?.text) : "en";
        const lang = pickLangCode(targetText);
        const u = new SpeechSynthesisUtterance(text);
        u.lang = lang;
        const v = getVoiceFor(lang);
        if (v) u.voice = v;
        speechSynthesis.cancel();
        speechSynthesis.speak(u);
      });
    }

    // Helper to rebind UI features for dynamically-inserted lesson content
    function initLessonInteractions(root) {
      root = root || document;
      // Per-item bilingual toggle: buttons that are keyboard accessible and
      // toggle an expanded panel. We toggle classes and ARIA attributes so CSS
      // can animate the transition smoothly.
      root.querySelectorAll('.bilingual-toggle').forEach(btn => {
        const expId = btn.getAttribute('aria-controls');
        const exp = expId ? root.querySelector('#' + expId) : btn.nextElementSibling;
        if (!exp) return;
        const toggle = () => {
          const isOpen = btn.getAttribute('aria-expanded') === 'true';
          // Accordion behavior: close other open panels within the same result container
          const container = btn.closest('.translation-result') || document;
          container.querySelectorAll('.bilingual-expanded.is-open').forEach(openEl => {
            if (openEl !== exp) {
              openEl.classList.remove('is-open');
              openEl.setAttribute('aria-hidden', 'true');
              const b = container.querySelector(`[aria-controls="${openEl.id}"]`);
              if (b) b.setAttribute('aria-expanded', 'false');
            }
          });

          btn.setAttribute('aria-expanded', isOpen ? 'false' : 'true');
          exp.setAttribute('aria-hidden', isOpen ? 'true' : 'false');
          exp.classList.toggle('is-open', !isOpen);
          // rotate caret icon inside the button to indicate state
          const caret = btn.querySelector('.caret');
          if (caret) caret.classList.toggle('rotated', !isOpen);
        };
        btn.addEventListener('click', toggle);
        // Keyboard support (Space/Enter)
        btn.addEventListener('keydown', (e) => {
          if (e.key === ' ' || e.key === 'Enter') {
            e.preventDefault();
            toggle();
          }
        });
      });

      // Show answer buttons
      root.querySelectorAll('.btn-show-answer').forEach(b => {
        b.addEventListener('click', () => {
          const ans = b.nextElementSibling;
          if (ans) ans.style.display = 'block';
        });
      });

      // Interactive cloze/exercise UI removed — left only passive hints; no handlers necessary.
    }

    // Delegated handler: in case per-button bindings aren't attached (timing or
    // dynamic insertion issues), listen on document and toggle panels when any
    // `.bilingual-toggle` is clicked. This is intentionally simple and mirrors
    // the toggle behavior in initLessonInteractions.
    function _toggleForButton(btn) {
      if (!btn) return;
      const expId = btn.getAttribute('aria-controls');
      const exp = expId ? document.getElementById(expId) : btn.nextElementSibling;
      if (!exp) return;
      const isOpen = btn.getAttribute('aria-expanded') === 'true';
      const container = btn.closest('.translation-result') || document;
      container.querySelectorAll('.bilingual-expanded.is-open').forEach(openEl => {
        if (openEl !== exp) {
          openEl.classList.remove('is-open');
          openEl.setAttribute('aria-hidden', 'true');
          const b = container.querySelector(`[aria-controls="${openEl.id}"]`);
          if (b) b.setAttribute('aria-expanded', 'false');
        }
      });
      btn.setAttribute('aria-expanded', isOpen ? 'false' : 'true');
      exp.setAttribute('aria-hidden', isOpen ? 'true' : 'false');
      exp.classList.toggle('is-open', !isOpen);
      const caret = btn.querySelector('.caret');
      if (caret) caret.classList.toggle('rotated', !isOpen);
    }

    document.addEventListener('click', function (e) {
      const btn = e.target.closest && e.target.closest('.bilingual-toggle');
      if (btn) {
        e.preventDefault();
        _toggleForButton(btn);
      }
      const diffBtn = e.target.closest && e.target.closest('.difficulty-tab');
      if (diffBtn) {
        e.preventDefault();
        const diff = diffBtn.getAttribute('data-diff');
        document.querySelectorAll('.difficulty-section').forEach(sec => {
          sec.style.display = (sec.getAttribute('data-diff') === diff) ? 'block' : 'none';
        });
        // Update tab styling so the clicked tab looks active
        document.querySelectorAll('.difficulty-tab').forEach(t => {
          if (t.getAttribute('data-diff') === diff) {
            t.classList.remove('btn-outline-secondary');
            t.classList.add('btn-secondary');
            t.classList.add('active');
          } else {
            t.classList.add('btn-outline-secondary');
            t.classList.remove('btn-secondary');
            t.classList.remove('active');
          }
        });
      }
    });

    document.addEventListener('keydown', function (e) {
      const active = document.activeElement;
      if (!active) return;
      if (active.classList && active.classList.contains('bilingual-toggle')) {
        if (e.key === ' ' || e.key === 'Enter') {
          e.preventDefault();
          _toggleForButton(active);
        }
      }
    });

    // Helper to show bootstrap toast messages
    function showToast(title, body, isError) {
      const container = document.getElementById('toast-container');
      if (!container) return;
      const id = 'toast-' + Date.now();
      const toastEl = document.createElement('div');
      toastEl.className = 'toast align-items-center text-bg-' + (isError ? 'danger' : 'success') + ' border-0';
      toastEl.id = id;
      toastEl.setAttribute('role', 'alert');
      toastEl.setAttribute('aria-live', 'assertive');
      toastEl.setAttribute('aria-atomic', 'true');
      toastEl.innerHTML = `<div class="d-flex"><div class="toast-body"><strong>${title}</strong><div>${body}</div></div><button type="button" class="btn-close btn-close-white me-2 m-auto" data-bs-dismiss="toast" aria-label="Close"></button></div>`;
      container.appendChild(toastEl);
      const bsToast = new bootstrap.Toast(toastEl, {delay: 4000});
      bsToast.show();
      // remove after hidden
      toastEl.addEventListener('hidden.bs.toast', () => toastEl.remove());
    }

    // AJAX submit helper
    async function postFormAJAX(formEl, url) {
      const data = new FormData(formEl);
      // Read CSRF token from cookie if present and include in header for Django
      function getCookie(name) {
        const v = document.cookie.match('(^|;)\\s*' + name + '\\s*=\\s*([^;]+)');
        return v ? v.pop() : '';
      }
      const csrftoken = getCookie('csrftoken');
      const headers = {'X-Requested-With': 'XMLHttpRequest'};
      if (csrftoken) headers['X-CSRFToken'] = csrftoken;
      const resp = await fetch(url, {method: 'POST', body: data, headers: headers, credentials: 'same-origin'});
      if (!resp.ok) throw new Error('Network response not ok');
      // Try parse JSON, but fall back to text (HTML) so server can return either.
      try {
        return await resp.json();
      } catch (e) {
        const text = await resp.text();
        return {__html_fallback: text};
      }
    }

    // Wire Learn form to use AJAX when present
    const learnForm = document.getElementById('learn-form');
    if (learnForm) {
      let __abuelita_ajax_attempted = false;
      learnForm.addEventListener('submit', async (e) => {
        e.preventDefault();
        const url = learnForm.action || window.location.pathname;
        try {
          // Attempt AJAX submit; wrap in try/catch to surface errors to the UI
          __abuelita_ajax_attempted = true;
          const data = await postFormAJAX(learnForm, url);
          if (data.__html_fallback) {
            const container = document.getElementById('learn-result-body');
            if (container) container.innerHTML = data.__html_fallback;
            return;
          }
          if (data.lesson_output || data.lesson_struct) {
            const container = document.getElementById('learn-result-body');
            if (container) {
              // Render simple fallback text and structured HTML if available
              let html = '';
              if (data.lesson_struct) {
                const s = data.lesson_struct;
                // Generate a deterministic per-response prefix so test ids are stable
                const respPrefix = 'bilingual-' + (window.__abuelita_bilingual_seq = (window.__abuelita_bilingual_seq || 0) + 1);
                // Detect page language: use the html[lang] attribute when present
                const pageLang = document.documentElement.lang || (document.querySelector('html').getAttribute('lang') || 'en');
                const showESCompact = pageLang && pageLang.startsWith('es');
                html += `<div class="translation-result p-3 rounded bg-light">`;
                const topicEn = s.topic_en || s.topic || '';
                const topicEs = s.topic_es || '';
                // Prefer labels provided in lesson_struct, but fall back to reasonable defaults.
                const labelsFromStruct = s.labels || {};
                const localized = showESCompact
                  ? {
                      topicLabel: labelsFromStruct.topicLabel_es || 'Tema',
                      tipText: labelsFromStruct.tipText_es || 'Haz clic en cualquier frase o ejemplo para ver Inglés y Español lado a lado.',
                      phrases: labelsFromStruct.phrases_es || 'Frases',
                      examples: labelsFromStruct.examples_es || 'Ejemplos',
                      miniQuiz: s.mini_quiz_es || 'Mini-prueba',
                      showAnswer: labelsFromStruct.showAnswer_es || 'Mostrar respuesta',
                      paraphrasesLabel: labelsFromStruct.paraphrases_es || (s.labels && s.labels.paraphrases_es) || 'Paráfrasis',
                      tryClozeLabel: labelsFromStruct.try_cloze_es || (s.labels && s.labels.try_cloze_es) || '',
                      difficultyLabels: (s.labels && s.labels.difficulty_es) || {easy: 'Fácil', medium: 'Medio', hard: 'Difícil'},
                    }
                  : {
                      topicLabel: labelsFromStruct.topicLabel_en || 'Topic',
                      tipText: labelsFromStruct.tipText_en || 'Tip: Click any phrase or example to view English and Spanish side-by-side.',
                      phrases: labelsFromStruct.phrases_en || 'Phrases',
                      examples: labelsFromStruct.examples_en || 'Examples',
                      miniQuiz: s.mini_quiz_en || 'Mini-quiz',
                      showAnswer: labelsFromStruct.showAnswer_en || 'Show Answer',
                      paraphrasesLabel: labelsFromStruct.paraphrases_en || (s.labels && s.labels.paraphrases_en) || 'Paraphrases',
                      tryClozeLabel: labelsFromStruct.try_cloze_en || (s.labels && s.labels.try_cloze_en) || '',
                      difficultyLabels: (s.labels && s.labels.difficulty_en) || {easy: 'Easy', medium: 'Medium', hard: 'Hard'},
                    };

                html += `<h6 class="fw-semibold">${localized.topicLabel}: ${showESCompact ? topicEs : topicEn}</h6>`;
                html += `<div class="mb-2 small text-muted">${localized.tipText}</div>`;

                // Render progression controls (client-side) using localized label
                const progressionLabel = showESCompact ? (s.labels && s.labels.lesson_progression_es) || 'Progresión de la lección' : (s.labels && s.labels.lesson_progression_en) || 'Lesson progression';
                html += `<div class="mb-3"><strong>${progressionLabel}:</strong> <div class="btn-group ms-2" role="group">`;
                // Default difficulty selection comes from lesson_struct labels (fallback to 'easy')
                const defaultDiff = (s.labels && s.labels.default_difficulty) || 'easy';
                ['easy','medium','hard'].forEach(d => {
                  const isActive = d === defaultDiff;
                  // Active style: grey background + white text -> use btn-secondary
                  const cls = isActive ? 'btn btn-sm btn-secondary difficulty-tab active' : 'btn btn-sm btn-outline-secondary difficulty-tab';
                  html += `<button type="button" class="${cls}" data-diff="${d}">${localized.difficultyLabels[d]}</button>`;
                });
                html += `</div></div>`;

                // Render phrases grouped by difficulty
                ['easy','medium','hard'].forEach((diff) => {
                  const showByDefault = diff === ((s.labels && s.labels.default_difficulty) || 'easy');
                  html += `<div class="difficulty-section" data-diff="${diff}" style="display:${showByDefault ? 'block' : 'none'}">`;
                  // Use localized phrases label if provided
                  const phrasesLabel = showESCompact ? (s.labels && s.labels.phrases_es) || localized.phrases : (s.labels && s.labels.phrases_en) || localized.phrases;
                  html += `<h6>${phrasesLabel} - ${localized.difficultyLabels[diff]}</h6><ul>`;
                  const group = (s.phrases_by_difficulty && s.phrases_by_difficulty[diff]) || [];
                  for (let i = 0; i < group.length; i++) {
                    const p = group[i];
                    const pid = `${respPrefix}-phrase-${diff}-${i}`;
                    html += `<li class="bilingual-item">`;
                    if (showESCompact) {
                      html += `<button type="button" class="bilingual-toggle btn btn-link p-0 text-start" aria-expanded="false" aria-controls="${pid}"><div class="d-flex align-items-center"><div class="bilingual-compact">ES: ${p.es}</div><i class="bi bi-caret-down-fill caret ms-2"></i></div></button>`;
                      html += `<div id="${pid}" class="bilingual-expanded mt-2" aria-hidden="true"><div class="row"><div class="col-12"><strong>EN</strong>: ${p.en}</div></div>`;
                      // Replace paraphrases with opposite-language phonetic guidance when available
                      if (showESCompact) {
                        // Spanish page: show phonetic hint for English text (opposite language)
                        if (p.phonetic_en) {
                          html += `<div class="mt-2 small text-muted">Pronunciation (EN):</div><div class="small">${p.phonetic_en}</div>`;
                        }
                      } else {
                        // English page: show phonetic hint for Spanish text
                        if (p.phonetic_es) {
                          html += `<div class="mt-2 small text-muted">Pronunciation (ES):</div><div class="small">${p.phonetic_es}</div>`;
                        }
                      }
                      html += `</div>`;
                    } else {
                      html += `<button type="button" class="bilingual-toggle btn btn-link p-0 text-start" aria-expanded="false" aria-controls="${pid}"><div class="d-flex align-items-center"><div class="bilingual-compact">EN: ${p.en}</div><i class="bi bi-caret-down-fill caret ms-2"></i></div></button>`;
                      html += `<div id="${pid}" class="bilingual-expanded mt-2" aria-hidden="true"><div class="row"><div class="col-12"><strong>ES</strong>: ${p.es}</div></div>`;
                      // Show opposite-language phonetic hint when available; fall back to paraphrases
                      if (p.phonetic_es) {
                        html += `<div class="mt-2 small text-muted">Pronunciation (ES):</div><div class="small">${p.phonetic_es}</div>`;
                      } else if (p.paraphrases_en && p.paraphrases_en.length) {
                        html += `<div class="mt-2 small text-muted">${localized.paraphrasesLabel}:</div><ul>`;
                        p.paraphrases_en.forEach(pa => html += `<li class="small">${pa}</li>`);
                        html += `</ul>`;
                      }
                      html += `</div>`;
                    }
                    html += `</li>`;
                  }
                  html += `</ul></div>`;
                });

                // Render examples (cloze hints removed)
                const examplesLabel = showESCompact ? (s.labels && s.labels.examples_es) || localized.examples : (s.labels && s.labels.examples_en) || localized.examples;
                html += `<div class="mt-4"><h6>${examplesLabel}</h6>`;
                const examples_all = s.examples || [];
                examples_all.forEach((ex, idx) => {
                  html += `<div class="mb-3">`;
                  if (showESCompact) {
                    html += `<div class="small text-muted">ES: ${ex.es}</div><div class="mt-1"><strong>EN</strong>: ${ex.en}</div>`;
                  } else {
                    html += `<div class="small text-muted">EN: ${ex.en}</div><div class="mt-1"><strong>ES</strong>: ${ex.es}</div>`;
                  }
                    // Cloze hints intentionally removed across difficulties and languages
                  html += `</div>`;
                });
                html += `</div>`;

                html += `<h6>${localized.miniQuiz}</h6><ol>`;
                s.quiz.forEach(q => {
                  html += `<li>`;
                  if (showESCompact) {
                    // On Spanish page: show the Spanish prompt, reveal the English answer
                    html += `<div>${q.q_es || q.q}</div>`;
                    if (q.choices_es) { html += '<ul>'; q.choices_es.forEach(c=> html += `<li>${c}</li>`); html += '</ul>'; }
                    const showAnswerLabel = (s.labels && s.labels.showAnswer_es) || (s.labels && s.labels.showAnswer_en) || (showESCompact ? 'Mostrar respuesta' : 'Show Answer');
                    html += `<button class="btn btn-sm btn-outline-info mt-1 btn-show-answer">${showAnswerLabel}</button><div class="mt-1" style="display:none">${q.answer_text_en || ''}</div>`;
                  } else {
                    // On English page: show the English prompt, reveal the Spanish answer
                    html += `<div>${q.q_en || q.q}</div>`;
                    if (q.choices_en) { html += '<ul>'; q.choices_en.forEach(c=> html += `<li>${c}</li>`); html += '</ul>'; }
                    const showAnswerLabel = (s.labels && s.labels.showAnswer_en) || (s.labels && s.labels.showAnswer_es) || (showESCompact ? 'Mostrar respuesta' : 'Show Answer');
                    html += `<button class="btn btn-sm btn-outline-info mt-1 btn-show-answer">${showAnswerLabel}</button><div class="mt-1" style="display:none">${q.answer_text_es || ''}</div>`;
                  }
                  html += `</li>`;
                });
                html += `</ol></div>`;
              } else if (data.lesson_output) {
                html += `<div class="translation-result p-3 rounded bg-light"><p class="fs-5 mb-0" style="white-space: pre-line">${data.lesson_output}</p></div>`;
              }
              container.innerHTML = html;
              initLessonInteractions(container);
            }
          }

          // Bind interactions for any server-rendered lesson content present on page load
          try {
            initLessonInteractions(document);
          } catch (e) {
            console.error('Failed to init lesson interactions on load', e);
          }
        } catch (err) {
          console.error('Learn request failed', err);
          try {
            showToast('Learn failed', String(err), true);
          } catch (e) {
            // ignore toast errors
          }
          // Fall back to normal form submit so server-rendered page loads
          try {
            learnForm.removeEventListener('submit', arguments.callee);
          } catch (e) {}
          learnForm.submit();
        }
      });
    }

    // Ensure server-rendered bilingual toggles are bound on initial page load
    try {
      initLessonInteractions(document);
    } catch (e) {
      // Log and continue — non-fatal if DOM isn't ready for some reason
      console.error('Failed to init lesson interactions at startup', e);
    }

    // --- Translation Hub AJAX handling ---
    const translationForm = document.getElementById('translation-form');
    if (translationForm) {
      translationForm.addEventListener('submit', async (e) => {
        e.preventDefault();
        const url = translationForm.action || window.location.pathname;
        try {
          const data = await postFormAJAX(translationForm, url);
          const resultArea = document.getElementById('translation-result-area');
          const resultCard = document.getElementById('translation-result-card');
          const out = document.getElementById('translation-output');
          if (data && data.translation_result) {
            // Populate the persistent result area
            if (resultCard) resultCard.classList.remove('d-none');
            if (resultArea && !resultArea.querySelector('.card')) {
              // If server didn't render a card, inject the card markup
              if (resultCard) resultArea.appendChild(resultCard);
            }
            if (out) out.textContent = data.translation_result;
            // If a download_url is provided, show a download button
            if (data.download_url) {
              // remove existing download link if present
              const existing = resultArea.querySelector('.download-translated');
              if (existing) existing.remove();
              const a = document.createElement('a');
              a.href = data.download_url;
              a.className = 'btn btn-outline-success btn-sm download-translated';
              a.innerHTML = '<i class="bi bi-download"></i> Download';
              // place next to existing controls
              const controls = resultArea.querySelector('.translation-result .d-flex');
              if (controls) controls.appendChild(a);
            }
            // Bind copy/listen handlers for the newly inserted buttons
            initResultButtons(resultArea || document);
          } else if (data && data.__html_fallback) {
            // Server returned full HTML; replace result area
            if (resultArea) resultArea.innerHTML = data.__html_fallback;
            initResultButtons(resultArea || document);
          }
        } catch (err) {
          console.error('Translation request failed', err);
          showToast('Translation failed', String(err), true);
          // fallback to full submit
          translationForm.removeEventListener('submit', arguments.callee);
          translationForm.submit();
        }
      });
    }

    function initResultButtons(root) {
      root = root || document;
      // Copy button
      root.querySelectorAll('.copy-btn').forEach(btn => {
        btn.addEventListener('click', async () => {
          const out = document.getElementById('translation-output');
          if (!out) return;
          try {
            await navigator.clipboard.writeText(out.innerText.trim());
            showToast('Copied', 'Translation copied to clipboard', false);
          } catch (e) {
            showToast('Copy failed', String(e), true);
          }
        });
      });

      // Listen button (uses existing speech helpers)
      root.querySelectorAll('.listen-btn').forEach(btn => {
        btn.addEventListener('click', () => {
          const out = document.getElementById('translation-output');
          if (!out) return;
          const text = out.innerText.trim();
          if (!text) return;
          const targetSelect = document.getElementById('id_target_language');
          const targetText = targetSelect ? (targetSelect.value || targetSelect.options[targetSelect.selectedIndex]?.text) : 'en';
          const lang = pickLangCode(targetText);
          const u = new SpeechSynthesisUtterance(text);
          u.lang = lang;
          const v = getVoiceFor(lang);
          if (v) u.voice = v;
          speechSynthesis.cancel();
          speechSynthesis.speak(u);
        });
      });
    }

    // Culture feature removed — no client-side wiring necessary.
  });
})();
