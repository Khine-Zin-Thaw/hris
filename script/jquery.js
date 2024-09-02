/*!
 * jQuery JavaScript Library v1.9.1
 * http://jquery.com/
 *
 * Includes Sizzle.js
 * http://sizzlejs.com/
 *
 * Copyright jQuery Foundation and other contributors
 * Released under the MIT license
 * http://jquery.org/license
 *
 * Date: 2013-02-04
 */
(function(global, factory) {
    if (typeof module === "object" && typeof module.exports === "object") {
        // Node.js or CommonJS
        module.exports = global.document ?
            factory(global, true) :
            function (w) {
                if (!w.document) {
                    throw new Error("jQuery requires a window with a document");
                }
                return factory(w);
            };
    } else {
        // Browser globals
        factory(global);
    }
}(typeof window !== "undefined" ? window : this, function(window, noGlobal) {

    // Define a local copy of jQuery
    var jQuery = function(selector, context) {
        return new jQuery.fn.init(selector, context);
    };

    // The default jQuery object
    jQuery.fn = jQuery.prototype = {
        constructor: jQuery,
        // jQuery core methods
        init: function(selector, context) {
            var match, elem;
            // Handle $(""), $(null), $(undefined), $(false)
            if (!selector) {
                return this;
            }
            // Handle $(DOMElement)
            if (selector.nodeType) {
                this[0] = selector;
                this.length = 1;
                return this;
            }
            // Handle $(html) or $(html, props)
            if (typeof selector === "string") {
                if (selector[0] === "<" && selector[selector.length - 1] === ">") {
                    match = [null, selector, null];
                }
                // Other string selector cases
            }
            // Return the jQuery object for chaining
            return jQuery.makeArray(selector, this);
        },
        // Other jQuery methods...
    };

    // Give the init function the jQuery prototype for later instantiation
    jQuery.fn.init.prototype = jQuery.fn;

    // Expose jQuery to the global object
    if (!noGlobal) {
        window.jQuery = window.$ = jQuery;
    }

    return jQuery;
}));
