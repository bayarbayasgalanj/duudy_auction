odoo.define('mw_auction.website_sale', function (require) {
    "use strict";
    var publicWidget = require('web.public.widget');
    var core = require('web.core');
     var ajax = require('web.ajax');
    var _t = core._t;
    var QWeb = core.qweb;
	var VariantMixin = require('sale.VariantMixin');
    
	console.log('mw_acu js');
    publicWidget.registry.WebsiteSale.include({
	    
	 events: _.extend({
	            'change form.js_models input, form.js_models select': '_onChangeModel',
	            'change form.js_makes input, form.js_makes select': '_onChangeMake',
	            
	    }, publicWidget.registry.WebsiteSale.prototype.events),
	    	    
//	    events: _.extend({}, VariantMixin.events || {}, {
//	        'change form.js_models input, form.js_attributes select': '_onChangeModel',
//	    }),
//        events: {
//            'change form.js_models input, form.js_attributes select': '_onChangeModel',
//        },

    /**
     * @private
     * @param {Event} ev
     */
    _onChangeModel: function (ev) {
    	console.log('aaaaaaaa');
        if (!ev.isDefaultPrevented()) {
            ev.preventDefault();
            $(ev.currentTarget).closest("form").submit();
        }
    },    
    _onChangeMake: function (ev) {
    	console.log('aaaaaaaa');
        if (!ev.isDefaultPrevented()) {
            ev.preventDefault();
            $(ev.currentTarget).closest("form").submit();
        }
    },        

    });
});
