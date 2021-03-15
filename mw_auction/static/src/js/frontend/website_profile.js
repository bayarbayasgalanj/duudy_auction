odoo.define('mw_auction.website_profile', function (require) {
'use strict';

var publicWidget = require('web.public.widget');
var wysiwygLoader = require('web_editor.loader');

publicWidget.registry.websiteProfileMWEditor = publicWidget.Widget.extend({
    selector: '.o_wprofile_editor_form',
    read_events: {
        'click .o_forum_profile_pic_edit': '_onEditProfilePicClick',
        'change .o_forum_file_upload': '_onFileUploadChange',
        'click .o_forum_profile_pic_clear': '_onProfilePicClearClick',
        'click .o_wprofile_submit_btn': '_onSubmitClick',

        'click .o_forum_pass_pic_edit': '_onEditPassPicClick',
        'change .o_forum_pass_file_upload': '_onPassFileUploadChange',
        'click .o_forum_pass_pic_clear': '_onPassPicClearClick',
    
    },

    /**
     * @override
     */
//    start: function () {
//        var def = this._super.apply(this, arguments);
//        if (this.editableMode) {
//            return def;
//        }
//
//        var $textarea = this.$('textarea.o_wysiwyg_loader');
//        var loadProm = wysiwygLoader.load(this, $textarea[0], {
//            recordInfo: {
//                context: this._getContext(),
//                res_model: 'res.users',
//                res_id: parseInt(this.$('input[name=user_id]').val()),
//            },
//        }).then(wysiwyg => {
//            this._wysiwyg = wysiwyg;
//        });
//
//        return Promise.all([def, loadProm]);
//    },

    //--------------------------------------------------------------------------
    // Handlers
    //--------------------------------------------------------------------------

    /**
     * @private
     * @param {Event} ev
     */
    _onEditProfilePicClick: function (ev) {
        ev.preventDefault();
        $(ev.currentTarget).closest('form').find('.o_forum_file_upload').trigger('click');
    },
    /**
     * @private
     * @param {Event} ev
     */
    _onFileUploadChange: function (ev) {
        if (!ev.currentTarget.files.length) {
            return;
        }
        var $form = $(ev.currentTarget).closest('form');
        var reader = new window.FileReader();
        reader.readAsDataURL(ev.currentTarget.files[0]);
        reader.onload = function (ev) {
            $form.find('.o_forum_avatar_img').attr('src', ev.target.result);
        };
        $form.find('#forum_clear_image').remove();
    },
    /**
     * @private
     * @param {Event} ev
     */
    _onProfilePicClearClick: function (ev) {
        var $form = $(ev.currentTarget).closest('form');
        $form.find('.o_forum_avatar_img').attr('src', '/web/static/src/img/placeholder.png');
        $form.append($('<input/>', {
            name: 'clear_image',
            id: 'forum_clear_image',
            type: 'hidden',
        }));
    },
    /**pass**/
    _onEditPassPicClick: function (ev) {
        ev.preventDefault();
        $(ev.currentTarget).closest('form').find('.o_forum_pass_file_upload').trigger('click');
    },
    /**
     * @private
     * @param {Event} ev
     */
    _onPassFileUploadChange: function (ev) {
        if (!ev.currentTarget.files.length) {
            return;
        }
        var $form = $(ev.currentTarget).closest('form');
        var reader = new window.FileReader();
        reader.readAsDataURL(ev.currentTarget.files[0]);
        reader.onload = function (ev) {
            $form.find('.card_img_mw').attr('src', ev.target.result);
        };
        $form.find('#forum_pass_clear_image').remove();
    },
    /**
     * @private
     * @param {Event} ev
     */
    _onPassPicClearClick: function (ev) {
        var $form = $(ev.currentTarget).closest('form');
        $form.find('.card_img_mw').attr('src', '/web/static/src/img/placeholder.png');
        $form.append($('<input/>', {
            name: 'clear_pass_image',
            id: 'forum_pass_clear_image',
            type: 'hidden',
        }));
    },
    
    
    /**
     * @private
     */
    _onSubmitClick: function () {
        if (this._wysiwyg) {
            this._wysiwyg.save();
        }
    },
});


});
