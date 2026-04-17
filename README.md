# wazo-plugind-cli

A CLI program to interact with wazo-plugind.

## Usage

### Installing a plugin

```shell
$ wazo-plugind-cli install git https://github.com/wazo-platform/wazo-admin-ui-conference.git
extracting...
building...
packaging...
installing...
completed
```

Use `--async` to return immediately without waiting for completion:

```shell
wazo-plugind-cli install git https://github.com/wazo-platform/wazo-admin-ui-conference.git --ref main --async
```

Supported options on `git` installs: `--ref <ref>`, `--subdirectory <path>`.

### Uninstalling a plugin

```shell
$ wazo-plugind-cli uninstall official/admin-ui-conference
completed
```

`--async` is also supported.

### Listing installed plugins

```shell
$ wazo-plugind-cli list
* List of plugins installed *
- official/admin-ui-conference (1.0.0)
```

`list` supports cliff's `-f` flag for alternative output formats:

```shell
wazo-plugind-cli list -f table
wazo-plugind-cli list -f json
wazo-plugind-cli list -f csv
wazo-plugind-cli list -f yaml
```

The default format is the legacy text format.

### Legacy `-c` flag

The `-c "<command>"` invocation is still accepted for backward
compatibility but is deprecated; prefer passing the command as direct
arguments.

```shell
wazo-plugind-cli -c "install git https://github.com/wazo-platform/wazo-admin-ui-user.git"
```

## Building a debian package

### Increment the package version in the changelog

From the root of the project:

```sh
dch -i
```

### Build the package

From the root of the project:

```sh
dpkg-buildpackage -us -uc
```

If the build succeeds, a `.deb` will be created in the parent directory.
