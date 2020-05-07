Simplemail is a basic mail server that uses Postfix (for SMTP) and Dovecot (for IMAP). It also contains a webserver that runs Roundcube and a simple PHP application to add more users to the mail server. This does not require and authorization to create the account, so anybody can create one.

The webserver is HTTPS, so access it at:
```
https://<SERVER_IP>
```

The account creator is available at:
```
https://<SERVER_IP>/newaccount.php
```