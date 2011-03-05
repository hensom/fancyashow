/**
 * Copyright (c) 2007 Ingo Schommer (www.chillu.com)
 * Licensed under the MIT License:
 * http://www.opensource.org/licenses/mit-license.php
 * 
 * Splits a /-list into equal-sized columns.
 * 
 * Requirements: 
 * 
 * All list-elements need to have the same height.
 * List has to be blocklevel
 * 
 * 
 * Caution: margin-top/margin-left on  are overridden.
 * Doesn't react to changes to the DOM, you need to call the function
 * manually afterwards.
 * 
 * @see http://www.alistapart.com/articles/multicolumnlists
 */
jQuery.fn.columnizeList = function(settings){
    settings = jQuery.extend({
        cols: 3,
        width: '13',
        unit: 'em'
    }, settings);

    var prevColNum = 0;
    var size = $('li',this).size();
    var computedColHeight = 0;
    var baseFontSize = parseFloat($(this).css('font-size'));
    var baseHeight   = $('li', this).first().outerHeight(true);
    var maxHeight    = 0;

    $('li',this).each(function(i) {
        var currentColNum = Math.floor(((i)/size) * settings.cols);
        $(this).css('margin-left',(currentColNum*settings.width)+''+settings.unit);
        if(prevColNum != currentColNum) {
            $(this).css('margin-top','-'+(computedColHeight)+'px');
            //computedColHeight = $(this).outerHeight(true);
            computedColHeight = baseHeight;
        } else {
            $(this).css('margin-top','0');
            //computedColHeight += $(this).outerHeight(true);
            computedColHeight += baseHeight;

        }

        prevColNum = currentColNum;
        maxHeight = (computedColHeight > maxHeight) ? computedColHeight : maxHeight;
    });

    this.css('height', maxHeight + 'px');
    this.after('');

    var onchange = function(e) {
        if(!e.originalTarget || e.originalTarget.tagName != 'LI') return true;
        var scope = this; // caution: closure
        setTimeout(function() {$(scope).columnizeList(settings);}, 50);
    };

    this.one('DOMNodeInserted',onchange);
    this.one('DOMNodeRemoved',onchange);

    return this;
};

jQuery.fn.uncolumnizeList = function(){
    $('li',this).each(function(i) {
        if(!$(this).attr('style')) return;
        $(this).attr('style', 
            $(this).attr('style')
            .replace(/margin\-left[^,]*/g,'')
            .replace(/margin\-top[^,]*/g,'')
        );
    });
    $('ul',this).each(function(i) {
        if(!$(this).attr('style')) return;
        $(this).attr('style', 
            $(this).attr('style')
            .replace(/[^-]height[^,]*/g,'')
        );
    });
    $(this).height('auto');
    this.unbind('DOMNodeInserted');
    this.unbind('DOMNodeRemoved');

    return this;
}
