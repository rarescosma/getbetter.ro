Title: Rsync Tricks

!!! info "Wikipedia"

    `rsync` is a utility for efficiently transferring and synchronizing files between a computer and an external hard drive and across networked computers by comparing the modification times and sizes of files. It is commonly found on Unix-like operating systems.

In other words, it's the linux hobbyist's best friend when it comes to efficient networked data transfer between SSH-enabled hosts.

Over the years I've gathered quite a few tips and tricks for (ab)using the power of `rsync`.

### Preview mode

!!! help "Preview mode"

    Before proceeding with actual transfers, or when using the dangerous `--delete` flag, it's useful to get a preview of the operations `rsync` will perform.

#### List files present on `SRC` but not on `DEST`

This offers an accurate preview of what will get transfered over the wire: 
```shell
rsync -avu --delete DEST/ SRC/ -n | grep -E "^deleting "
```

!!! warning

    Notice the `-n` flag, the shorthand for `--dry-run`. 

    It is wise to always use it for testing commands which `--delete` things.

#### List files that would be transferred from `SRC` to `DEST`
```shell
rsync -avP --size-only SRC/ DEST/ -ni | grep -E '^<'
```

### Mirror mode

!!! help "Mirror mode"

    Sometimes it's useful to mirror a local directory structure using [hard links](https://en.wikipedia.org/wiki/Hard_link).

    A good example is wanting to use a backup tool that does not yet support advanced include/exclude/filter logic.

    We can piggyback on `rsync` to do that for us, then run the tool against the filtered "mirror".

#### Mirror `ROOT` to `ROOT/.rsync_mirror` using a `.rsync_exclude` file
```shell
rsync -av --delete \
  --exclude-from ROOT/.rsync_exclude \
  --link-dest="ROOT" \
  "ROOT/" "ROOT/.rsync_mirror/"
```

#### Mirror `ROOT` to `ROOT/.rsync_mirror` using a `.rsync_filter` file
```shell
rsync -av --delete \
  --filter=". ROOT/.rsync_filter" \
  --link-dest="ROOT" \
  "ROOT/" "ROOT/.rsync_mirror/"
```

!!! note "Caveat"

    To avoid cycles make sure the exclude or filter file references itself, as well as the mirror directory:
    ```
    .rsync_exclude
    .rsync_filter
    .rsync_mirror
    ```

### Controlling transfers

!!! help "Controlling transfers"

    Sometimes, due to limited computing capacity on the receiver, or simply because we're dealing with compressed binary files, it's useful to skip the checksum checks and act solely based on the file-size. 

    This can be achieved using the `--size-only` flag.

    Other times, we're not interesting in all the stuff that the `-a` archive mode would transfer. 

    We can easily exclude a bunch of stuff: `--no-perms` `--no-owner` `--no-group` `--omit-dir-times`

    When computing power permits, force checksum-based skipping even when the `mtime` and the `size` of a file match by using the `--checksum` flag.

    Use the `-N` flag to transfer the creation time of files. Good for those special cameras who don't include timestamps in the file names.

#### Transfer only the directory structure
Simply tell `rsync` to filter __in__ everything that looks like a directory and filter __out__ everything else:

```shell
rsync -av -f"+ */" -f"- *" SRC/ DEST/
```

Alternatively, using the `include/exclude` options:

```shell
rsync -av --include='*/' --exclude='*' SRC/ DEST/
```

#### Filter based on file prefixes
```shell
rsync -avP --size-only -f"+ IMG_2021*" -f"+ PANO_2021*" -f"- *" SRC/ DEST/images/
rsync -avP --size-only -f"+ VID_2021*" -f"- *" SRC/ DEST/videos/
```

#### Use different SSH keys and/or parameters
```shell
rsync -avP -e 'ssh -i /path/to/key.file' SRC/ DEST/
```

#### Change ownership & permissions during transfer
```shell
rsync -rvP --usermap=:user1 --chown:user1:user1 <SRC>/ <DEST>/
```

### Pro tips

!!! danger "[Here be dragons](https://en.wikipedia.org/wiki/Here_be_dragons)"

    Congratulations for making it thus far. Let the fun stuff begin!

#### Detect file moves & renames
Sometimes we get in that special mood of moving files and directories around in an effort to take control of the festering pile of bytes that make up our hard acquired digital hoards.

We proceed with the re-org, only to realize, with a certain degree of horror, that we now have to sync the changes to the a redundant remote hoard. Why the horror? Because `rsync` will transfer the entire content of moved files, unable to detect complex move operations. (No, the `--fuzzy` flag doesn't help.)

So what gives?

**BEFORE** the re-org - make a hard linked copy of the working tree, either by using the [rsync itself](#mirror-mode) or a simple `cp`:

```shell
cp -rlp ~/media/photo ~/media/photo-work
```

Now do the re-org in the `~/media/photo-work` dir: renaming, moving, adding and deleting as you see fit, but **DO NOT** touch the tree in `~/media/photo`.

When done with the re-org:

```shell
rsync -avP --hard-links --delete-after --no-inc-recursive \
  ~/media/photo ~/media/photo-work remotebox:~/media/
```

Finalize by swapping the original and `-work` trees _on both machines_.

#### Parallelize transfers
We already know how to [preview file transfers](#list-files-that-would-be-transferred-from-src-to-dest).

Let's keep the filenames only and use `split` in streaming (round-robin) mode to create equal work logs for a bunch of `rsync` workers:

```shell
rsync -avP --size-only SRC/ DEST/ -ni | grep -E '^<' \
  | cut -d" " -f2 | split - -n r/8 /tmp/transfers.
```

!!! note
    The `-n r/8` flag tells split to use round-robin for populating *8* output files, splitting the input at the line boundary. Since it's impossible to know the length of standard input data in advance, this is the only viable splitting strategy.

Then use `parallel` and the `--files-from` flag to start the actual transfers:

```shell
ls /tmp/transfers.* | parallel --lb -t -j 8 rsync -avP --files-from {} SRC/ DEST/
```

!!! note
    The `-j 8` flag matches the number of files we've generated with `split`.

    **Caveat:** the method outlined here does not guarantee an even distribution of transferred data between workers.

#### Back up entire filesystems

```shell
rsync -a -A --checksum --delete \
  --hard-links --sparse --devices \
  --numeric-ids --xattrs \
  SRC/ DEST/
```
