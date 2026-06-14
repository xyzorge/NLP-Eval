const API_URL = "/api/bleu";

const I18N = {
    ru: {
        title:         "NLP Eval — Оценка качества машинного перевода",
        heading:       "Оценка качества машинного перевода",
        subtitle:      "Сравнение двух переводов с эталоном по метрике&nbsp;<b>BLEU</b>",
        label_original:"Оригинал",
        label_reference:"Эталонный перевод (Человек)",
        label_cand1:   "Перевод 1 (Google)",
        label_cand2:   "Перевод 2 (DeepL)",
        ph_original:   "Исходный текст…",
        ph_reference:  "Перевод, выполненный человеком…",
        ph_cand1:      "Машинный перевод №1…",
        ph_cand2:      "Машинный перевод №2…",
        btn_calculate: "Рассчитать BLEU",
        btn_loading:   "Расчёт…",
        results_title: "Результаты",
        footer:        "Бета-версия · BLEU (NLTK)",
        watermark:     "© 2026 Федосеев Илья Максимович. Все права защищены.",
        err_fields:    "Заполните эталонный перевод и оба перевода для сравнения.",
        err_server:    "Не удалось связаться с сервером. Убедитесь, что бэкенд запущен. ",
        verdict_tie:   "Переводы получили <b>одинаковый</b> коэффициент BLEU.",
        verdict_win:   "Ближе к эталону: ",
    },
    en: {
        title:         "NLP Eval — Machine Translation Quality Evaluation",
        heading:       "Machine Translation Quality Evaluation",
        subtitle:      "Comparing two translations against a reference using the&nbsp;<b>BLEU</b> metric",
        label_original:"Source",
        label_reference:"Reference translation (Human)",
        label_cand1:   "Translation 1 (Google)",
        label_cand2:   "Translation 2 (DeepL)",
        ph_original:   "Source text…",
        ph_reference:  "Human-made translation…",
        ph_cand1:      "Machine translation #1…",
        ph_cand2:      "Machine translation #2…",
        btn_calculate: "Calculate BLEU Score",
        btn_loading:   "Calculating…",
        results_title: "Results",
        footer:        "Beta · BLEU (NLTK)",
        watermark:     "Copyright © 2026 Ilya Fedoseev. All Rights Reserved.",
        err_fields:    "Please fill in the reference translation and both candidate translations.",
        err_server:    "Could not reach the server. Make sure the backend is running. ",
        verdict_tie:   "Both translations received the <b>same</b> BLEU score.",
        verdict_win:   "Closer to the reference: ",
    },
};

let currentLang = localStorage.getItem("nlp-eval-lang") || "en";

const root = document.documentElement;
const themeToggle = document.getElementById("theme-toggle");

const savedTheme = localStorage.getItem("nlp-eval-theme");
if (savedTheme) {
    root.setAttribute("data-theme", savedTheme);
} else if (window.matchMedia("(prefers-color-scheme: dark)").matches) {
    root.setAttribute("data-theme", "dark");
}

themeToggle.addEventListener("click", () => {
    const next = root.getAttribute("data-theme") === "dark" ? "light" : "dark";
    root.setAttribute("data-theme", next);
    localStorage.setItem("nlp-eval-theme", next);
});

const langToggle = document.getElementById("lang-toggle");

function applyLang(lang) {
    currentLang = lang;
    const dict = I18N[lang];
    root.setAttribute("lang", lang);

    document.querySelectorAll("[data-i18n]").forEach(el => {
        const key = el.getAttribute("data-i18n");
        if (!dict[key]) return;
        if (el.getAttribute("data-i18n-html") === "true") {
            el.innerHTML = dict[key];
        } else {
            el.textContent = dict[key];
        }
    });

    document.querySelectorAll("[data-i18n-ph]").forEach(el => {
        const key = el.getAttribute("data-i18n-ph");
        if (dict[key]) el.placeholder = dict[key];
    });

    document.getElementById("watermark").textContent = dict.watermark;
    document.title = dict.title;

    langToggle.querySelectorAll(".lang-opt").forEach(opt => {
        opt.classList.toggle("active", opt.getAttribute("data-lang") === lang);
    });

    localStorage.setItem("nlp-eval-lang", lang);
}

langToggle.addEventListener("click", () => {
    applyLang(currentLang === "ru" ? "en" : "ru");
});

applyLang(currentLang);

const btn       = document.getElementById("calculate");
const btnLabel  = btn.querySelector(".btn-label");
const spinner   = btn.querySelector(".spinner");
const errorBox  = document.getElementById("error");
const results   = document.getElementById("results");

const card1 = document.getElementById("card1");
const card2 = document.getElementById("card2");
const score1 = document.getElementById("score1");
const score2 = document.getElementById("score2");
const bar1 = document.getElementById("bar1");
const bar2 = document.getElementById("bar2");
const verdict = document.getElementById("verdict");

btn.addEventListener("click", async () => {
    const dict = I18N[currentLang];

    const payload = {
        original:   document.getElementById("original").value.trim(),
        reference:  document.getElementById("reference").value.trim(),
        candidate1: document.getElementById("candidate1").value.trim(),
        candidate2: document.getElementById("candidate2").value.trim(),
    };

    if (!payload.reference || !payload.candidate1 || !payload.candidate2) {
        showError(dict.err_fields);
        return;
    }
    hideError();
    setLoading(true);

    try {
        const res = await fetch(API_URL, {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify(payload),
        });

        if (!res.ok) throw new Error("HTTP " + res.status);

        const data = await res.json();
        renderResults(data);
    } catch (err) {
        showError(dict.err_server + err.message);
    } finally {
        setLoading(false);
    }
});

function renderResults(data) {
    const { bleu1, bleu2, winner } = data;
    const dict = I18N[currentLang];

    score1.textContent = bleu1.toFixed(4);
    score2.textContent = bleu2.toFixed(4);

    card1.classList.remove("winner");
    card2.classList.remove("winner");
    if (winner === "candidate1") card1.classList.add("winner");
    if (winner === "candidate2") card2.classList.add("winner");

    if (winner === "tie") {
        verdict.innerHTML = dict.verdict_tie;
    } else {
        const name = winner === "candidate1" ? dict.label_cand1 : dict.label_cand2;
        verdict.innerHTML = `${dict.verdict_win}<b>${name}</b>`;
    }

    results.hidden = false;
    results.classList.remove("show");
    void results.offsetWidth;
    results.classList.add("show");

    setTimeout(() => {
        bar1.style.width = (bleu1 * 100).toFixed(1) + "%";
        bar2.style.width = (bleu2 * 100).toFixed(1) + "%";
    }, 50);
}

function setLoading(isLoading) {
    const dict = I18N[currentLang];
    btn.disabled = isLoading;
    spinner.hidden = !isLoading;
    btnLabel.textContent = isLoading ? dict.btn_loading : dict.btn_calculate;
}

function showError(msg) {
    errorBox.textContent = msg;
    errorBox.hidden = false;
}

function hideError() {
    errorBox.hidden = true;
}
