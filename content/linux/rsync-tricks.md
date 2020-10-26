Title: Rsync Tricks
Tags: Linux, Wiki

Just a bunch of nifty `rsync` tricks gathered over the years.

### List all files that do not exist in `$TARGET` but exist in `$SOURCE`

This one helps with previewing what will actually get synced.

```
rsync -avun --delete $TARGET/ $SOURCE/ | grep "^deleting "
```

### Hardlink mirror the directory tree under `$DATA` to `$DATA/.rsync-mirror`

This one is really helpful when you're dealing with a random backup tool but want a generic solution for exclusion filters. Just add anything you *don't* want mirrored into `$DATA/.rsync_ignore`.

```
rsync -av --exclude-from $DATA/.rsync_ignore --link-dest=$DATA $DATA/ $DATA/.rsync_mirror
```

Make sure `$DATA/.rsync_ignore` excludes itself and the mirror directory to avoid cycles:

```
.rsync_ignore
.rsync_mirror
```

### Good for backups

    rsync -a -HA --sparse --devices --delete --checksum --numeric-ids --xattrs
