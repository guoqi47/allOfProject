;(function () {
        'use strict';
        let salt = "oknopk(8*lfdigjhDJGBEO%#&BGV";
        let pwd = document.getElementById('pass_word');
        let phone = document.getElementById('phone');
        let pass_word = md5(pwd.value+salt);
        // let sms_code = document.getElementById('sms_code');

        document.getElementById('send_sms_code').addEventListener(
            'click',
            function (event) {
                event.preventDefault();
                // alert(pass_word)
                $.ajax({
                  url:'http://47.100.239.246:8081/get_sms',
                  type: 'POST',
                  data:{
                      'phone_num':phone.value,
                      // 'password':pass_word
                      'password':md5(pwd.value+salt)
                   },
                   contentType:"application/x-www-form-urlencoded",
                   success:function(res){
                         console.log(res);//输出后端返回的数据
                         alert(res.msg)
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
                        // async : false,
                       success:function(res){
                            window.location.href ="http://47.100.239.246:8081/query";
                       },
                       error:function(err){
                            alert(err.msg);
                       }
                  });
                }
          )
    }())