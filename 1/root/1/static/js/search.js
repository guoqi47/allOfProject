;(function () {
        'use strict';
        let phone = document.getElementById('phone');
        // let sms_code = document.getElementById('sms_code');

        document.getElementById('search').addEventListener(
            'click',
            function (event) {
                event.preventDefault();
                // alert(pass_word)
                $.ajax({
                  url:'http://47.100.239.246:8081/search',
                  type: 'GET',
                  data:{
                      'phone':phone.value,
                      // 'password':pass_word
                   },
                   contentType:"application/x-www-form-urlencoded",
                   success:function(res){
                         console.log(res.data.column);//输出后端返回的数据
                         console.log(res.data.column.Tel_act_2017);//输出后端返回的数据
                         // $('#dataTables-example').css({
                         //    'width' : '100px'
                         //    });
                         //  $("#dataTables-example thead tr th ").text("Hello world!");
                          $("#dataTables-example").html("<p>"+res.data.column.Tel_act_2017+"</p>");
                   },
                   error:function(err){
                        alert(err.msg);
                   }
              });
            }
      ),document.getElementById('sign_in').addEventListener(
                'click',
                function (event) {
                    event.preventDefault();
                    // alert("sign_in")
                    $.ajax({
                      url:'http://47.100.239.246:8081/login',
                      type: 'POST',
                      data:{
                          'phone_num':phone.value,
                           'password':md5(pwd.value+salt),
                          'sms_code':sms_code.value
                       },
                       contentType:"application/x-www-form-urlencoded",
                       success:function(res){
                             // alert("登录成功，欢迎回来！");
                           alert(res.msg);
                       },
                       error:function(err){
                            alert(err.msg);
                       }
                  });
                }
          )
    }())