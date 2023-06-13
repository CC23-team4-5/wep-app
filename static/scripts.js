let answers = {};
var answer = "";
function submit() {
    const answer = $("#text-input").val();
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
    var textareaSummary = document.getElementById("textareaSummary");
    var text = textarea.value;
    var textareaSummaryText = textareaSummary.value;
    text = text.replace(/\\n/g, "\r\n");
    textareaSummaryText = textareaSummaryText.replace(/\\n/g, "\r\n");
    textarea.value = text;
    textareaSummary.value = textareaSummaryText;
 }

$(document).ready(function () {
    $('.form-check-input').change(checkAllCheckboxes);
    $('#agree-button').click(giveConsent);
    
    $("#submit-button").on("click", submit);
    
    
    $("#exit-button").on("click", function(event) {
        event.preventDefault();
        showConfirmationModal("Are you sure you want to exit the experiment?", "/wyloguj_user");
    });
    
    $("#revoke-button").on("click", function(event) {
        event.preventDefault();
        showConfirmationModal("Are you sure you want to leave and revoke your consent?", "/revoke-consent");
    });
    makeNewLines();
});