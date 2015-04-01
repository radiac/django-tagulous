/** Tagulous adaptor for Select2 */
$(function () {
    $('input[data-tagulous]')
        // Initialise tag fields which exists
        .each(function () {
            var $el = $(this),
                $blank = $el
                    .find('option:first[value=""]:contains("---------")')
                    .text('')
            ;
            $el
                // Clear out first option if it's the blank value
                .select2({
                    allowClear: $blank.length === 1,
                    width:      'resolve'
                })
            ;
        })
    ;
    return;
    
    // Clear out first option if it's ---------
    $sel.find('option:first[value=""]:contains("---------")').text('');
    
    $sel.select2({
        allowClear: true,
        //width:  'element',
        width:  'resolve',
        formatSelection: function (item, container) {
            var label = $(item.element[0]).parent('optgroup').attr('label');
            if (label) {
                return item.text + ' (' + label + ')';
            }
            return item.text;
        }
    });
});
