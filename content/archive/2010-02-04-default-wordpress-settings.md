Title: Default WordPress Settings
Tags: wordpress, a-lifetime-ago
ExtraTags: wordpress

Do you often find yourself changing the default WordPress settings after a fresh install? Not anymore.
<!-- PELICAN_END_SUMMARY -->


[WPEngineer](http://wpengineer.com/wordpress-useful-default-configuration-settings-via-plugin/) has a great article promoting a very simple but ultra-effective plugin.
​
The plugin was written by [Thomas Scholz](http://toscho.de) and addresses the problem of always having to do the same adjustments after a clean WordPress install.
​
Examples include setting the Permalink structure, deleting the default post, and basically altering any other default setting from the `wp_options` table. If you don’t have database access you can access an automatically generated overview of available options at `[your_base_URL]/wp-admin/options.php`.
​
### Instructions
​
Take the following steps:

1. [Download](http://f.toscho.de/php-skripte/toscho_basic_settings-0.2.zip) the plugin by toscho.
2. Upload the plugin into your `/wp-content/plugins/` directory
3. Activate the plugin
4. Deactivate the plugin
5. Delete the plugin
​
### The Code
​
```php
<?php
/*
Plugin Name: Toscho's basic settings
Plugin URI: http://toscho.de/2010/wordpress-grundeinstellungen-per-plugin-setzen/
Description: Some useful default configuration settings. See 'wp-admin/options.php' for more options.
Version: 0.2
Author: Thomas Scholz
Author URI: http://toscho.de
*/
function set_toscho_defaults() {
    $o = array(
        'avatar_default'            => ''blank',
        'avatar_rating'             => 'G',
        'category_base'             => '/thema',
        'comment_max_links'         => 0,
        'comments_per_page'         => 0,
        'date_format'               => 'd.m.Y',
        'default_ping_status'       => 'closed',
        'default_post_edit_rows'    => 30,
        'links_updated_date_format' => 'j. F Y, H:i',
        'permalink_structure'       => '/%year%/%postname%/',
        'rss_language'              => 'de',
        'timezone_string'           => 'Etc/GMT-1',
        'use_smilies'               => 0,
    );
​
    foreach ( $o as $k => $v ) {
        update_option($k, $v);
    }
​
    // Delete dummy post and comment.
    wp_delete_post( 1, true );
    wp_delete_comment( 1 );
    return;
}
​
register_activation_hook( __FILE__, 'set_toscho_defaults' );
```
​
**Update:** Thomas has kindly provided a link to a public repository on GitHub. Feel free to contribute.
[http://github.com/toscho/WordPress-Basic-Settings](http://github.com/toscho/WordPress-Basic-Settings)
