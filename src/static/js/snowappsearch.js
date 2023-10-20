$(document).ready(function(){

    $("#txt_search").keyup(function(){
        var search = $(this).val();

        if(search != "" && search.length>=3){

            $.ajax({
                url: '/searchtext',
                type: 'post',
                data: {searchterm:search, file:"snowapps", "fuzzy": "true"},
                dataType: 'json',
                success:function(response){
                    console.log(response['results']) 
                    var len = response['results'].length;
                    $("#searchResult").empty();
                    for( var i = 0; i<len; i++){
                        var name = response['results'][i];

                        $("#searchResult").append("<li value='"+name+"'>"+name+"</li>");

                    }

                    // binding click event to li
                    $("#searchResult li").bind("click",function(){
                        setText(this);
                    });

                }
            });
        }

    });

});

function setText(element){

    var value = $(element).text();
    var userid = $(element).val();

    $("#txt_search").val(value);
    $("#searchResult").empty();
}
