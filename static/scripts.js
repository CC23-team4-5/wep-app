let answers = {};
var answer = "";
function submit() {
    const review = $("#text-input").val();
    const task = $("#task-description").val();
    answers[task] = review;  // Store the answer for this task
    $.post("/submit", {review: review}, function (data) {
        console.log(data);
        $("#result").text(data.message);
    }).fail(function () {
        $("#result").text("Error");
    });
}
function unfog() {
    $("#additional-info").removeClass("foggy");
    $("#unfog-button").prop("disabled", true);
}

function nextTask() {
    $.get("/next_task", function (data) {
        $("#microtask-name").text(data.microtask_name);
        $("#task-description").val(data.task_description);
        $("#additional-info").val(data.additional_info);
        $("#text-input").val(data.user_answer || '');
        // answer = data.user_answer;
        // $("#text-input").val('');  // Clear the text input field
        if (answers[data.task_description]) {  // If an answer for this task has been submitted before
            $("#text-input").val(answers[data.task_description]);  // Load the previously submitted answer
        }
    });
}

$(document).ready(function () {
    $("#submit-button").on("click", submit);
    $("#unfog-button").on("click", unfog);
    $("#next-task").on("click", nextTask);
});