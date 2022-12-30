Title: Add a class to wp_nav_menu() items with URLs included in the current URL
Tags: wordpress, a-lifetime-ago
ExtraTags: wordpress

We're all enjoying the benefits and features of WordPress 3.0. Custom menus are awesome and custom post types shatter all capability and imagination limits. A small problem arises when these two features are used in conjunction: the classes applied to navigation menu items only reflect direct inheritance, and entities that have their URLs included in the current URL can't get highlighted.
<!-- PELICAN_END_SUMMARY -->

### The Problem

Let me illustrate through a simple example:

Suppose you defined a *Services* page that lives at this URL: `http://example.com/services/`.
This page has an entry in the main menu of your website. To further emphasize your services, you also defined a *services* custom post type with the slug `services`. The URL of a 'service' post can be `http://example.com/services/branding/`.

When you browse the *Branding* post, however, no special class is applied to the menu entry of your *Services* page, and it's impossible to style it as the current section of your website, even though the proposed URL structure is semantic.

### The Solution

The solution is based on the `nav_menu_css_class` WordPress hook. This is a filter hook that allows us to alter an array containing CSS classes that will be applied to a menu item.

We also need a way to find the current URL, or the URL being browsed.

### The Code

```php
<?php
add_filter( 'nav_menu_css_class', 'add_parent_url_menu_class', 10, 2 );

function add_parent_url_menu_class( $classes = array(), $item = false ) {
  // Get current URL
  $current_url = current_url();

  // Get homepage URL
  $homepage_url = trailingslashit( get_bloginfo( 'url' ) );

  // Exclude 404 and homepage
  if( is_404() or $item->url == $homepage_url ) return $classes;

  if ( strstr( $current_url, $item->url) ) {
    // Add the 'parent_url' class
    $classes[] = 'parent_url';
  }

  return $classes;
}

function current_url() {
  // Protocol
  $url = ( 'on' == $_SERVER['HTTPS'] ) ? 'https://' : 'http://';

  $url .= $_SERVER['SERVER_NAME'];

  // Port
  $url .= ( '80' == $_SERVER['SERVER_PORT'] ) ? '' : ':' . $_SERVER['SERVER_PORT'];

  $url .= $_SERVER['REQUEST_URI'];

  return trailingslashit( $url );
}
```

In the hooked function, a check is first made to see if we're on a 404 page. When an invalid URL is accessed, we don't want to highlight anything.

The same holds if the menu item points to the domain root URL: all other URLs on the website include it.

The rest is pretty straightforward: add the class if the menu item URL is included in the current URL and return the `$classes` array.
