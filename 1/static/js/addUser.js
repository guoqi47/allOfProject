;(function () {
        'use strict';
        

        document.getElementById('addUserButton').addEventListener(
            'click',
            function (event) {
                event.preventDefault();
                alert(" 222")
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