#Photo Sharing

Google App Engine based backend for posting and retrieving photos.

All functions appear to work. However, they only work if the url includes the token in the following form: 
".../<token>/" and not in the form ".../?id_token=<token>"

CREATE ACCOUNT
curl -X POST http://localhost:8080/create_account/test/pwd/
—> 200


AUTHENTICATE ACCOUNT
curl -X POST http://localhost:8080/user/authenticate/test/pwd/
—> 200 


SUBMIT FORM
example: 
curl -X POST -H "Content-Type: multipart/form-data" -F caption='curl' -F "image=@/Users/mousehouseapp/Unknown.jpeg"  http://localhost:8080/post/test/56a11d35-61a8-434e-b445-14a59096dd55/
—> Code 302 redirection



VIEW USER PICTURES IN JSON
curl -X GET http://localhost:8080/user/test1/json/?id_token=56a11d35-61a8-434e-b445-14a59096dd55
—> doesn’t work

curl -X GET http://localhost:8080/user/test/json/56a11d35-61a8-434e-b445-14a59096dd55/
—> works 



MOST RECENT ON WEB PAGE
curl -X GET http://localhost:8080/user/test1/web/?id_token=56a11d35-61a8-434e-b445-14a59096dd55
—> doesn’t work: 404 error 

curl -X GET http://localhost:8080/user/test/web/56a11d35-61a8-434e-b445-14a59096dd55/
—> works 
