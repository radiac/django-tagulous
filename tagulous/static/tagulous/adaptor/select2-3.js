/** Tagulous adaptor for Select2 */
(function ($) {
    if (!window.Select2 || !window.Tagulous) {
        return;
    }
    
    /** Select2 monkeypatching
        Adds support for new option, quotedTags
        
        This is used by tagulous to add quote support to the tag parser,
        without affecting other use of select2 on the page.
    */
    var MultiSelect2 = Select2['class'].multi,
        oldGetVal = MultiSelect2.prototype.getVal,
        oldSetVal = MultiSelect2.prototype.setVal
    ;
    MultiSelect2.prototype.getVal = function () {
        /** Parse tag string into tags */
        if (this.select || !this.opts.quotedTags) {
            return oldGetVal.call(this);
        }
        return Tagulous.parseTags(
            this.opts.element.val(), this.opts.spaceDelimiter
        );
    };
    MultiSelect2.prototype.setVal = function (val) {
        /** Join tags into a string */
        if (this.select || !this.opts.quotedTags) {
            return oldSetVal.call(this, val);
        }
        
        var str = Tagulous.renderTags(val);
        this.opts.element.val(str);
    };
    
    /** Select2 option functions
        
        These replace default options with quote-aware ones
    */
    function initSelectionSingle(element, callback) {
        var val = element.val();
        callback({id: val, text: val});
    }
    function initSelectionMulti_factory(opts) {
        /** initSelection has no way to get options, so need to use closure */
        return function (element, callback) {
            /** Initialises selection for fields with multiple tags */
            var tags = Tagulous.parseTags(element.val(), opts.spaceDelimiter),
                data = [],
                i
            ;
            for (i=0; i<tags.length; i++) {
                data.push({id: tags[i], text: tags[i]});
            }
            callback(data);
        };
    }
    
    function tokenizer(input, selection, selectCallback, opts) {
        /** Tokenises input and detects when a tag has been completed */
        if (!this.opts.quotedTags) {
            return $.fn.select2.defaults.tokenizer.call(
                this, input, selection, selectCallback, opts
            );
        }
        
        // Still need to be able to create search options
        if (!opts.createSearchChoice) return undefined;
        
        // Parse with raw
        var parsed = Tagulous.parseTags(input, opts.spaceDelimiter, true),
            tags = parsed[0],
            raws = parsed[1],
            lastRaw = raws.slice(-1)[0],
            i, token
        ;
        
        if (!tags.length) {
            return input;
        }
        
        if (lastRaw === null) {
            // Last tag wasn't completed
            tags.pop();
            raws.pop();
            lastRaw = raws.slice(-1)[0];
        }
        
        for (i=0; i<tags.length; i++) {
            token = opts.createSearchChoice.call(this, tags[i], selection);
            
            // De-dupe using select2 logic (without equal call)
            if (token !== undefined && token !== null && opts.id(token) !== undefined && opts.id(token) !== null) {
                dupe = false;
                for (i = 0, l = selection.length; i < l; i++) {
                    if (opts.id(token) === opts.id(selection[i])) {
                        dupe = true; break;
                    }
                }

                if (!dupe) selectCallback(token);
            }
            // End select2 dedupe logic
        }
        
        // Return whatever was left after the last completed tag was parsed
        return (lastRaw === undefined) ? input : lastRaw;
    }
    
    function createSearchChoice(term, data) {
        /** Creates quote-aware search options from new input
            
            Also makes SingleTagField look like a select field
        */
        // Thanks to https://github.com/select2/select2/issues/521
        if (this.opts.multiple && this.opts.quotedTags) {
            var tags = Tagulous.parseTags(term, this.opts.spaceDelimiter);
            if (tags.length == 1) {
                term = tags[0];
            }
        }
        if ($(data).filter(
            function () {
                return this.text.localeCompare(term) === 0;
            }).length === 0
        ) {
            return {id:term, text:term};
        }
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
            // Our overriden methods
            tokenizer: tokenizer,
            createSearchChoice: createSearchChoice,
            
            // Things defined by field/tag options, which can't be overridden
            multiple: !isSingle,
            quotedTags: true,
            allowClear: !options.required,
            maximumSelectionSize: isSingle ? 1 : options.max_count || 0,
            spaceDelimiter: options.space_delimiter !== false
        });
        
        // Add in any specific to the field type
        if (isSingle) {
            args['initSelection'] = initSelectionSingle;
        } else {
            args['initSelection'] = initSelectionMulti_factory(args);
        }
        if (url) {
            args['ajax'] = {
                url: url,
                dataType: 'json',
                data: function (term, page) {
                    return {q:term, p:page};
                },
                results: function (data) {
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
            args['tags'] = list || [];
        }
        
        // Initialise
        return $el.select2(args);
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
})(jQuery);
