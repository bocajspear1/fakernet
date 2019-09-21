<?php
error_reporting(E_ALL);
ini_set('display_errors', 1);

$file_db = new PDO('sqlite:/etc/postfix/vmail.sqlite');

$file_db->setAttribute(PDO::ATTR_ERRMODE, PDO::ERRMODE_EXCEPTION);

$errorMessage = "";
$successMessage = "";

if (array_key_exists("username", $_POST) && array_key_exists("password", $_POST)) {

    $username = $_POST['username'];
    $password = $_POST['password'];

    $salt = substr(sha1(rand()), 0, 16);
    $hashedPassword = "{SSHA512}" . base64_encode(hash('sha512', $password . $salt, true) . $salt);


    $sql = "INSERT INTO users (email,password,quota) VALUES (?, ?, 2000000);";
    $stmt= $file_db->prepare($sql);
    $stmt->execute([$username, $hashedPassword]);

    $successMessage = "User added. <a href='/roundcube'>Login</a>";
} else {
    $errorMessage = "Please enter a username and password";
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
                        <input type="text" name="username" placeholder="Username"/>
                    </div>
                </div>
                <div class="row">
                    <div class="col-sm-12 col-md-6">
                        <label for="password">Password</label>
                        <input type="password" name="password" placeholder="Password"/>
                    </div>
                </div>
                <div class="row">
                    <div class="col-sm-12 col-md-6">
                        <input type="submit" value="Submit" class="tertiary"/>
                    </div>
                </div>
            </fieldset>
            <div class="row">
            <?php if($errorMessage != "") : ?>
                <div class="card warning">
                    <?php echo $errorMessage; ?>
                </div>
            <?php endif; ?>
            <?php if($successMessage != "") : ?>
                <div class="card">
                    <?php echo $successMessage; ?>
                </div>
            <?php endif; ?>
            </div>
        </form>
    </body>


</html>