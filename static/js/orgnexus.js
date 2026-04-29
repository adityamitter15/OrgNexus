// File: static/js/orgnexus.js - Aditya Mitter (W19869650)
// Tiny vanilla helpers - we keep JS minimal so the marker can read it
// without setting up a build step.

(function () {
    "use strict";

    // Auto-dismiss flash messages after a few seconds so the page does
    // not stay cluttered after a successful action.
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
})();
