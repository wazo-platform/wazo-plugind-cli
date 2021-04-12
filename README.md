# wazo-plugind-cli

This is the command line interface for wazo-plugind.

## Usage

### Installing a plugin

To install a plugin use the install command followed by the method and the URL

Example:

```
wazo-plugind-cli> install git https://github.com/wazo-platform/wazo-admin-ui-conference.git
extracting
building
packaging
installing
completed
wazo-plugind-cli>
```

"--async" can be used to avoid waiting until the end of the plugin installation.

Example:

```
wazo-plugind-cli> install git https://github.com/wazo-platform/wazo-admin-ui-conference.git --async
wazo-plugind-cli>
```

### Deleting a plugin

To remove a plugin, use the uninstall command

Example:

```
wazo-plugind-cli> uninstall official/admin-ui-conference
completed
wazo-plugind-cli>
```

This command can also be executed asynchronously using the --async command flag

Example:

```
wazo-plugind-cli> uninstall official/admin-ui-conference --async
wazo-plugind-cli>
```

### Executing commands without entering the CLI

To execute a command without first entering the wazo-plugind cli use the -c argument.

Example:

```sh
wazo-plugind-cli -c "install git https://github.com/wazo-platform/wazo-admin-ui-user.git"
```

## Building a debian package

### Increment the package version in the changelog

from the root of the project

```sh
dch -i
```

### Build the package

from the root of the project

```sh
dpkg-buildpackage -us -uc
```

If the build succeds, a .deb will be created in the parent directory.

