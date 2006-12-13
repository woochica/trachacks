/**
 * jCarousel - Riding carousels with jQuery
 *   http://sorgalla.com/jcarousel/
 *
 * Copyright (c) 2006 Jan Sorgalla (http://sorgalla.com)
 * Dual licensed under the MIT (MIT-LICENSE.txt)
 * and GPL (GPL-LICENSE.txt) licenses.
 *
 * Built on top of the jQuery library
 *   http://jquery.com
 *
 * Inspired by the "Carousel Component" by Bill Scott
 *   http://billwscott.com/carousel/
 */

jQuery.fn.extend({
    /**
     * Creates a carousel for all matched elements.
     *
     * @example $("#mycarousel").jcarousel();
     * @before <ul id="mycarousel"><li>First item</li><li>Second item</li></ul>
     * @result
     * <div class="jcarousel-scope">
     *   <button disabled="disabled" class="jcarousel-prev jcarousel-prev-disabled">&lt;&lt;</button>
     *   <button class="jcarousel-next">&gt;&gt;</button>
     *   <div class="jcarousel-clip">
     *     <ul id="mycarousel" class="jcarousel-list">
     *       <li class="jcarousel-item-1">First item</li>
     *       <li class="jcarousel-item-2">Second item</li>
     *     </ul>
     *   </div>
     * </div>
     *
     * @name jcarousel
     * @type jQuery
     * @param Hash o A set of key/value pairs to set as configuration properties.
     * @cat jCarousel
     */
    jcarousel: function(o) {
        return this.each(function() {
            new jQuery.jcarousel(this, o);
        });
    }
});

