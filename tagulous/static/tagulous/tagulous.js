/*****************************************************************************
** Common tagulous functionality
*****************************************************************************/

var Tagulous = (function () {
    
    /**************************************************************************
    ** Port of utils.py
    */
    
    // Constants to improve legibility
    var COMMA = ',',
        SPACE = ' ',
        QUOTE = '"'
    ;
    
    function parseTags(str) {
        // Empty string is easy
        if (!str) {
            return [];
        }
        
        // Prep vars for parser
        var tags = [],
            tag = '',
            delimiter = SPACE,
            strLen = str.length,
            strLast = strLen - 1,
            index, inQuote, chr, tagLen, leftCount, rightCount
        ;
        
        // Loop through chars
        for (index=0; index<strLen; index++) {
            chr = str[index];
            
            // See if it's a delimiter
            if (!inQuote) {
                // Comma delimiter takes priority
                if (delimiter !== COMMA && chr === COMMA) {
                    delimiter = COMMA;
                    
                    // All previous tags were actually just one tag
                    tag = str.substring(0, index).replace(/^ +| +$/g, '');
                    tags = [];
                    
                    // Strip start/end quotes
                    tagLen = tag.length;
                    tag = tag.replace(/^"+/, '');
                    leftCount = tagLen - tag.length;
                    tagLen = tag.length;
                    tag = tag.replace(/"+$/, '');
                    rightCount = tagLen - tag.length;
                    
                    // Escape inner quotes
                    tag = tag.replace(QUOTE + QUOTE, QUOTE);
                    
                    // Add back escaped start/end quotes
                    tag = Array(Math.floor(leftCount / 2) + 1).join(QUOTE) +
                        tag +
                        Array(Math.floor(rightCount / 2) + 1).join(QUOTE)
                    ;
                    
                    // Add back insignificant unquoted quotes
                    if (leftCount % 2 == 1) {
                        if (rightCount % 2 != 1) {
                            tag = QUOTE + tag;
                        }
                    } else if (rightCount % 2 == 1) {
                        tag += QUOTE;
                    }
                }
                
                // Found end of tag
                if (chr === delimiter) {
                    tag = tag.replace(/ +$/, '');
                    if (tag) {
                        tags.push(tag);
                        tag = '';
                    }
                    continue;
                }
                
                // If tag is empty, ignore whitespace
                if (!tag && chr === SPACE) {
                    continue;
                }
            }
            
            
            // Now either in a quote, or not a delimiter
            // If it's not a quote, add to tag
            if (chr != QUOTE) {
                tag += chr;
                continue;
            }
            
            // Char is quote - count how many quotes appear here and skip them
            leftCount = 1;
            while (index < strLast && str[index + 1] == QUOTE) {
                leftCount++;
                index++;
            }
            
            if (!tag) {
                // Quote at start
                // If an odd number, now in quote
                if (leftCount % 2 == 1) {
                    inQuote = true;
                }
                
                // Tag starts with escaped quotes
                tag = Array(Math.floor(leftCount / 2) + 1).join(QUOTE);
            } else {
                // Quote in middle or at end
                // Add any escaped
                tag += Array(Math.floor(leftCount / 2) + 1).join(QUOTE);
                
                // An odd number followed by a delimiter will mean it has ended
                // Need to look ahead to figure it out
                if (leftCount % 2 == 1) {
                    // If it's the last character, it has closed
                    if (index == strLast) {
                        inQuote = false;
                        break;
                    }
                    
                    for (var i2=index + 1, c2; i2<strLen; i2++) {
                        c2 = str[i2];
                        if (c2 == SPACE) {
                            if (delimiter == SPACE) {
                                // Quotes closed; tag will end next loop
                                inQuote = false;
                                break;
                            } else {
                                // Spaces are insignificant during whitespace
                                // Tag may continue, keep checking chars
                                continue;
                            }
                        } else if (c2 == COMMA) {
                            // Quotes closed; tag will end next loop
                            // Delimiter doesn't matter, comma always wins
                            inQuote = false;
                            break;
                        }
                        
                        // Tag has not ended
                        // Add odd quote to tag and keep building
                        tag += QUOTE;
                        break;
                    }
                }
            }
        }
        
        // Chars expanded
        if (tag) {
            // Partial tag remains; add to stack
            if (inQuote) {
                // Add the quote back to the start - it wasn't significant
                tag = QUOTE + tag;
            }
            tags.push(tag);
        }
        
        // Enforce uniqueness and sort
        for (var unique={}, finalTags=[], i=0, l=tags.length; i<l; i++) {
            if (!unique[tags[i]]) {
                finalTags.push(tags[i]);
                unique[tags[i]] = true;
            }
        }
        finalTags.sort();
        
        return finalTags;
    }
    
    
    function renderTags(tags) {
        var safe = [], i, str;
        for (i=0; i<tags.length; i++) {
            str = tags[i].replace(/"/g, QUOTE + QUOTE);
            if (str.indexOf(COMMA) > -1 || str.indexOf(SPACE) > -1) {
                safe.push(QUOTE + str + QUOTE);
            } else {
                safe.push(str);
            }
        }
        safe.sort();
        return safe.join(', ');
    }
    
    
    return {
        parseTags: parseTags,
        renderTags: renderTags
    };
})();
