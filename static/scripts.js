let answers = {};
var answer = "";
var submit_flag = false;

function submit() {
    var answer

    if($("#text-input").val()) {
        answer = $("#text-input").val();
    } else if ($("input[name='validationScore']:checked").val()) {
        answer = $("input[name='validationScore']:checked").val();
    }
    console.log('=========Answer=========')
    console.log(answer)
    const task = $("#task-description").val();
    answers[task] = answer;  // Store the answer for this task
    $.post("/submit", {answer: answer}, function (data) {
        console.log(data);
        $("#result").text(data.message);
    }).fail(function () {
        $("#result").text("Error");
    });
    submit_flag = true;
    console.log(submit_flag)
}


function giveConsent() {
    window.location.href = '/give-consent';
}

function showConfirmationModal(message, actionUrl) {
    $("#modal-text").text(message);
    $("#confirm-action").attr("href", actionUrl);
    var myModal = new bootstrap.Modal(document.getElementById('confirmationModal'), {});
    myModal.show();
}

function checkAllCheckboxes() {
    let allChecked = true;
    $('.form-check-input').each(function() {
        if (!$(this).prop('checked')) {
            allChecked = false;
            return false; // breaks the each() loop
        }
    });
    $('#agree-button').prop('disabled', !allChecked);
}

function makeNewLines() {
    var textarea = document.getElementById("textarea");
    var text = textarea.value;
    text = text.replace(/\\n/g, "\r\n");
    textarea.value = text;
 }

 $(document).ready(function () {
     early_exit = false;
     $('.form-check-input').change(checkAllCheckboxes);
     $('#agree-button').click(giveConsent);
     
     $("#submit-button").on("click", submit);
     
     
     $('#exit-button').on('click', function(event) {
        event.preventDefault();
        var score = $("input[name='validationScore']:checked").val(); // The selected score
        var summary = $('#text-input').val();  // The summary text
        console.log(score)
        console.log(summary)
        if (!submit_flag) {  
            $('#myModal').modal('show');
        } else {
            showConfirmationModal("Are you sure you want to leave?", "/wyloguj_user") 
        }
    });
        
    $("#revoke-button").on("click", function(event) {
        event.preventDefault();
        showConfirmationModal("Are you sure you want to leave and revoke your consent?", "/revoke-consent");
    });

    $('.confirm-continue').on('click', function() {
        window.location.href = '/wyloguj_user';
    });
    
    $('.early-exit').on('click', function() {
        window.location.href = '/early_exit';
    });
        
    makeNewLines();
    });