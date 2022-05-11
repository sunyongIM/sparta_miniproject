// 이미지 미리보기 이벤트
function change_preview(a) {
    let file = a.files[0]
    let reader = new FileReader();
    reader.onload = function (e) {
        $("#image").attr("src", e.target.result);
        $("#image").css("width", "400");
        $("#image").css("height", "450");
    }
    reader.readAsDataURL(file);
}