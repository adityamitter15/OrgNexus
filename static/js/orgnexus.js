// File: static/js/orgnexus.js - Aditya Mitter (W19869650)
// Tiny vanilla helpers - we keep JS minimal so the marker can read it
// without setting up a build step.

(function () {
    "use strict";

    // ---- Auto-dismiss flash messages ----------------------------------
    document.querySelectorAll(".alert.on-alert").forEach(function (el) {
        if (el.classList.contains("alert-danger") || el.classList.contains("alert-error")) {
            return; // leave errors visible until the user acts on them
        }
        setTimeout(function () {
            el.style.transition = "opacity .4s";
            el.style.opacity = "0";
            setTimeout(function () { el.remove(); }, 400);
        }, 4000);
    });


    // ---- Show/hide password toggle ------------------------------------
    // Markup: wrap the input in <div class="on-pw-wrap">…</div> and the
    // JS injects an eye button. We don't add the button server-side so
    // the form stays clean if JS is disabled.
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


    // ---- Live password rules ------------------------------------------
    // Mirrors the validators in settings.py:
    //   - at least 10 characters
    //   - contains a letter
    //   - contains a digit
    //   - not entirely numeric (covered by letter rule)
    //   - not too similar to username/email (best-effort only)
    function rule(passes, label) { return { passes: passes, label: label }; }

    function evaluate(value, similarTo) {
        var lower = value.toLowerCase();
        var rules = [
            rule(value.length >= 10,                 "At least 10 characters"),
            rule(/[A-Za-z]/.test(value),             "Contains a letter"),
            rule(/[0-9]/.test(value),                "Contains a digit"),
            rule(!/^\d+$/.test(value) && value.length > 0,
                                                     "Not entirely numbers"),
        ];
        if (similarTo) {
            similarTo.split(/[\s@.]+/).forEach(function (token) {
                if (token.length >= 4) {
                    rules.push(rule(
                        !lower.includes(token.toLowerCase()),
                        "Doesn't repeat \"" + token + "\""
                    ));
                }
            });
        }
        return rules;
    }

    document.querySelectorAll("[data-pw-rules]").forEach(function (input) {
        var listId = input.getAttribute("data-pw-rules");
        var list = document.getElementById(listId);
        if (!list) return;

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
        }

        input.addEventListener("input", refresh);
        // Also refresh when companion fields change so the
        // 'similar-to' rules update live.
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
