<?php
error_reporting(E_ALL);
ini_set('display_errors', 1);

$file_db = new PDO('sqlite:/etc/postfix/vmail.sqlite');

$file_db->setAttribute(PDO::ATTR_ERRMODE,  PDO::ERRMODE_EXCEPTION);

$users = $file_db->query('SELECT * FROM users;');

if (array_key_exists("username", $_POST) && array_key_exists("password", $_POST)) {
    
}

?>

<html>
    <head>
        <title>Register New User</title>
        <link rel="stylesheet" href="mini.min.css">

    </head>
    <body>
        <form action="newaccount.php" method="post">
            <fieldset>
                <legend>Register New Email Account</legend>
                <div class="row">
                    <div class="col-sm-12 col-md-6">
                        <label for="username">Username</label>
                        <input type="text" id="username" placeholder="Username"/>
                    </div>
                </div>
                <div class="row">
                    <div class="col-sm-12 col-md-6">
                        <label for="password">Password</label>
                        <input type="password" id="password" placeholder="Password"/>
                    </div>
                </div>
                <div class="row">
                    <div class="col-sm-12 col-md-6">
                        <input type="submit" value="Submit" class="tertiary"/>
                    </div>
                </div>
            </fieldset>
        </form>
    </body>


</html>