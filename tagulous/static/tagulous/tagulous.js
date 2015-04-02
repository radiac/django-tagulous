/*****************************************************************************
** Common tagulous functionality
*****************************************************************************/

var Tagulous = (function () {
    
    /**************************************************************************
    ** Port of python tag parser
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
    
    return {
        trim: trim,
        stripSplit: stripSplit,
        parseTagString: parseTagString
    };
})();
