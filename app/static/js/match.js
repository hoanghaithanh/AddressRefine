// Client-side-only interactions for the combined Method/Distance-function +
// live results table page (`algorithm.html`). No `fetch`/XHR calls here —
// HTMX attributes on the form controls already handle the live recompute and
// merge round-trips; this file only ever manipulates the DOM directly.

(function () {
  "use strict";

  /**
   * Filter the Distance-function <select>'s visible options to the selected
   * Method, and show/hide + relabel the parameter field accordingly. Param
   * metadata is read from `data-*` attributes rendered on each <option> by
   * the server (see `algorithm.html`).
   */
  function syncMethodAndDistanceFunction() {
    var methodField = document.getElementById("method");
    var algorithmField = document.getElementById("algorithm_key");
    if (!methodField || !algorithmField) {
      return;
    }

    var selectedMethod = methodField.value;
    var options = Array.prototype.slice.call(algorithmField.options);
    var visibleOptions = options.filter(function (option) {
      return option.dataset.family === selectedMethod;
    });

    options.forEach(function (option) {
      var visible = option.dataset.family === selectedMethod;
      option.hidden = !visible;
      option.disabled = !visible;
    });

    var currentlySelectedIsVisible = visibleOptions.some(function (option) {
      return option.value === algorithmField.value;
    });

    if (!currentlySelectedIsVisible && visibleOptions.length > 0) {
      algorithmField.value = visibleOptions[0].value;
    }

    syncParamField();
  }

  /**
   * Structurally add/remove and relabel the parameter field based on the
   * currently selected Distance function's param metadata. The field is
   * removed from the DOM entirely (not merely hidden via CSS) when the
   * selected Distance function has no parameters (plain Fingerprint).
   */
  function syncParamField() {
    var algorithmField = document.getElementById("algorithm_key");
    var matchControls = document.getElementById("match-controls");
    if (!algorithmField || !matchControls) {
      return;
    }

    var selectedOption = algorithmField.options[algorithmField.selectedIndex];
    if (!selectedOption) {
      return;
    }

    var paramName = selectedOption.dataset.paramName || "";
    var existingGroup = document.getElementById("param-field-group");
    var isNewlyCreated = false;

    if (!paramName) {
      if (existingGroup) {
        existingGroup.remove();
      }
      return;
    }

    if (!existingGroup) {
      isNewlyCreated = true;
      existingGroup = document.createElement("div");
      existingGroup.className = "control-group";
      existingGroup.id = "param-field-group";

      var label = document.createElement("label");
      label.id = "param-field-label";
      label.setAttribute("for", "param-field");

      var input = document.createElement("input");
      input.type = "number";
      input.id = "param-field";
      input.className = "field";
      input.step = "1";
      input.setAttribute("hx-post", "/algorithm/recompute");
      input.setAttribute("hx-target", "#results-table-container");
      input.setAttribute("hx-swap", "outerHTML");
      input.setAttribute("hx-include", "#match-controls");
      input.setAttribute("hx-trigger", "change");
      if (window.htmx) {
        window.htmx.process(input);
      }

      existingGroup.appendChild(label);
      existingGroup.appendChild(input);
      matchControls.querySelector(".control-row").appendChild(existingGroup);
    }

    var paramLabel = document.getElementById("param-field-label");
    var paramInput = document.getElementById("param-field");

    paramLabel.textContent = selectedOption.dataset.paramLabel || "";
    paramInput.name = paramName;

    if (selectedOption.value === "ncd") {
      paramInput.min = "1";
      paramInput.max = "10";
    } else if (selectedOption.value === "levenshtein") {
      paramInput.min = "0";
      paramInput.removeAttribute("max");
    } else {
      // ngram_fingerprint: n >= 1.
      paramInput.min = "1";
      paramInput.removeAttribute("max");
    }

    // Only reset to the algorithm's default when the field is newly created
    // (i.e. the user just switched to a Distance function that didn't
    // previously have a parameter field showing) or when its name changed
    // (switching between two parameterized algorithms, e.g. Levenshtein ->
    // NCD) — never overwrite a value the server already rendered for the
    // currently-selected algorithm on initial page load.
    if (isNewlyCreated || paramInput.dataset.boundParam !== paramName) {
      paramInput.value = selectedOption.dataset.paramDefault || "";
    }
    paramInput.dataset.boundParam = paramName;
  }

  /**
   * Wire up per-row interactions (AC-M4-21/22/23) for every row currently in
   * the results table. Safe to call repeatedly (e.g. after an HTMX swap
   * replaces the table) since it only attaches listeners to elements found
   * in the current DOM.
   */
  function bindResultsTable() {
    var rows = document.querySelectorAll(".pair-row");

    rows.forEach(function (row) {
      var checkbox = row.querySelector(".pair-row-checkbox");
      var newValueInput = row.querySelector(".pair-row-new-value");
      var pairIdField = row.querySelector(".pair-row-pair-id-field");
      var newValueField = row.querySelector(".pair-row-new-value-field");
      var addressButtons = row.querySelectorAll(".pair-row-address");

      if (!checkbox || !newValueInput || !pairIdField || !newValueField) {
        return;
      }

      function setSubmittedFieldsEnabled(enabled) {
        pairIdField.disabled = !enabled;
        newValueField.disabled = !enabled;
        newValueField.value = newValueInput.value;
      }

      // AC-M4-21: checking "Merge?" without a prior address click defaults
      // "New cell value" to the row's first-listed address.
      checkbox.addEventListener("change", function () {
        if (checkbox.checked && newValueInput.value === "") {
          var firstAddress = addressButtons.length > 0 ? addressButtons[0].dataset.address : "";
          newValueInput.value = firstAddress || "";
        }
        setSubmittedFieldsEnabled(checkbox.checked);
      });

      // AC-M4-22: clicking either address sets "New cell value" and
      // auto-checks "Merge?", regardless of its prior state.
      addressButtons.forEach(function (button) {
        button.addEventListener("click", function () {
          newValueInput.value = button.dataset.address || "";
          checkbox.checked = true;
          setSubmittedFieldsEnabled(true);
        });
      });

      // AC-M4-23: typing into "New cell value" is never overwritten, and
      // keeps the submitted hidden field's value in sync.
      newValueInput.addEventListener("input", function () {
        newValueField.value = newValueInput.value;
      });
    });
  }

  function init() {
    var methodField = document.getElementById("method");
    var algorithmField = document.getElementById("algorithm_key");

    if (methodField) {
      methodField.addEventListener("change", syncMethodAndDistanceFunction);
    }
    if (algorithmField) {
      algorithmField.addEventListener("change", syncParamField);
    }

    syncMethodAndDistanceFunction();
    bindResultsTable();
  }

  document.addEventListener("DOMContentLoaded", init);

  // Re-bind row interactions whenever HTMX swaps in a fresh results-table
  // partial (the Method/Distance-function controls themselves live outside
  // the swapped fragment, so they don't need re-binding).
  document.body.addEventListener("htmx:afterSwap", function (event) {
    if (event.target && event.target.id === "results-table-container") {
      bindResultsTable();
    }
  });

  // htmx 1.9.10's default responseHandling treats any 4xx/5xx response as
  // "don't swap" (it only fires htmx:responseError and leaves the DOM
  // untouched). Both POST /algorithm/recompute (AC-M4-9) and POST /merge
  // (AC-M4-34) deliberately return 422 with a flash-error fragment as the
  // response body, so we explicitly opt 422 responses back into swapping —
  // this is htmx's documented validation-response pattern.
  document.body.addEventListener("htmx:beforeSwap", function (event) {
    if (event.detail.xhr.status === 422) {
      event.detail.shouldSwap = true;
    }
  });
})();
