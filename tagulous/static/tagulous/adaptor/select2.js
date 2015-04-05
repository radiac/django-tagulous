/** Tagulous adaptor for Select2 */
(function () {
    if (!window.Select2 || !window.Tagulous) {
        return;
    }
    
    /** Select2 monkeypatching */
    // ++ Add support for new option - quotedTags
    // ++ New getVal/setVal check for !this.select and this.opts.quotes
    //    then pass off into new code, otherwise call old code
    var MultiSelect2 = Select2['class'].multi,
        oldGetVal = MultiSelect2.prototype.getVal,
        oldSetVal = MultiSelect2.prototype.setVal
    ;
    MultiSelect2.prototype.getVal = function () {
        if (this.select && !this.opts.quotes) {
            return oldGetVal.call(this);
        }
        return Tagulous.parseTags(this.opts.element.val());
    };
    MultiSelect2.prototype.setVal = function (val) {
        if (this.select && !this.opts.quotes) {
            return oldSetVal.call(this, val);
        }
        // ++ Join tags into a string
        // ++ port utils.render_tags
        var unique = [],
            valMap = {},
            selector = this.opts.separator,
            name, i
        ;
        // Filter out duplicates
        $(val).each(function () {
            name = this;
            // Escape them
            for (i=0; i<tokenSeparators.length; i++) {
                if (name.indexOf(tokenSeparators[i]) !== -1) {
                    name = '"' + name + '"';
                    break;
                }
            }
            if (!(name in valMap)) {
                unique.push(name);
                valMap[name] = 0;
            }
        });
        this.opts.element.val(
            unique.length === 0 ? "" : unique.join(this.opts.separator)
        );
    };
    function tokenizer(input, selection, selectCallback, opts) {
        // Same conditions as normal
        if (!opts.createSearchChoice || !opts.tokenSeparators || opts.tokenSeparators.length < 1) return undefined;
        // ++ notice if it starts with quotes and handle differently
        return $.fn.select2.defaults.tokenizer(
            input, selection, selectCallback, opts
        );
    }
        
    function select2(el) {
        // Convert element to jQuery object
        var $el = $(el),
            thisTagField = this,
            
            // Get info from element
            isSingle = $el.data('tag-type') === "single",
            options = $el.data('tag-options') || {},
            list = $el.data('tag-list'),
            url = $el.data('tag-url'),
            
            // Other values
            $blank, args, field_args
        ;
        
        // Clear out first option if it's Django's blank value
        $blank = $el
            .find('option:first[value=""]:contains("---------")')
            .text('')
        ;
        
        // Default constructor args
        args = {
            maximumSelectionSize: isSingle ? 1 : options.max_count || 0,
            allowClear: !options.required,
            multiple: !isSingle,
            tokenSeparators: [',', ' '],
            tokenizer: tokenizer
        };
        
        // Merge in any overrides
        field_args = options.autocomplete_settings;
        if (field_args) {
            $.extend(args, field_args);
        }
        
        // SingleTagField should look like a select field
        // Thanks to https://github.com/select2/select2/issues/521
        if (isSingle) {
            args['createSearchChoice'] = function (term, data) {
                if ($(data).filter(
                    function () {
                        return this.text.localeCompare(term) === 0;
                    }).length === 0
                ) {
                    return {id:term, text:term};
                }
            };
        } else {
            // Select2 doesn't understand quotes and doesn't allow us to
            // override the things we need to, so we have to use a character
            // we hope won't appear in any tags
            
        }
        
        // Merge in compulsory settings
        args['quotes'] = true;
        if (url) {
            args['ajax'] = {
                url: url,
                dataType: 'json',
                data: function (term, page) {
                    return {q:term, p:page};
                },
                results: function (data) {
                    if (isSingle) {
                        // Not in tags mode
                        data['results'] = listToData(data['results']);
                    }
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
        $el.select2(args);
    }
    
    function listToData(list) {
        /** Convert a list of tags into an object with tag:tag key/vals */
        var data = [], i;
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
        $('input[data-tagulous]')
            // Initialise tag fields which exists
            .each(function () {
                Tagulous.select2(this);
            })
        ;
        
        this.raise.error()
    });
})();


