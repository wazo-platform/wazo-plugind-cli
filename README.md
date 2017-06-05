# wazo-plugind-cli

This is the command line interface for wazo-plugind.

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
