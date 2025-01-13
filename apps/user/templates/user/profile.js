(function(){

    var date = moment('{{up_form.birth_date.value}}', 'MMM DD, YYYY')
    var dateObj = date.isValid() ? date.toDate() : null;
    if (!!dateObj) {
        $("#datetimepicker_birth_date").datetimepicker({
            format: 'L',
            date: dateObj,
        });
    } else {
        $("#datetimepicker_birth_date").datetimepicker({
            format: 'L',
        });
    }

    $("#datetimepicker_birth_date").on('change.datetimepicker', function(e) {
        $('#profile-form').change();
        $('#profile-form').data('changed', true);
    });

    //$('#profile-form').AJAXFormSubmit();

    $('#upload-image-form').AJAXUploadImage("{% url 'upload_image' %}");

    $('#delete-image-form').AJAXDeleteImage("{% url 'delete_image' %}");


    // Profile form email
    var ajaxProfileForm = function () {
        var thisForm = $('#profile-form');
        var data = thisForm.serializeFiles();
        $.ajax({
            url: window.location.href,
            type: 'POST',
            data: data,
            async: true,
            cache: false,
            processData: false,
            contentType: false,

            success: function(json) {
                if (json.success) {
                    if (json.url) {
                        window.location.href = json.url;
                    } else {
                        thisForm.resetForm();
                        $.fn.animateMessage(json.success, 'success');
                    }
                } else {
                    thisForm.resetForm();
                    thisForm.renderForm(json);
                }
            },

            error: function(xhr, errmsg, err) {
                $.fn.animateMessage('We have encountered an error: ' + errmsg, 'error');
                console.log(xhr.status + ": " + xhr.responseText);
            }
        });
    };
    const initialEmail = $('#id_email').val();
    var form = $('#profile-form');
    form.trackChanges();
    form.on('submit', function(e) {
        e.preventDefault();
        var _this = $(this);
        var emailChanged = $('#id_email').val() == initialEmail ? false : true;

        if (_this.isChanged()) {
            if (emailChanged) {
                var dialog = "Changing email address requires your re-activation. Do you want to continue?";
                confirmSubmit(dialog, ajaxProfileForm);
            } else {
                ajaxProfileForm();
            }
        } else {
            $.fn.animateMessage('No change is made!');
        }
    });

    String.prototype.splice = function(idx, rem, str) {
        return this.slice(0, idx) + str + this.slice(idx + Math.abs(rem));
    };

    $('#id_phone').keyup(function(e){
        if(this.value == '(') return true;
        if(e.keyCode > 36 && e.keyCode < 41) return true;
        if(e.keyCode == 8) return true;
        this.value = this.value.replace(/[^0-9]/g, '');
        if (this.value.length > 0) this.value = '(' + this.value;
        if (this.value.length > 3) this.value = this.value.splice(4, 0, ')');
        if (this.value.length > 7) this.value = this.value.splice(8, 0, '-');
        if (this.value.length > 13) this.value = this.value.substring(0, 13);
        return true;
    });

})();