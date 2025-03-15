# Managing Symbolic Links in Linux

<br/><br/>

Symbolic links (symlinks) are special file types that point to another file or directory. They act as shortcuts and are commonly used for managing file locations efficiently.

<br/><br/>

## Creating a Symbolic Link

<br/>

To create a symbolic link, use the `ln -s` command:

<br/>

```bash
ln -s /path/to/original /path/to/symlink
```

<br/><br/>

### Example

<br/>

If you have a directory `/home/user/projects/original` and want to create a symlink `/home/user/projects/link`, run:

<br/>

```bash
ln -s /home/user/projects/original /home/user/projects/link
```

<br/>

Now, `/home/user/projects/link` will act as a reference to `/home/user/projects/original`.

<br/><br/>

## Listing Symbolic Links

<br/>

To verify symlinks, use:

<br/>

```bash
ls -l /path/to/symlink
```

<br/>

The output will show:

<br/>

```
symlink -> /path/to/original
```

<br/><br/>

## Removing a Symbolic Link

<br/>

To delete a symlink, use the `rm` command:

<br/>

```bash
rm /path/to/symlink
```

<br/>

### Important Notes

- Removing a symlink **does not** delete the original file or directory.

- Do **not** use `rm -r` unless you want to remove the target directory itself.

<br/><br/>

## Overwriting an Existing Symlink

<br/>

If a symlink already exists and you want to replace it, use:

<br/>

```bash
ln -sf /new/path /path/to/symlink
```

<br/>

The `-f` flag forces overwriting.

<br/><br/>

## Finding Symbolic Links

<br/>

To find symlinks in a directory, use:

<br/>

```bash
find /path/to/directory -type l
```

<br/>

This command lists all symbolic links within the specified directory.

<br/><br/><br/><br/>

# My symlink for kmk library

<br/>

```bash
ln -s /home/maks/Dokumenty/split_keeb/.ALL/kmk_repo/kmk_firmware/kmk /home/maks/Dokumenty/split_keeb/libs_to_compile/lib/kmk
```

<br/><br/>