# PrivateOn-DeployReencrypt

###&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;Offline re-encryption tool for dm-crypt/LUKS systems
<br />
Add this application to a Debian-based live Linux distribution and repackage the image for distribution. <br />
The GUI allows the user to add key-slots, delete key-slots, view the header and re-encrypt the disk. <br />
The progress of the re-encryption process is show with a progress bar and an ETA estimate. <br />

The application is meant for mass deployment to end-users that have predefined disk configurations. <br />
It can be run from a desktop environment or it can replace the window manager altogether. <br />
If you need to re-encrypt a single computer, we suggest booting a live Linux and running the *cryptsetup* and *cryptsetup-reencrypt* commands directly without this program. <br />
<br />
*Note:* This application can **NOT** re-encrypt the disk partition that the system is running from. <br />
Hence, if your root-filesytem is encrypted, your only option is to boot another Linux that doesn't use this disk partition.
