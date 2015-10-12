function checked_only(){
    checkboxes = $('input[name="select_col"]')
    checkboxes.click(function() {
        $('#add-selected').attr("disabled", !checkboxes.is(":checked"));
        $('#delete-selected').attr("disabled", !checkboxes.is(":checked"));
        $('#download-selected').attr("disabled", !checkboxes.is(":checked"));
    });
}
function action_selected(url){
    $.ajax({
        type: 'POST',
        data: $('#administration-form').serialize(),
        cache: false,
        success: function (data, status) {
            console.log(data);
            if (data['stat'] == "ok") {
                window.location = data['redirect_url']
            }
            else {
                console.log(data);
            }
        }
    });
    
}

