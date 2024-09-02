/*!
 * jQuery BubbleTip Plugin v1.0.6
 * https://github.com/yourusername/jquery-bubbletip
 * 
 * Copyright 2013 Your Name
 * Released under the MIT license
 * https://opensource.org/licenses/MIT
 */
(function($) {
    $.fn.bubbleTip = function(options) {
        // Default settings
        var settings = $.extend({
            content: 'Tooltip content',
            position: 'top', // top, bottom, left, right
            offset: 10,
            backgroundColor: '#333',
            textColor: '#fff'
        }, options);

        // Function to create bubble tip
        function createBubbleTip(element) {
            var $element = $(element);
            var $bubble = $('<div class="bubble-tip"></div>').text(settings.content)
                .css({
                    'position': 'absolute',
                    'background-color': settings.backgroundColor,
                    'color': settings.textColor,
                    'padding': '5px',
                    'border-radius': '3px',
                    'display': 'none',
                    'z-index': 1000
                });
            
            $('body').append($bubble);

            var offset = $element.offset();
            var elementWidth = $element.outerWidth();
            var elementHeight = $element.outerHeight();
            var bubbleWidth = $bubble.outerWidth();
            var bubbleHeight = $bubble.outerHeight();

            // Positioning the bubble tip
            switch(settings.position) {
                case 'top':
                    $bubble.css({
                        'left': offset.left + (elementWidth / 2) - (bubbleWidth / 2),
                        'top': offset.top - bubbleHeight - settings.offset
                    });
                    break;
                case 'bottom':
                    $bubble.css({
                        'left': offset.left + (elementWidth / 2) - (bubbleWidth / 2),
                        'top': offset.top + elementHeight + settings.offset
                    });
                    break;
                case 'left':
                    $bubble.css({
                        'left': offset.left - bubbleWidth - settings.offset,
                        'top': offset.top + (elementHeight / 2) - (bubbleHeight / 2)
                    });
                    break;
                case 'right':
                    $bubble.css({
                        'left': offset.left + elementWidth + settings.offset,
                        'top': offset.top + (elementHeight / 2) - (bubbleHeight / 2)
                    });
                    break;
            }

            // Show the bubble tip on hover
            $element.hover(function() {
                $bubble.fadeIn();
            }, function() {
                $bubble.fadeOut();
            });
        }

        // Apply bubble tip to each selected element
        return this.each(function() {
            createBubbleTip(this);
        });
    };
}(jQuery));
