window.addEventListener("load", () => setTimeout(function() {
    (function ($) {
        $('#changelist-filter').children().wrapAll('<form></form>'); // required for forward func
    })(django.jQuery);
}, 10));
