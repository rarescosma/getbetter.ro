Title: WordPress hooks: user_register
Tags: wordpress, a-lifetime-ago
ExtraTags: wordpress

I'm gonna keep things short in this article and show you how you can 
automatically alter WordPress user data after registration.
<!-- PELICAN_END_SUMMARY -->


### Use Case: Changing the user's Display Name

One of WordPress' present shortcomings is the lack of a configuration option 
to specify a default display name format for your users. 
The last sentence was long, so let me give you an example.

Let's say you've allowed user registration on your WordPress website ([Settings – General](http://codex.wordpress.org/Settings_General_SubPanel "Settings - General")) 
but instead of the plain username, you want to display their full name 
on the articles they submit.

You have two options: either you independently edit each user and change 
the 'Display Name' option or...

### Enter the 'user_register' hook

This action hook runs immediately after the successful registration 
of a new user on your website. 
It passes on the user ID to the callback function. 
For our purpose, the code is very simple:

```php
<?php
/**
 * Provides custom user functionality through hooks.
 * References:
 * @codex [the user_register action hook](http://codex.wordpress.org/Plugin_API/Action_Reference/user_register)
 * @codex [get_userdata()](http://codex.wordpress.org/Function_Reference/get_userdata)
 * @codex [wp_update_user()](http://codex.wordpress.org/Function_Reference/wp_update_user)
 */
class myUsers {
  static function init() {
    // Change the user's display name after insertion
    add_action( 'user_register', [ __CLASS__, 'change_display_name' ] );
  }

  static function change_display_name( $user_id ) {
    $info = get_userdata( $user_id );

    wp_update_user( [
      'ID' => $user_id,
      'display_name' => $info->first_name . ' ' . $info->last_name,
    ] );
  }
}

myUsers::init();
```

First, we grab the newly created user information with the `get_userdata()` function. 
Then, we concatenate the first name and the last name and feed it as an argument to `wp_update_user()`.

Just paste this into your `functions.php` file and you're all set.
