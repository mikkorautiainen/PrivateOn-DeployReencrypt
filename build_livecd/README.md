# Prerequisite

```
apt-get install live-build

mkdir config/includes.chroot/opt/PrivateOn-DeployReencrypt
cp -p ../* config/includes.chroot/opt/PrivateOn-DeployReencrypt/
cp -p -r ../images config/includes.chroot/opt/PrivateOn-DeployReencrypt/
```

# Building

```
lb build
```

# Run this to rebuild the image

```
lb clean
lb build
```

