/** Tagulous adaptor for Select2 */
(function () {
    if (!window.Tagulous) {
        return;
    }
    
    function setupTagField(el) {
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
            tokenSeparators: [',', ' ']
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
        }
        
        // Merge in compulsory settings
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
    
    
    $.extend(Tagulous, {
            // ++
    });
})();


$(function () {
    /** Initialise the tags */
    
    $('input[data-tagulous]')
        // Initialise tag fields which exists
        .each(function () {
            setupTagField(this);
        })
    ;
    
    this.raise.error()
});
