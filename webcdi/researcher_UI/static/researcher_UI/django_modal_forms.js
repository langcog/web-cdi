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
                $.ajax({
                    type: 'POST',
                    url: form_url,
                    data: $('#'+modal_id+" form").serialize(),
                    cache: false,
                    success: function (data, status) {
                        if (data['stat'] == "ok") {
                            $('#'+modal_id).modal('hide');
                            $('#'+modal_id).children().remove();
                            window.location = data['redirect_url']
                            return render(request, 'researcher_UI/administer_new_modal.html')

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
            $("#"+modal_id+" [name=autogenerate-count]").keypress(function() {
                if (event.which == 13) callback();
            });
            $("#"+modal_id+" [name=new-subject-ids]").keypress(function() {
                if (event.which == 13) callback();
            });
            $("#"+modal_id+" [name=submit]").click(callback); 
        }
    });
}
