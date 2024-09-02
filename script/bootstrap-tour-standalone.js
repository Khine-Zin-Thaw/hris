/*!
 * Bootstrap Tour v0.11.0 (https://github.com/sorich87/bootstrap-tour)
 * Copyright 2012-2014, Sam R. Johnson
 * Licensed under MIT (https://github.com/sorich87/bootstrap-tour/blob/master/LICENSE)
 */

!function ($) {
    'use strict';
  
    var Tour = function (options) {
      this.options = $.extend({}, $.fn.tour.defaults, options);
      this.$element = $(this.options.element);
      this.$backdrop = $('<div class="tour-backdrop"></div>');
      this.$tooltip = $('<div class="tour-tooltip"></div>');
      this.currentStep = 0;
      this.init();
    };
  
    Tour.prototype = {
      constructor: Tour,
  
      init: function () {
        this.setupTooltip();
        this.setupEvents();
      },
  
      setupTooltip: function () {
        var that = this;
        this.$tooltip
          .addClass(this.options.template)
          .append('<div class="tooltip-arrow"></div><h3 class="tooltip-title"></h3><div class="tooltip-content"></div><div class="tooltip-buttons"><button class="btn btn-default tour-prev">Prev</button><button class="btn btn-default tour-next">Next</button></div>')
          .appendTo('body');
      },
  
      setupEvents: function () {
        var that = this;
        $(document).on('click', '.tour-prev', function () {
          that.prev();
        });
        $(document).on('click', '.tour-next', function () {
          that.next();
        });
        $(document).on('click', '.tour-backdrop', function () {
          that.end();
        });
      },
  
      start: function () {
        this.showStep(this.currentStep);
      },
  
      showStep: function (index) {
        var step = this.options.steps[index];
        if (step) {
          this.$backdrop.appendTo('body').show();
          this.$tooltip
            .find('.tooltip-title').text(step.title).end()
            .find('.tooltip-content').html(step.content).end()
            .css({ top: step.top, left: step.left })
            .show();
          this.currentStep = index;
        }
      },
  
      next: function () {
        if (this.currentStep < this.options.steps.length - 1) {
          this.showStep(this.currentStep + 1);
        } else {
          this.end();
        }
      },
  
      prev: function () {
        if (this.currentStep > 0) {
          this.showStep(this.currentStep - 1);
        }
      },
  
      end: function () {
        this.$tooltip.hide();
        this.$backdrop.hide();
      }
    };
  
    $.fn.tour = function (options) {
      return this.each(function () {
        var $this = $(this);
        var data = $this.data('tour');
        if (!data) {
          $this.data('tour', (data = new Tour(options)));
        }
        if (typeof options == 'string') data[options]();
      });
    };
  
    $.fn.tour.defaults = {
      element: 'body',
      template: 'tooltip-template',
      steps: []
    };
    
  }(jQuery);
  