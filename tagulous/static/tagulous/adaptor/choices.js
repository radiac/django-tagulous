document.addEventListener('DOMContentLoaded', () => {
  if (!window.Choices || !window.Tagulous) {
    console.log('not loaded');
    return;
  }

  const defaultSettings = {
    'silent': false,

  };
  function choices(elements) {
    elements.forEach((el) => {

      // Get settings from element
      const isSingle = ;
      const options = JSON.parse(el.dataset.tagOptions || "");
      const url = el.dataset.tagUrl;

      // Extract values
      const settings = options.autocomplete_settings || {};
      const spaceDelimiter = options.space_delimiter !== false;

      // Collect any existing values
      const [tags, raws] = Tagulous.parseTags(el.value, spaceDelimiter, true);

      if (el.dataset.tagType === "single") {
        // TODO: Untested
        settings.renderChoiceLimit = 1;
      }

      if (el.dataset.tagList) {
        // TODO: This doesn't work with text inputs
        settings.choices = JSON.parse(el.dataset.tagList).map(item => ({
          value: item,
          label: item,
          selected: tags.includes(item),
          disabled: false,
        }));
      }

      new Choices(el, settings);
    });
  }

  // Make functions public
  Tagulous.choices = choices;

  // Initialise tag fields which exists
  const inputSelector = 'input[data-tagulous]:not([id*=-__prefix__-])'
  const inputs = document.querySelectorAll(inputSelector);
  choices(inputs);

  // Watch for formsets
  document.addEventListener('formset:added', function (event, formset) {
    var inputs = formset.querySelectorAll(inputSelector);
    choices(inputs);
  });
});
