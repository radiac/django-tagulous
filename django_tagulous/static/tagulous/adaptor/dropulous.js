/**
 * Tagulous adaptor for Dropulous
 *
 * Subclasses Dropulous to use the Tagulous tag parser
 */

class TagulousDropulous extends Dropulous {

  constructor(field, options = {}) {
    super(field, options);
    this.spaceDelimiter = options.spaceDelimiter !== false;

    // Support delimiter detection in multiple mode
    if (this.isMultiple) {
      this.inputEl.addEventListener('input', () => this.handleLiveInput());
    }
  }

  // Parse a serialised tag string into an array of values
  parseValue(str) {
    return Tagulous.parseTags(str, this.spaceDelimiter);
  }

  // Reverse of parseValue() - serialise values back
  formatValue(values) {
    return Tagulous.renderTags(values);
  }

  // Detect delimited tags
  handleLiveInput() {
    const query = this.inputEl.value;
    if (!query) return;

    const [tags, raws] = Tagulous.parseTags(query, this.spaceDelimiter, true);
    if (!tags.length) return;

    // raws[i] is the remaining string after the delimiter that closed tags[i].
    // A null entry means the parser ran out of input - that tag is still being typed.
    const lastIsPartial = raws[raws.length - 1] === null;
    const completeTags = lastIsPartial ? tags.slice(0, -1) : tags;
    const partialTag = lastIsPartial ? tags[tags.length - 1] : '';

    if (!completeTags.length) return;

    // Select or add each completed tag
    completeTags.forEach(tag => {
      const existing = this.availableOptions.find(opt =>
        opt.value === tag ||
        opt.label.toLowerCase() === tag.toLowerCase()
      );
      if (existing) {
        this.selectOption(existing.value);
      } else if (this.canAdd) {
        this.addNewOption(tag);
      }
    });

    // selectOption() clears the input; restore any unfinished partial tag
    this.query = partialTag;
    this.inputEl.value = partialTag;

    // Re-render so the dropdown filters against the partial tag, not the full string
    this.render();
  }
}

function applyTagulousDropulous(el) {
  const tagOptions = JSON.parse(el.dataset.tagOptions || '{}');

  // Convert data-tag-list (array of strings) to data-options (dropulous format)
  // so collectOptions() picks them up for non-remote fields.
  if (el.dataset.tagList && !el.dataset.tagUrl) {
    el.dataset.options = JSON.stringify(
      JSON.parse(el.dataset.tagList).map(tag => ({ value: tag, label: tag }))
    );
  }

  new TagulousDropulous(el, {
    multiple: el.dataset.tagType !== 'single',
    canAdd: tagOptions.can_create !== false,
    spaceDelimiter: tagOptions.space_delimiter !== false,
    placeholder: tagOptions.placeholder || '',
    maxSelections: tagOptions.max_count || 0,
    source: el.dataset.tagUrl,
  });
}

const tagulousSelector = 'input[data-tagulous]:not([id*=-__prefix__-])';

document.addEventListener('DOMContentLoaded', () => {
  document.querySelectorAll(tagulousSelector).forEach(applyTagulousDropulous);
});

document.addEventListener('formset:added', event => {
  const root = event.detail?.formset ?? event.target;
  root.querySelectorAll(tagulousSelector).forEach(applyTagulousDropulous);
});
