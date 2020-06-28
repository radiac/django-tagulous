/** Tagulous adaptor for Select2 v4 */
(function ($) {
  if (!$.fn.select2 || !window.Tagulous) {
    return;
  }
  var Tagulous = window.Tagulous;

  /**
   * Quote-aware data adapter
   */
  $.fn.select2.amd.require([
      'select2/data/tokenizer',
  ], function (Tokenizer) {

    function tokenizer(params, options, selectCallback) {
        /**
         * Tokenises input and detects when a tag has been completed
         */
        if (!options.get('quotedTags')) {
            // If not quoting tags, use the default tokenizer
            return Tokenizer.prototype.tokenizer.call(
                this, this, params, options, selectCallback
            );
        }

        // Parse with raw
        var term = params.term,
            parsed = Tagulous.parseTags(term, options.get('spaceDelimiter'), true),
            tags = parsed[0],
            raws = parsed[1],
            lastRaw = raws.slice(-1)[0],
            i
        ;

        if (!tags.length) {
            return {term: term};
        }

        // Check for incomplete partial tag
        // If more than one tag then raw was pasted - assume all complete
        if (lastRaw === null && tags.length < 2) {
          // Last tag wasn't completed - return it to input
          tags.pop();
          raws.pop();

          lastRaw = raws.slice(-1)[0];
        }

        for (i=0; i<tags.length; i++) {
          selectCallback({
            id: tags[i],
            text: tags[i]
          })
        }

        // Return whatever was left after the last completed tag was parsed
        return {
          term: (lastRaw === undefined) ? term : lastRaw
        };
    }

    /** Apply select2 to a specified element

        Arguments:
            el          The DOM or jQuery object to use as the tag element
            canDefer    If true and tag-options.defer is set, this field
                        will not be initialised.
    */
    function apply_select2(el, canDefer) {
        // Convert element to jQuery object (if it isn't already)
        var $el = $(el),
            thisTagField = this,

            // Get info from element
            isSingle = $el.data('tag-type') === "single",
            options = $el.data('tag-options') || {},
            settings = options.autocomplete_settings || {},
            list = $el.data('tag-list'),
            url = $el.data('tag-url'),

            // Other values
            $blank, args, field_args
        ;
        // See if this is a deferred tag
        if (canDefer && settings.defer) {
            return $el;
        }
        delete settings.defer;

        // Clear out first option if it's Django's blank value
        $blank = $el
            .find('option:first[value=""]:contains("---------")')
            .text('')
        ;

        // Default constructor args, which can be overridden
        args = {
            width: 'resolve'
        };

        // Merge in any overrides
        field_args = settings;
        if (field_args) {
            $.extend(args, field_args);
        }
        // Merge in common compulsory settings
        $.extend(args, {
            // Select2 options
            tokenizer: tokenizer,
            tags: true,

            // Things defined by field/tag options, which can't be overridden
            multiple: !isSingle,
            quotedTags: true,
            allowClear: !options.required,
            maximumSelectionLength: isSingle ? null : options.max_count || null,
            spaceDelimiter: options.space_delimiter !== false
        });

        // Add in any specific to the field type
        if (url) {
            args['ajax'] = {
                url: url,
                dataType: 'json',
                data: function (params) {
                    return {q:params.term, p:params.page};
                },
                processResults: function (data) {
                    data['results'] = listToData(data['results']);
                    return data;
                }
            };

            // Merge in override ajax values
            if (field_args && field_args.ajax) {
                $.extend(args['ajax'], field_args.ajax);
            }

        } else if (isSingle) {
            // Make SingleTagField look like a select, set data not tags
            args['data'] = listToData(list);

        } else {
            // Multiple tags, normal tags mode appropriate
            $.extend(args, {
              data: list || [],
            });
        }

        // Collect values
        var currentVal = $el.val();
        var selectedTags = [];
        if (isSingle) {
          if (currentVal) {
            selectedTags = [currentVal];
          }
        } else {
          selectedTags = Tagulous.parseTags(currentVal, args.spaceDelimiter);
        }

        /**
         * Convert <input> to <select>
         */
        var $inputEl = $el;
        var $selectEl = $('<select/>').width($el.width());

        // Swap in
        $selectEl.insertAfter($inputEl.hide());
        var $selectCtl = $selectEl.select2(args);

        if (selectedTags.length > 0) {
          var selectedData = [];
          for (var i=0; i<selectedTags.length; i++) {
            var option = new Option(selectedTags[i], selectedTags[0], true, true);
            $selectCtl.append(option).trigger('change');
            selectedData.push({id: selectedTags[i], text: selectedTags[i]});
          }

          $selectCtl.trigger({
            type: "select2:select",
            params: {
              data: selectedData,
            }
          });
        }

        // Ensure select2 data makes it back into the form field for submission
        $selectEl.on("change", function (e) {
          var valueObjects = $selectEl.select2('data');
          var values = valueObjects.map(function(obj) { return obj.text; });
          var rendered = Tagulous.renderTags(values);
          $inputEl.val(rendered);
        });
        return $selectCtl;
    }

    /** Select2 initialiser

        This initialises select2 on this

        Arguments:
            $el         The jQuery object to use as the tag selector
            canDefer    If true and tag-options.defer is set, this field
                        will not be initialised.
    */
    function select2($el, canDefer) {
        return $el.each(function () {
            apply_select2(this, canDefer);
        });
    }

    function listToData(list) {
        /** Convert a list of tags into an object with tag:tag key/vals */
        var data = [], i;
        if (!list) {
            return data;
        }
        for (i=0; i<list.length; i++) {
            data.push({id:list[i], text:list[i]});
        }
        return data;
    }

    // Make functions public
    $.extend(Tagulous, {
        select2: select2
    });

    // Finally, initialise the tags
    $(function () {
        // Initialise tag fields which exists
        return select2($('input[data-tagulous]'), true);
    });
  });
})(jQuery);
