$(function () {
    /*
    ** Variables which should probably be customisable
    */
    var ajaxDelayTime=0,    // Delay before issuing an AJAX request
        maxHeight = 5,      // Maximum height of dropdown, as number of items
        minChars = 0        // Minimum number of characters for an AJAX request
    ;
    
    
    /*
    ** Library code
    */
    
    function trim(str) {
        return str.replace(/^ +/, '').replace(/ +$/, '');
    }
    
    function stripSplit(str, delim) {
        /* Based on django-taggit and django-tagging */
        if (!str) {
            return [];
        }
        
        var word, words = [], parts = str.split(delim);
        for (var i=0; i<parts.length; i++) {
            word = trim(parts[i]);
            if (word) {
                words.push(word);
            }
        }
        return words;
    }
        
        
    function parseTagString(str) {
        // If there are no commas or double quotes, just split on spaces
        if (str.indexOf(',') == -1 && str.indexOf('"') == -1) {
            return stripSplit(str, ' ');
        }
        
        var words = [],
            buffer = '',
            to_be_split = [],
            saw_loose_comma = false,
            open_quote = false
        ;
        
        for (var i=0; i<str.length; i++) {
            c = str[i];
            
            // Quote
            if (c == '"') {
                // Check if this is a closing quote
                if (open_quote) {
                    // Add the buffer to words
                    if (buffer) {
                        word = trim(buffer);
                        if (word) {
                            words.push(word);
                        }
                        buffer = '';
                    }
                    // Close the quote
                    open_quote = false;
                    continue;
                }
                
                // Quote just opened; defer splitting of non-quoted sections
                // until we know if there are any unquoted commas.
                if (buffer) {
                    to_be_split.push(buffer);
                    buffer = '';
                }
                
                // Open the quote
                open_quote = true;
                continue;
                
            // In a quote
            } else if (open_quote) {
                buffer += c;
                
            // Outside a quote
            } else {
                if (!saw_loose_comma && c == ',') {
                    saw_loose_comma = true;
                }
                buffer += c;
            }
        }
        
        /*
        // Original Python implementation
        // If we were parsing an open quote which was never closed, treat the
        // buffer as unquoted.
        if (buffer) {
            if (open_quote && buffer.indexOf(',') > -1) {
                saw_loose_comma = true;
            }
            to_be_split.push(buffer);
        }
        */
        // This part differs from the Python implementation
        if (buffer) {
            if (open_quote) {
                // If we were parsing an open quote which was never closed,
                // assume the user is going to close it.
                // It can't be incorrect from the server.
                words.push(buffer);
            } else {
                // Otherwise it needs to be split
                to_be_split.push(buffer);
            }
        }
        
        // If there's anything else to split, split it
        if (to_be_split.length > 0) {
            var delim = (saw_loose_comma) ? ',' : ' ';
            for (var j=0; j<to_be_split.length; j++) {
                words = words.concat(
                    stripSplit(to_be_split[j], delim)
                );
            }
        }
        
        return words;
    }
    
    function getCaretIndex($el) {
        var field = $el.get(0),
            index = 0
        ;
        
        // IE
        if (document.selection) {
            var sel = document.selection.createRange();
            sel.moveStart('character', -field.value.length);
            index = sel.text.length;

        // Firefox
        } else if (field.selectionStart || field.selectionStart == '0') {
            index = field.selectionStart;
        }
        
        return index;
    }
    
    // From https://gist.github.com/1007907
    function setCaretIndex($el, index) {
        el = $el.get(0);
        if (el.createTextRange) {
            var range = el.createTextRange();
            range.move("character", index);
            range.select();
        } else if (el.selectionStart != null) {
            el.focus();
            el.setSelectionRange(index, index);
        }
    }
    
    
    /*
    ** Dropdown class
    */
    var Dropdown = function () {
        // Build the elements
        this.$root = $('<div/>')
            .addClass('tagulous_dropdown')
        ;
        this.$ul = $('<ul/>')
            .appendTo(this.$root)
        ;
        this.clear();
        this.isOpen = false;
    };
    Dropdown.prototype = {
        clear: function () {
            this.items = [];
            this.index = 0;
            this.$ul.empty();
            this._show();
        },
        add: function (label) {
            var thisDropdown = this,
                thisIndex = this.items.length
            ;
            var $li = $('<li/>')
                .appendTo(this.$ul)
            ;
            this.items.push(
                $('<span href="#">' + label + '</span>')
                    .mouseover(function () {
                        thisDropdown.jump(thisIndex);
                    })
                    .mousedown(function (e) {
                        // Prevent dragging and focus
                        e.preventDefault();
                    })
                    .click(function (e) {
                        e.preventDefault();
                        thisDropdown.jump(thisIndex);
                        thisDropdown.select();
                    })
                    .appendTo($li)
            );
            this._show();
        },
        init: function ($el, selectFn) {
            // Position the dropdown underneath the specified element
            this.selectFn = selectFn;
            
            var position = $el.position();
            var offsetParent = $el.offsetParent();
            this.$root
                .insertAfter($el)
                .css({
                    'top':  (position.top + offsetParent.scrollTop() + $el.outerHeight()) + 'px',
                    'left': (position.left + offsetParent.scrollLeft()) + 'px',
                    'width': $el.outerWidth()
                })
            ;
        },
        open: function () {
            // Open it
            this.isOpen = true;
            this._show();
        },
        _show: function () {
            // Control whether it is visible or not
            var count = this.items.length;
            if (this.isOpen && count > 0) {
                this.$root.show();
                this.jump(0);
                if (count <= maxHeight) {
                    this.$root
                        .height(this.$ul.outerHeight())
                        .css('overflow', 'hidden')
                    ;
                } else {
                    var itemHeight = this.items[0].outerHeight();
                    this.$root
                        .height(itemHeight * (count + 0.5))
                        .css('overflow-y', 'scroll')
                    ;
                }
            } else {
                this.$root.hide();
            }
        },
        close: function () {
            this.$root.hide();
        },
        jump: function (index) {
            // Jump to an index
            this.items[this.index].removeClass('selected');
            this.index = index;
            this.items[this.index].addClass('selected');
        },
        up: function () {
            // Move selection up
            if (this.index == 0) {
                return;
            }
            this.jump(this.index - 1);
        },
        down: function () {
            // Move selection down
            if (this.index >= this.items.length - 1) {
                return;
            }
            this.jump(this.index + 1);
        },
        select: function () {
            // Action selection
            if (this.selectFn) {
                this.selectFn(this.items[this.index].text());
            }
            this.close();
        }
    };
    
    
    /*
    ** Autocomplete class
        options
            known           List of all known values
            url             URL to JSON autocomplete
            caseSensitive   Whether the lookup should be case sensitive
            action          A callback to use instead of replacing the input
                            value, once a suggestion is selected
    */
    
    var ajaxDelayTimer;
    var AutoComplete = function ($el, options) {
        if (!options) {
            options = {};
        }
        this.options = options;
        this.known = options.known || [];
        this.url = options.url || '';
        this.caseSensitive = options.caseSensitive || false;
        this.urlCache = {};
        this.$el = $el;
        this.last = '';
        this.requestId = 0;
        
        // Prepare the known values for matching
        if (this.known.length > 0 && !this.options.caseSensitive) {
            // They are not case sensitive, match using lower case
            this.match = [];
            for (var i=0; i<this.known.length; i++) {
                this.match.push(this.known[i].toLowerCase());
            }
        } else {
            this.match = this.known;
        }
        
        // Initialise display
        this.init();
    };
    AutoComplete.prototype = {
        /*
        Attributes:
        known       List of all known values
        match       A copy of `known` used to match
                    Will be in lower case if not case sensitive
        $el         Current input html element
        last        Last value
        requestId   ID of current request to autocomplete url
        url         URL to JSON autocomplete query service
        urlCache    Cache of requested queries
        */
        init: function () {
            // Create the dropdown
            this.dropdown = new Dropdown();
        },
        
        // Events
        focus: function (e) {
            this.open();
        },
        blur: function (e) {
            this.close();
        },
        keypress: function (e) {
            // Handle special keypresses immediately
            var processed = false;
            
            // Up
            if (e.keyCode == 38) {
                processed = true;
                this.up();
            
            // Down
            } else if (e.keyCode == 40) {
                processed = true;
                this.down();
            
            // Enter
            } else if (e.keyCode == 13) {
                processed = true;
                this.select();
            
            // Tab
            } else if (e.keyCode == 9) {
                // Be careful not to interrupt this one
                return;
            }
            
            if (processed) {
                e.preventDefault();
                return;
            }
            
            // Otherwise process the keypress after a brief delay, to allow the
            // field to update
            var thisAC = this;
            setTimeout(function () {
                thisAC.update();
            }, 0);
        },
        
        // Ops
        open: function () {
            /** Initialise and display render area */
            var thisAC = this;
            this.dropdown.init(this.$el, function (str) {
                thisAC.action(str);
            });
            this.dropdown.open();
            this.update();
        },
        up: function () {
            /** Up arrow pressed */
            this.dropdown.up();
        },
        down: function () {
            /** Down arrow pressed */
            this.dropdown.down();
        },
        update: function () {
            /** The string may have changed - collect, look up and render */
            var str = this.collect();
            
            // No need to do anything if the value hasn't changed
            //if (str == this.last) {
            //    return;
            //}
            this.last = str;
            
            // Look up the string
            this.lookup(str);
        },
        collect: function () {
            /** Collect the value from the input area */
            return this.$el.val();
        },
        lookup: function (str) {
            /** Look up the value in internal list or using JSON url */
            // If not case-sensitive, match on lower case
            if (!this.caseSensitive) {
                str = str.toLowerCase();
            }
            
            // Check URL
            if (this.url) {
                // Character limit
                if (str.length < minChars) {
                    return;
                }
                
                // Check the cache
                if (this.urlCache.hasOwnProperty(str)) {
                    return done(this.urlCache[str]);
                }
                
                // Touch the cache so we don't send two identical requests
                this.urlCache[str] = [];
                
                // Going to need to make a request
                var id = ++this.requestId;
                var thisAC = this;
                
                // Delay ajax so we don't hammer the server too hard
                if (ajaxDelayTimer) {
                    clearTimeout(ajaxDelayTimer);
                }
                ajaxDelayTimer = setTimeout(function () {
                    $.ajax({
                        url:    thisAC.url,
                        data:   {q: str},
                        cache:  false,
                        dataType: 'json'
                    }).done(function (response) {
                        // Check there are some results in the response
                        if (response && response.results) {
                            // Cache them
                            thisAC.urlCache[str] = response.results;
                            
                            // Check this is the response we're expecting
                            if (id != thisAC.requestId) {
                                return;
                            }
                            
                            // Return the results
                            thisAC.render(response.results);
                        }
                    }).fail(function(jqXHR, textStatus) {
                        // Clear the cache so it can be re-sent
                        delete(thisAC.urlCache[str]);
                    });
                }, ajaxDelayTime);
            
            // Otherwise use known list
            } else {
                // Naive algorithm for matching against known values
                var suggestions = [];
                for (var i=0; i<this.known.length; i++) {
                    if (this.match[i].indexOf(str) == 0) {
                        suggestions.push(this.known[i]);
                    }
                }
                this.render(suggestions);
            }
        },
        render: function (suggestions) {
            /** Show the suggestions in the render area */
            this.dropdown.clear();
            for (var i=0; i<suggestions.length; i++) {
                this.dropdown.add(suggestions[i]);
            }
        },
        select: function () {
            /** When an item is selected from the input (by keypress) */
            this.dropdown.select();
        },
        action: function (newStr) {
            /** Replace the value with the new one */
            if (this.options.action) {
                this.options.action(newStr);
            } else {
                this.$el.val(newStr).change();
            }
        },
        close: function () {
            /** Shut down and hide the render area */
            // Lost focus
            this.dropdown.close();
            this.last = '';
        }
    };
    
    
    /*
    ** TagField class
    
    Element $el will be updated by getField, so a TagField instance can be
    shared between cloned HTML elements
    */
    var TagField = function (id, $el) {
        this.id = id;
        this.options = $el.data('tag-options') || {};
        AutoComplete.call(this, $el, {
            known:  $el.data('tag-autocomplete') || [],
            url:    $el.data('tag-autocomplete-url') || '',
            caseSensitive: this.options.case_sensitive
        });
        this.isSingle = ($el.data('tag-autocomplete-type') == 'single');
        
        // Tag will need to keep track of last parse; .last will be last tag
        this.lastParse = {};
    };
    
    TagField.prototype = $.extend({}, AutoComplete.prototype, {
        keypress: function (e) {
            // Suppress " if in single tag mode
            if (this.isSingle && e.which == 34) {
                e.preventDefault();
                return;
            }
            
            // Force lowercase of alpha chars
            if (this.options.force_lowercase && e.which >= 65 && e.which <= 90) {
                // Suppress the uppercase
                e.preventDefault();
                
                // Find caret position and current element value
                var caretIndex = getCaretIndex(this.$el),
                    value = this.$el.val();
                ;
                
                // Insert lowercase character into string and jump caret
                this.$el.val(
                    value.substr(0, caretIndex)
                    + String.fromCharCode(e.which + (97-65))
                    + value.substr(caretIndex)
                );
                setCaretIndex(this.$el, caretIndex+1);
            }
            
            // AutoComplete the change
            AutoComplete.prototype.keypress.call(this, e);
        },
        collect: function () {
            var caretIndex = getCaretIndex(this.$el),
                str = this.$el.val(),
                tags, currentTag
            ;
            
            // Find tags and current tag
            if (str == this.lastParse.str && caretIndex == this.lastParse.caretIndex) {
                // Hasn't changed
                tags = this.lastParse.tags;
                currentTag = this.last;
                
            } else {
                var caretTagIndex;
                if (this.isSingle) {
                    // If the widget is in single mode, no need to parse
                    currentTag = str;
                    tags = [str];
                    caretTagIndex = caretIndex;
                } else {
                    // New string. Mark the caret location with a newline, then
                    // parse into tags
                    tags = parseTagString(
                        str.substr(0, caretIndex) + "\n" + str.substr(caretIndex)
                    );
                    
                    // Find the current tag and remove the newline
                    for (var i=0; i<tags.length; i++) {
                        caretTagIndex = tags[i].indexOf("\n");
                        if (caretTagIndex > -1) {
                            currentTag = tags[i].substr(0,caretTagIndex)
                                + tags[i].substr(caretTagIndex+1)
                            ;
                            break;
                        }
                    }
                }
                
                // Store
                this.lastParse = {
                    str:    str,
                    tags:   tags,
                    caretIndex: caretIndex,
                    caretTagIndex: caretTagIndex
                };
            }
            
            // Show warning for too many tags
            // ++
            
            return currentTag;
        },
        replace: function (newStr) {
            // Replace the current tag with the new one specified
            var lastParse = this.lastParse, str = lastParse.str;
            
            // Find the start of the tag
            var tagStart = lastParse.caretIndex - lastParse.caretTagIndex;
            
            // Get the text to the left and right of the old tag and replace it
            this.$el.val(
                str.substr(0, tagStart)
                + newStr
                + str.substr(tagStart + this.last.length)
            ).change();
        }
    });
    
    
    /*
    ** Field registry
    
    The registry uses IDs stored on the form elements.
    That way if a field is cloned on the page (eg an 'add' fieldset button),
    the ID will be cloned too, meaning the fields can share autocomplete cache.
    */
    
    // Registry of tag fields
    var registry = [];
    var next_id = 1;
    
    // Get a TagField for a given tagulous <input>
    function getField($el) {
        // See if it has already been initialised
        var id = $el.data('tagulous-id');
        if (id) {
            id = parseInt(id);
        } else {
            // New field, initialise
            id = next_id++;
            var field = new TagField(id, $el);
            registry[id] = field;
            $el.data('tagulous-id', id);
        }
        registry[id].$el = $el;
        return registry[id];
    }
    
    
    /*
    ** Element binding and initialisation
    */
    
    // Find tagulous tag fields
    $('input[data-tag-tagulous]')
        // Initialise tag fields which exists
        .each(function () {
            // Don't need to do anything with it yet, just initialise
            getField($(this));
        })
        // Watch for TagField events on existing and new fields
        .live('focus click', function (e) {
            // Initialise or retrieve TagField, then focus it
            getField($(this)).focus(e);
        })
        .live('blur', function (e) {
            getField($(this)).blur(e);
        })
        .live('keypress', function (e) {
            getField($(this)).keypress(e);
        })
        
    ;
});
