;(function () {
        'use strict';
        let salt = "oknopk(8*lfdigjhDJGBEO%#&BGV";
        let pwd = document.getElementById('pass_word');
        let name = document.getElementById('name');
        let phone = document.getElementById('phone');
        let pass_word = md5(pwd.value+salt);

        document.getElementById('addUserButton').addEventListener(
            'click',
            function (event) {
                event.preventDefault();
                alert(" ssss")
                $.ajax({
                  url:'http://47.100.239.246:8081/add_user',
                  type: 'POST',
                  data:{
                      'phone':phone.value,
                      'name':name.value,
                      'password':md5(pwd.value+salt)
                   },
                   contentType:"application/x-www-form-urlencoded",
                   success:function(res){
                         console.log(res);//输出后端
                         alert(res.msg)
                   },
                   error:function(err){
                        alert(err.msg);
                   }
              });
            }
      )
    }())