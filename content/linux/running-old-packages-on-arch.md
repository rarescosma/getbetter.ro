Title: Running Old Packages on Arch
Tags: Linux, Wiki

# The problem

Sometimes the need arises to run an old package version on Arch. For example you could have a really, really derpy stock broker with such an outdated UI that it requires some forsaken version of Firefox to get going. 

# The solution

First, locate the package version you want in the [Arch archive](https://archive.archlinux.org/packages/).

Then, extract the libs of the old package somewhere in `/opt`, for example `/opt/firefox-libs`

Finally, override `LD_LIBRARY_PATH` when starting the program:

```
LD_LIBRARY_PATH=/opt/firefox-libs firefox
``` 
