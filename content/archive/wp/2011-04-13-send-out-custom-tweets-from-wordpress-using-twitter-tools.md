Title: Send out custom Tweets from WordPress using Twitter Tools
Tags: wordpress, twitter, a-lifetime-ago
ExtraTags: wordpress, twitter

In this post I will explain how you can send out custom tweets from WordPress.
For this purpose, we will configure and use the functionality present
in the WordPress Twitter Tools plug-in.
<!-- PELICAN_END_SUMMARY -->


### Get Twitter Tools

Head over to the [WordPress plugin repository](http://wordpress.org/extend/plugins/twitter-tools/ "Twitter Tools for WordPress") and grab the Twitter Tools zip file. Upload it to your `/wp-content/plugins` directory and unzip. Next, go to the **Plugins** section of your WP admin and activate the plugin.

Twitter Tools bundles a set of complementary plugins. Make sure you activate **Twitter Tools – Bit.ly URLs** for the URL shortening ability. We'll be using this plugin to send out custom tweets (triggered by any type of action), so we don't need the other components (Exclude Category and Hashtags).

### Connect to Twitter

Follow the instructions on the Twitter Tools settings page to connect your website to Twitter. First, you need to [register your site as a Twitter application](http://dev.twitter.com/apps/new "Twitter's app registration page"). A couple of things to keep in mind:

* Your Application's Name will be what shows up after “via” in your twitter stream
* Application Type should be set on **Browser**
* The Callback URL should be your website URL
* Default Access type should be set to **Read & Write**

A screenshot is worth more than 1000 words, so here's an example:

![Register your Twitter Application](/images/legacy/register_your_app2.png)

A couple of special strings used for authentication and API access need to be copied over to Twitter Tools:

* The Twitter Consumer Key and Consumer Secret
* The application Access Token and Access Token Secret

The latter can be found by going to 'My Access Token' in the right menu:

![My Access Token](/images/legacy/my_access_token.png)

### Configure Twitter Tools

Remember that we only need this plugin as a support to send out our custom Tweets, so we're gonna disable all the auto-tweeting functionality. Set the following options to **'No'**:

* Enable option to create a tweet when you post in your blog?
* Create tweets from your sidebar?
* Create a daily digest blog post from your tweets?

That's it! Now let's get down to some coding.

### Example code for a custom tweet

Suppose your website uses a [Custom Post Type](http://codex.wordpress.org/Post_Types "WordPress Codex - Post Types") called **'product'** and you want to send out a custom notification on Twitter each time a new **'product'** is added.

First let's create a custom function that uses (or hijacks) the Twitter Tools objects to tweet out a text portion, a link and some hashtags:

```php
<?php
function my_tweet( $args = array() ) {
  // Check reqs
  if( ! class_exists( 'aktt_tweet' ) )
    return;

  global $aktt;

  // Set up defaults
  $defaults = array(
    'text' => '',
    'url' => '',
    'tags' => array()
  );

  // Extract the arguments
  extract( wp_parse_args( $args, $defaults ) );

  // Sanity check
  if( empty( $text ) )
    return;

  // Add the URL, after shortening
  if( ! empty( $url ) )
    $text .= ' ' . aktt_bitly_shorten_url( $url );

  // Add the hashtags
  if( count( $tags ) )
    $separator = ' #';
    $text .= $separator . implode( $separator, $tags );

  // Initialize the aktt_tweet object
  $tweet = new aktt_tweet;
  $tweet->tw_text = @html_entity_decode( $text , ENT_COMPAT, 'UTF-8' );

  // And Tweet!
  return $aktt->do_tweet( $tweet );
}
```

Armed with this function, we'll use the `wp_insert_post` action hook to check when a new **'product'** is added:

```php
<?php
add_action( 'wp_insert_post' , 'my_twitter_notifications' , 99 );
function my_twitter_notifications( $post_id ) {
  $post = get_post( $post_id );
  if( $post->post_status != 'publish' ) return;

  switch ( $post->post_type ) {
    case 'product':
      // Tweet it
      $args = array(
        'text' => 'New Product: ' . $post->post_title,
        'url' => get_permalink( $post_id ),
        'tags' => array( '#awesome', '#merchandise', '#fb' )
      );

      my_tweet( $args );
    break;
  }
}
```

This function checks the post type and calls the `my_tweet` function with the appropriate arguments.