jQuery.extend({
    /**
     * The jCarousel object.
     *
     * @constructor
     * @private
     * @name jQuery.jcarousel
     * @param Object e The element to create the carousel for.
     * @param Hash o A set of key/value pairs to set as configuration properties.
     * @cat jCarousel
     */
    jcarousel: function(e, o) {
        // Public api of the jCarousel object passed to the
        // handler callback functions.
        var publ = this;

        /**
         * Returns the scope of the carousel which is the outer
         * <div> element containing the required markup (<ul> list,
         * prev/next buttons etc.).
         *
         * @name scope
         * @type Element
         * @cat jCarousel
         */
        publ.scope = function() { return priv.scope; };

        /**
         * Returns the list.
         *
         * @name list
         * @type Element
         * @cat jCarousel
         */
        publ.list = function() { return priv.list; };

        /**
         * Returns a jQuery object with list element for the given index.
         *
         * @name get
         * @type jQuery
         * @param Number idx The index of the element.
         * @cat jCarousel
         */
        publ.get = function(idx) { return priv.get(idx); };

        /**
         * Adds an element for the given index to the list.
         * If the element already exists, it updates the inner html.
         * Returns the created element as jQuery object.
         *
         * @name add
         * @type jQuery
         * @param Number idx The index of the element.
         * @param String html The innerHTML of the element.
         * @cat jCarousel
         */
        publ.add = function(idx, html) { return priv.add(idx, html); };

        /**
         * Returns true if all elements in the given range already exist,
         * false otherwise.
         *
         * @name available
         * @type Boolean
         * @param Number first The first index of the element range.
         * @param Number last The last index of the element range.
         * @cat jCarousel
         */
        publ.available = function(first, last) { return priv.available(first, last); };

        /**
         * Notifies the carousel object that updating of the carousel elements
         * has been finished. Must be called from the loadItemHandler callback
         * function after adding items with publ.add().
         *
         * @name loaded
         * @type undefined
         * @cat jCarousel
         */
        publ.loaded = function() { priv.loaded(); };

        /**
         * Moves the carousel forwards.
         *
         * @name next
         * @type undefined
         * @cat jCarousel
         */
        publ.next = function() { priv.next(); };

        /**
         * Moves the carousel backwards.
         *
         * @name prev
         * @type undefined
         * @cat jCarousel
         */
        publ.prev = function() { priv.prev(); };

        /**
         * Moves the carousel to a certain position.
         *
         * @name next
         * @type undefined
         * @param Number i The index of the element to scoll to.
         * @cat jCarousel
         */
        publ.scroll = function(i) { if (priv.available(i)) { priv.scroll(i); } };

        // Private methods/variables
        var priv = {
            o: {
                orientation: "horizontal",
                itemStart: 1,
                itemVisible: 3,
                itemScroll: null,
                scrollAnimation: "fast",
                autoScroll: 0,
                autoScrollStopOnInteract: true,
                autoScrollStopOnMouseover: false,
                autoScrollResumeOnMouseout: false,
                wrap: false,
                wrapPrev: false,
                itemWidth: null,
                itemHeight: null,
                loadItemHandler: null,
                nextButtonStateHandler: null,
                prevButtonStateHandler: null,
                itemFirstInHandler: null,
                itemFirstOutHandler: null,
                itemLastInHandler: null,
                itemLastOutHandler: null,
                itemVisibleInHandler: null,
                itemVisibleOutHandler: null,
                noButtons: false,
                buttonNextHTML: '<button type="button">&gt;&gt;</button>',
                buttonPrevHTML: '<button type="button">&lt;&lt;</button>'
            },

            scope: null,
            list: null,
            top: 0,
            left: 0,
            size: 0,
            end: 0,
            first: 0,
            prevFirst: 0,
            last: 0,
            prevLast: 0,
            lastButtonNext: null,
            lastButtonPrev: null,
            inAnimation: false,
            autoTimer: null,
            nextClick: function() { priv.next(); },
            prevClick: function() { priv.prev(); },
            itemFormat: {
                "float": "left",
                "styleFloat": "left",
                "overflow": "hidden",
                "listStyle": "none"
            },

            init: function(e, o) {
                if (o)
                    jQuery.extend(priv.o, o);

                priv.o.itemStart = Math.max(1, priv.intval(priv.o.itemStart));
                priv.o.horiz = priv.o.orientation == "vertical" ? false : true;
                priv.o.itemScroll = priv.o.itemScroll || priv.o.itemVisible;

                if (priv.o.itemWidth)
                    priv.itemFormat.width  = priv.o.itemWidth + "px";

                if (priv.o.itemHeight)
                     priv.itemFormat.height = priv.o.itemHeight + "px";

                priv.prepare(e);
                priv.calc();
                priv.resize();
                priv.buttons(false, false);
                priv.load(1, priv.o.itemStart + priv.o.itemVisible);
                priv.scroll(priv.o.itemStart);
                priv.startAuto();
            },

            get: function(idx) {
                return jQuery(".jcarousel-item-" + idx, priv.list);
            },

            add: function(idx, s) {
                var item = priv.get(idx);

                if (item.size() == 0) {
                    var item = priv.format(document.createElement("li"), idx);
                    jQuery(priv.list).append(item);
                    priv.size++;
                    priv.resize();
                }

                return item.html(s);
            },

            available: function(first, last) {
                if (last == undefined)
                    last = first;

                if (priv.end >= last)
                    return true;

                priv.end = last;
                return false;
            },

            load: function(first, last) {
                priv.buttons(false, false);

                if (priv.o.loadItemHandler != null)
                    priv.o.loadItemHandler(publ, first, last, priv.available(first, last));
                else
                    priv.loaded();
            },

            loaded: function() {
                if (priv.first > 1 && priv.last < priv.size) {
                    priv.buttons(true, true);
                } else if (priv.first == 1 && priv.last < priv.size) {
                    priv.buttons(true, priv.o.wrapPrev);
                } else if (priv.first > 1 && priv.last >= priv.size) {
                    priv.buttons(priv.o.wrap, true);
                }
            },

            next: function() {
                priv.stopAuto();

                if (priv.o.autoScrollStopOnInteract)
                    priv.disableAuto();

                priv.doNext();
            },

            doNext: function() {
                priv.scroll((priv.o.wrap && priv.last == priv.size) ? 1 : priv.first + priv.o.itemScroll);

                if (priv.o.wrap || priv.last < priv.size)
                    priv.startAuto();
            },

            prev: function() {
                priv.stopAuto();

                if (priv.o.autoScrollStopOnInteract)
                    priv.disableAuto();

                priv.doPrev();
            },

            doPrev: function() {
                priv.scroll((priv.o.wrapPrev && priv.first == 1) ? priv.size - priv.o.itemVisible + 1 : priv.first - priv.o.itemScroll);
                priv.startAuto();
            },

            scroll: function(idx) {
                if (priv.inAnimation)
                    return;

                priv.inAnimation = false;

                priv.prevFirst = priv.first;
                priv.prevLast  = priv.last;

                idx = idx < 1 ? 1 : idx;

                var last = idx + priv.o.itemVisible - 1;
                last = (last > priv.size) ? priv.size : last;

                var first = last - priv.o.itemVisible + 1;
                first = (first < 1) ? 1 : first;

                last = first + priv.o.itemVisible - 1;

                priv.first = first;
                priv.last  = last;

                priv.animate();
            },

            animate: function() {
                var pos = priv.dimension * (priv.first - 1) * -1;

                priv.notify(priv.prevFirst, priv.prevLast, priv.first, priv.last, "onBeforeAnimation");

                if (priv.o.scrollAnimation) {
                    priv.inAnimation = true;
                    jQuery(priv.list).animate(priv.o.horiz ? {"left": pos} : {"top": pos}, priv.o.scrollAnimation, function() { priv.scrolled(); });
                } else {
                    jQuery(priv.list)[priv.o.horiz ? "left" : "top"](pos + "px");
                    priv.scrolled();
                }
            },

            scrolled: function() {
                if (priv.first == 1)
                    jQuery(priv.list).top(priv.top + "px").left(priv.left + "px");

                priv.inAnimation = false;
                priv.notify(priv.prevFirst, priv.prevLast, priv.first, priv.last, "onAfterAnimation");
                priv.load(priv.last + 1, priv.last + priv.o.itemScroll);
            },

            handler: function(handler, evt, state, i1, i2, i3, i4) {
                if (priv.o[handler] == undefined || (typeof priv.o[handler] != 'object' && evt != "onAfterAnimation"))
                    return;

                var handler = typeof priv.o[handler] == 'object' ? priv.o[handler][evt] : priv.o[handler];

                if (typeof handler != 'function')
                    return;

                if (i2 == undefined)
                    priv.get(i1).each(function() { handler(publ, this, i1, state); });

                for (var i = i1; i <= i2; i++) {
                    if (!(i >= i3 && i <= i4))
                        priv.get(i).each(function() { handler(publ, this, i, state); });
                }
            },

            notify: function(prevFirst, prevLast, first, last, evt) {
                var state = prevFirst == 0 ? "init" : (prevFirst < first ? "next" : "prev");

                if (prevFirst != first) {
                    priv.handler("itemFirstOutHandler", evt, state, prevFirst);
                    priv.handler("itemFirstInHandler", evt, state, first);
                }

                if (prevLast != last) {
                    priv.handler("itemLastOutHandler", evt, state, prevLast);
                    priv.handler("itemLastInHandler", evt, state, last);
                }

                priv.handler("itemVisibleInHandler", evt, state, first, last, prevFirst, prevLast);
                priv.handler("itemVisibleOutHandler", evt, state, prevFirst, prevLast, first, last);
            },

            buttons: function(next, prev) {
                if (priv.o.noButtons) return;

                jQuery(".jcarousel-next", priv.scope)[next ? "bind" : "unbind"]("click", priv.nextClick)[next ? "removeClass" : "addClass"]("jcarousel-next-disabled")[next ? "removeAttr" : "attr"]("disabled", true);
                jQuery(".jcarousel-prev", priv.scope)[prev ? "bind" : "unbind"]("click", priv.prevClick)[prev ? "removeClass" : "addClass"]("jcarousel-prev-disabled")[prev ? "removeAttr" : "attr"]("disabled", true);

                if (priv.o.nextButtonStateHandler != null)
                    jQuery(".jcarousel-next", priv.scope).each(function() { priv.o.nextButtonStateHandler(publ, this, next); });

                if (priv.o.prevButtonStateHandler != null)
                    jQuery(".jcarousel-prev", priv.scope).each(function() { priv.o.prevButtonStateHandler(publ, this, prev); });
            },

            buttons: function(next, prev) {
                if (priv.o.noButtons) return;

                if (priv.lastButtonNext != next) {
                    priv.lastButtonNext = next;

                    jQuery(".jcarousel-next", priv.scope)[next ? "bind" : "unbind"]("click", priv.nextClick)[next ? "removeClass" : "addClass"]("jcarousel-next-disabled")[next ? "removeAttr" : "attr"]("disabled", true);

                    if (priv.o.nextButtonStateHandler != null)
                        jQuery(".jcarousel-next", priv.scope).each(function() { priv.o.nextButtonStateHandler(publ, this, next); });
                }

                if (priv.lastButtonPrev != prev) {
                    priv.lastButtonPrev = prev;

                    jQuery(".jcarousel-prev", priv.scope)[prev ? "bind" : "unbind"]("click", priv.prevClick)[prev ? "removeClass" : "addClass"]("jcarousel-prev-disabled")[prev ? "removeAttr" : "attr"]("disabled", true);

                    if (priv.o.prevButtonStateHandler != null)
                        jQuery(".jcarousel-prev", priv.scope).each(function() { priv.o.prevButtonStateHandler(publ, this, prev); });
                }
            },

            startAuto: function() {
                if (priv.o.autoScroll > 0)
                    priv.autoTimer = setTimeout(function() { priv.doNext(); }, priv.o.autoScroll * 1000);
            },

            stopAuto: function() {
                if (priv.autoTimer != null) {
                    clearTimeout(priv.autoTimer);
                    priv.autoTimer = null;
                }
            },

            disableAuto: function() {
                priv.stopAuto();
                priv.o.autoScroll = 0;
            },

            resize: function() {
                if (priv.size == 0)
                    return;

                if (priv.o.horiz)
                    jQuery(priv.list).width(priv.size * priv.dimension + 100 + "px");
                else
                    jQuery(priv.list).height(priv.size * priv.dimension + 100 + "px");
            },

            format: function(item, idx) {
                return jQuery(item).css(priv.itemFormat).addClass("jcarousel-item-" + idx);
            },

            margin: function(e, p) {
                if (p == "marginRight" && jQuery.browser.safari) {
                    var old = {"display": "block", "float": "none", "width": "auto"}, oWidth, oWidth2;

                    jQuery.swap(e, old, function() { oWidth = e.offsetWidth; });

                    old["marginRight"] = 0;
                    jQuery.swap(e, old, function() { oWidth2 = e.offsetWidth; });

                    return oWidth2 - oWidth;
                }

                return priv.intval(jQuery.css(e, p));
            },

            calc: function() {
                priv.size = jQuery("li", priv.list).size();
                priv.end = priv.size;

                if (priv.size == 0) {
                    var dummy = priv.format(document.createElement("li"), 1).get(0);
                    priv.list.appendChild(dummy);
                } else {
                    var idx = 1;
                    jQuery("li", priv.list).each(function() { priv.format(this, idx++); });
                }

                var i = jQuery("li", priv.list).get(0);

                var itemWidth  = i.offsetWidth + priv.margin(i, "marginLeft") + priv.margin(i, "marginRight");
                var itemHeight = i.offsetHeight + priv.margin(i, "marginTop") + priv.margin(i, "marginBottom");

                if (priv.o.horiz) {
                    priv.dimension = itemWidth;
                    var clipW  = itemWidth * priv.o.itemVisible - priv.margin(i, "marginRight");
                    var clipH  = itemHeight;
                } else {
                    priv.dimension = itemHeight;
                    var clipW  = itemWidth;
                    var clipH  = itemHeight * priv.o.itemVisible - priv.margin(i, "marginBottom");
                }

                jQuery(".jcarousel-clip", priv.scope).css({
                    "zIndex": 2,
                    "padding": 0,
                    "margin": 0,
                    "width":  clipW + "px",
                    "height": clipH + "px",
                    "overflow": "hidden",
                    "position": "relative"
                });

                priv.top  = priv.intval(jQuery(priv.list).top());
                priv.left = priv.intval(jQuery(priv.list).left());

                jQuery(priv.list).css({
                    "zIndex": 1,
                    "position": "relative",
                    "top": priv.top + "px",
                    "left": priv.left + "px",
                    "margin": 0,
                    "padding": 0
                });

                if (dummy != undefined)
                    priv.list.removeChild(dummy);
            },

            prepare: function(e) {
                if (e.nodeName == "UL" || e.nodeName == "OL") {
                    priv.list = e;
                    var scope = jQuery(priv.list).parent().get(0);

                    if (jQuery.className.has(scope, "jcarousel-clip")) {
                        if (!jQuery.className.has(jQuery(scope).parent().get(0), "jcarousel-scope"))
                            scope = jQuery(scope).wrap('<div class="jcarousel-scope"></div>');

                        scope = jQuery(scope).parent().get(0);
                    } else if (!jQuery.className.has(scope, "jcarousel-scope"))
                        scope = jQuery(priv.list).wrap('<div class="jcarousel-scope"></div>').parent().get(0);

                    priv.scope = scope;
                } else {
                    priv.scope = e;
                    priv.list = jQuery("ul", priv.scope).get(0) || jQuery("ol", priv.scope).get(0);
                }

                if (!jQuery.className.has(jQuery(priv.list).parent().get(0), "jcarousel-clip"))
                    jQuery(priv.list).wrap('<div class="jcarousel-clip"></div>');

                if (!priv.o.noButtons) {
                    if (jQuery(".jcarousel-prev", priv.scope).size() == 0) {
                        var dummy = jQuery(document.createElement("div")).html(priv.o.buttonPrevHTML).get(0);
                        jQuery(".jcarousel-clip", priv.scope).before(jQuery(dummy.firstChild).addClass("jcarousel-prev"));
                    }

                    if (jQuery(".jcarousel-next", priv.scope).size() == 0) {
                        var dummy = jQuery(document.createElement("div")).html(priv.o.buttonNextHTML).get(0);
                        jQuery(".jcarousel-clip", priv.scope).before(jQuery(dummy.firstChild).addClass("jcarousel-next"));
                    }

                    jQuery(".jcarousel-prev", priv.scope).css({"zIndex": 3});
                    jQuery(".jcarousel-next", priv.scope).css({"zIndex": 3});
                }

                if (priv.o.autoScrollStopOnMouseover) {
                    if (priv.o.autoScrollResumeOnMouseout) {
                        jQuery(".jcarousel-clip", priv.scope).mouseover(function() { priv.stopAuto(); }).mouseout(function() { priv.startAuto(); });
                    } else {
                        jQuery(".jcarousel-clip", priv.scope).mouseover(function() { priv.disableAuto(); });
                    }
                }

                jQuery(priv.list).addClass("jcarousel-list");
                jQuery(priv.scope).addClass("jcarousel-scope").show().find(":hidden").show();
            },

            intval: function(v) {
                v = parseInt(v);
                return isNaN(v) ? 0 : v;
            }
        };

        // Initialize the carousel
        priv.init(e, o);
    }
});
