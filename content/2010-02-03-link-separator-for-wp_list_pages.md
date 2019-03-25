Title: Link separator for wp_list_pages()
Tags: wordpress, a-lifetime-ago
ExtraTags: wordpress

A common problem with the WordPress built-in function for page navigation is the lack of anchor text separator support.
<!-- PELICAN_END_SUMMARY -->

In version 2.7 two more arguments for `wp_list_pages()` were added to mitigate this inconvenience: `link_before` and `link_after`. When using these, the function prepends or appends the specified strings to the generated anchor text. This works well for styling vertical menus.

However, for horizontal menus like the one below, you want the separator to appear between consecutive links and both options become unsuitable:

* `link_before` would produce extra markup before the first link
* `link_after` would produce extra markup after the last link

![Horizontal Menu Example](/images/legacy/horizontal_navigation.png)

### The solution

The solution involves using regular expressions to inject the page separator.
Basically, you want to alter the structure of all links except the last one. This can be accomplished by searching for all list elements that are followed by an extra list element.

### The code

```language-php
<?php
$args = array(
  'sort_column' => 'menu_order',
  'title_li' => '',
  'depth' => '1',
  'echo' => 0
);
$separator = ' | ';
$pattern = '/(<\\/a>).*?(<\\/li>).*?(<li)/is';
$replace = '</a>' . $separator . '</li><li';
$subnav = preg_replace( $pattern, $replace, wp_list_pages( $args ) );
echo $subnav;
```
You can specify the separator string in the `$separator` variable and alter its appearance position by changing the `$replace` variable.

### Resources

* The [wp\_list_pages()](http://codex.wordpress.org/Template_Tags/wp_list_pages) codex reference page
* The wonderful [http://txt2re.com](http://txt2re.com) regular expression generator
