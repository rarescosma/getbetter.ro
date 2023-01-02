Title: Displaying current focus in i3
Tags: i3, processes, focusing

I've set up [i3](https://i3wm.org/) to display the task I'm currently focusing
on in the top bar by hacking together a simple solution using
[i3blocks](https://github.com/vivien/i3blocks),
[zenity](https://help.gnome.org/users/zenity/3.32/)
and a bunch of shell scripts.

<!-- PELICAN_END_SUMMARY -->

## Motivation

This is especially good for procrastinators since you'll constantly be reminded
of what you should focus on and have no excuses to veer off into doing
something else.


## Implementation

First, add a new block script under `~/.i3/blocks`. Let's call it `focus`.

```sh
> cat ~/.i3/blocks/focus
#!/usr/bin/env bash

test -f /tmp/focus && cat /tmp/focus
```

It will simply output the content of the `/tmp/focus` file if it exists.

Wire it into i3blocks by adding a section to `~/.i3/i3blocks.conf`

```text
[focus]
min_width=700
align=left
color=#ffffff
label=
interval=2
```

Next, we'll need a script that prompts us for input when we want to change
the focus text:

```sh
> cat ~/.i3/change-focus.sh

#!/usr/bin/env bash

out=$(zenity --entry --title="Change focus" --text="Focus on: ")
if [[ "$?" == "0" ]];
then
    echo "$out" > /tmp/focus
fi
```

Finally, we'll want to add a keybinding in `~/.i3/config`:

```text
# set the task you want to focus on
bindsym $mod+space exec --no-startup-id ~/.i3/change-focus.sh
```

## Demo

The end result looks something like this:

![Focus Dialog Demo](/images/focus_demo.png)
