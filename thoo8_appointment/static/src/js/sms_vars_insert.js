odoo.define('thoo8_appointment.sms_vars_insert', function (require) {
    "use strict";

    $(document).on('click', '.sms-var', function () {
        const variable = $(this).data('var');
        const targetField = $(this).closest('.o_sms_vars').data('target');
        const $textarea = $(`textarea[name='${targetField}']`);

        if ($textarea.length) {
            const cursorPos = $textarea.prop("selectionStart");
            const v = $textarea.val();
            const textBefore = v.substring(0, cursorPos);
            const textAfter  = v.substring(cursorPos, v.length);

            $textarea.val(textBefore + variable + textAfter);
            $textarea.focus();
            $textarea[0].setSelectionRange(cursorPos + variable.length, cursorPos + variable.length);
        }
    });
});
