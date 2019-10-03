function modal_form(form_url){
    var modal_id = 'modal-form';
    $.ajax({
        type: 'GET',
        url: form_url,
        cache: false,
        success: function (data, status) {
            $('#'+modal_id).html(data);
            $('#'+modal_id).modal('show');
            var callback = function() {
                for (var instance in CKEDITOR.instances) {
                    CKEDITOR.instances[instance].updateElement();
                }
                $.ajax({
                    type: 'POST',
                    url: form_url,
                    data: new FormData($('#'+modal_id+" form")[0]),
                    cache: false,
                    contentType: false,
                    processData: false,

                    success: function (data, status) {
                        if (data['stat'] == "ok") {
                            $('#'+modal_id).modal('hide');
                            $('#'+modal_id).children().remove();
                            window.location = data['redirect_url']

                        }
                        else if(data['stat'] == "re-render"){
                            $('#'+modal_id).html(data);
                            $('#'+modal_id).modal('show');
                        }
                        else if(data['stat'] == "error"){
                            $('#'+modal_id).modal('show');
                            $('#'+modal_id +' #error-message-text').html(data['error_message']);
                            $('#'+modal_id + ' .error-message').css('display','block');
                        }
                    }
                });                
            };
            $("#"+modal_id+" input").keypress(function() {
                console.log(event.which)
                if (event.which == 13) callback();
            });
            $("#"+modal_id+" [name=submit]").click(callback); 
        }
    });
}
