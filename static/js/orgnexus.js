// File: static/js/orgnexus.js - Aditya Mitter (W19869650)
// Tiny vanilla helpers - we keep JS minimal so the marker can read it
// without setting up a build step.

(function () {
    "use strict";

    // ---- Auto-dismiss flash messages ----------------------------------
    document.querySelectorAll(".alert.on-alert").forEach(function (el) {
        if (el.classList.contains("alert-danger") || el.classList.contains("alert-error")) {
            return;
        }
        setTimeout(function () {
            el.style.transition = "opacity .4s";
            el.style.opacity = "0";
            setTimeout(function () { el.remove(); }, 400);
        }, 4000);
    });


    // ---- Show/hide password toggle ------------------------------------
    document.querySelectorAll(".on-pw-wrap").forEach(function (wrap) {
        var input = wrap.querySelector("input[type='password']");
        if (!input) return;

        var btn = document.createElement("button");
        btn.type = "button";
        btn.className = "btn btn-sm on-pw-toggle";
        btn.setAttribute("aria-label", "Show password");
        btn.innerHTML = '<i class="bi bi-eye"></i>';

        wrap.style.position = "relative";
        wrap.appendChild(btn);

        btn.addEventListener("click", function () {
            var hidden = input.type === "password";
            input.type = hidden ? "text" : "password";
            btn.innerHTML = hidden
                ? '<i class="bi bi-eye-slash"></i>'
                : '<i class="bi bi-eye"></i>';
            btn.setAttribute("aria-label", hidden ? "Hide password" : "Show password");
            input.focus();
        });
    });


    // ---- Live password rules + strength meter -------------------------
    // Mirror the validators in settings.py + accounts/validators.py.
    function rule(passes, label) { return { passes: passes, label: label }; }

    var SYMBOL_RE = /[!"#$%&'()*+,\-./:;<=>?@\[\\\]^_`{|}~]/;

    function commonPasswordHit(value) {
        // Tiny client-side dictionary - the server enforces the full
        // CommonPasswordValidator, this is purely for live feedback.
        var lower = value.toLowerCase();
        var weak = [
            "password", "qwerty", "letmein", "admin", "welcome",
            "iloveyou", "monkey", "dragon", "abc123", "12345"
        ];
        for (var i = 0; i < weak.length; i++) {
            if (lower.indexOf(weak[i]) !== -1) return weak[i];
        }
        return null;
    }

    function evaluate(value, similarTo) {
        var rules = [
            rule(value.length >= 10,           "At least 10 characters"),
            rule(/[A-Z]/.test(value),          "Contains an uppercase letter (A-Z)"),
            rule(/[a-z]/.test(value),          "Contains a lowercase letter (a-z)"),
            rule(/[0-9]/.test(value),          "Contains a digit (0-9)"),
            rule(SYMBOL_RE.test(value),        "Contains a symbol (! @ # $ % etc.)"),
            rule(value.length === 0 || !/\s/.test(value),
                                               "No spaces or tabs"),
            rule(commonPasswordHit(value) === null,
                                               "Not a common / dictionary word"),
        ];
        if (similarTo) {
            similarTo.split(/[\s@.,;]+/).forEach(function (token) {
                if (token.length >= 4) {
                    rules.push(rule(
                        value.toLowerCase().indexOf(token.toLowerCase()) === -1,
                        "Doesn't repeat \"" + token + "\""
                    ));
                }
            });
        }
        return rules;
    }

    function strengthScore(value) {
        // 0..4 score loosely modelled on the NIST diversity bonuses.
        if (!value) return 0;
        var s = 0;
        if (value.length >= 10) s++;
        if (value.length >= 14) s++;
        if (/[A-Z]/.test(value) && /[a-z]/.test(value)) s++;
        if (/[0-9]/.test(value) && SYMBOL_RE.test(value)) s++;
        if (commonPasswordHit(value)) s = Math.max(0, s - 2);
        return Math.min(s, 4);
    }

    var STRENGTH_LABELS = ["Too weak", "Weak", "Okay", "Strong", "Very strong"];
    var STRENGTH_COLOURS = ["#dc2626", "#d97706", "#ca8a04", "#1f9d55", "#16a34a"];

    function setupMeter(input) {
        var meter = document.createElement("div");
        meter.className = "on-pw-meter";
        meter.innerHTML =
            '<div class="on-pw-meter-bar"><div class="on-pw-meter-fill"></div></div>' +
            '<small class="on-pw-meter-label text-muted">Type a password</small>';
        input.parentNode.parentNode.insertBefore(meter, input.parentNode.nextSibling);
        return meter;
    }

    document.querySelectorAll("[data-pw-rules]").forEach(function (input) {
        var listId = input.getAttribute("data-pw-rules");
        var list = document.getElementById(listId);
        if (!list) return;

        var meter = setupMeter(input);
        var fill = meter.querySelector(".on-pw-meter-fill");
        var label = meter.querySelector(".on-pw-meter-label");

        function refresh() {
            var similarTo = "";
            (input.getAttribute("data-pw-similar-to") || "")
                .split(",")
                .forEach(function (sel) {
                    sel = sel.trim();
                    if (!sel) return;
                    var other = document.querySelector(sel);
                    if (other && other.value) similarTo += " " + other.value;
                });

            var rules = evaluate(input.value, similarTo);
            list.innerHTML = "";
            rules.forEach(function (r) {
                var li = document.createElement("li");
                li.className = "on-rule " + (r.passes ? "ok" : "miss");
                li.innerHTML =
                    '<i class="bi ' + (r.passes ? "bi-check-circle-fill" : "bi-circle") +
                    '"></i> ' + r.label;
                list.appendChild(li);
            });

            var score = strengthScore(input.value);
            var pct = (score / 4) * 100;
            fill.style.width = pct + "%";
            fill.style.background = STRENGTH_COLOURS[score];
            label.textContent = input.value
                ? "Strength: " + STRENGTH_LABELS[score]
                : "Type a password";
        }

        input.addEventListener("input", refresh);
        (input.getAttribute("data-pw-similar-to") || "")
            .split(",").forEach(function (sel) {
                sel = sel.trim();
                if (!sel) return;
                var other = document.querySelector(sel);
                if (other) other.addEventListener("input", refresh);
            });
        refresh();
    });
})();
