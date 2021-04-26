/**************************************************
        01. Search in Header
        02. Page Scroll up
        03. Theme Wishlist
        04. Shop Events
        05. cart Popover
        06. Theme layout
        07. Compare short name
**************************************************/
odoo.define('mw_auction.theme_script', function(require) {
    'use strict';

    var sAnimations = require('website.content.snippets.animation');
    var theme_script = require('theme_clarico_vega.theme_script');
    
    var publicWidget = require('web.public.widget');
    var Widget = require('web.Widget');
    var core = require('web.core');
    var _t = core._t
    var ajax = require('web.ajax');
    var config = require('web.config');
//    var sale = new sAnimations.registry.WebsiteSale();

    //------------------------------------------
    // 07. Compare short name
    //------------------------------------------
    console.log('12312 2');
//    registry.reset_password_popup
//    sAnimations.registry.reset_password_popup = sAnimations.Class.extend({
    sAnimations.registry.reset_password_popup.include({

//        selector: "#wrapwrap",
//        start: function () {
//            self = this;
//            self.resetPassword();
//            self.customerLogin();
//            self.customerRegistration();
//            self.selectProductTab();
//        },

        customerRegistration: function(){
            $("#loginRegisterPopup .oe_signup_form_ept").submit(function(e) {
                var $form = $('#loginRegisterPopup .oe_signup_form_ept');
                e.preventDefault();
                var email = $form.find('#login').val();
                var name = $form.find('#name').val();
                var password = $form.find('#password').val();
                var confirm_password = $form.find('#confirm_password').val();
                var lastname = $form.find('#lastname').val();
                var ufile = $form.find('#ufile').val();
                
            	console.log('12312 3'+name);
            	console.log('image_1920 3'+ufile);
                ajax.jsonRpc('/web/signup_custom', 'call', {'login':email,'name':name,'password':password,
                											'confirm_password':confirm_password,'lastname':lastname,
                											'ufile':ufile,
                											'redirect':'','token':''}).then(function(data) {
                    if(!data.is_success){
                        $("#loginRegisterPopup .oe_signup_form_ept .te_error-success").replaceWith("<div class='te_error-success alert alert-danger'>" + data.error + "</div>");
                    } else {
                        $(location).attr('href', '/my');
                    }
                });
            });
        },

    });


});
