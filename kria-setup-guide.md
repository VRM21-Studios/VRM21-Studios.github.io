# Complete Setup Guide: Kria KR260 and KV260 (Ubuntu 22.04 LTS + PYNQ)

This guide documents the essential steps for configuring an AMD/Xilinx Kria KR260 or KV260 from a fresh installation to a development-ready environment. The resulting system can be configured for JupyterLab, Remote SSH development, and FPGA or embedded DSP experimentation.

> **Note:** This guide documents the development environment and configuration procedures used for this project. It is not intended to replace the official AMD/Xilinx documentation. Software versions, package availability, supported applications, and installation procedures may change over time between platforms and software releases.

> **Platform Note:** The KR260 and KV260 use the Kria K26 SOM platform, allowing many Ubuntu and network-level configuration procedures in this guide to be applied to both boards. However, platform-specific applications, hardware interfaces, and PYNQ installation options should always be verified for the target board.

---

## 1. System Optimization: Reducing SD Card Wear

By default, Ubuntu continuously writes system logs to persistent storage. On systems running from an SD card, reducing unnecessary write activity can help minimize storage wear.

This configuration applies to both the KR260 and KV260 when using a compatible Ubuntu-based environment.

### Configure Journald

Open the Journald configuration file:

```bash
sudo nano /etc/systemd/journald.conf
```

Locate the following line:

```text
#Storage=auto
```

Remove the comment marker and change it to:

```text
Storage=volatile
```

Save the file using `Ctrl+O`, press `Enter`, and exit with `Ctrl+X`.

Restart the Journald service:

```bash
sudo systemctl restart systemd-journald
```

> **Note:** With `Storage=volatile`, system logs are stored in RAM and will be lost after a reboot.

---

## 2. Practical Network Setup with mDNS

Using mDNS allows a Kria board to be accessed through a hostname instead of requiring its dynamically assigned IP address.

The following configuration can generally be applied to both the KR260 and KV260.

### Install Avahi

Update the package list and install the required packages:

```bash
sudo apt update
sudo apt install avahi-daemon libnss-mdns -y
```

### Configure the Hostname

You can assign a hostname according to the target platform.

For a KR260:

```bash
sudo hostnamectl set-hostname kria-kr260
```

For a KV260:

```bash
sudo hostnamectl set-hostname kria-kv260
```

Alternatively, a shared hostname such as `kria` may be used if only one Kria board is present on the local network.

### Enable the Avahi Service

Enable and restart the service:

```bash
sudo systemctl enable avahi-daemon
sudo systemctl restart avahi-daemon
```

The board can then be accessed through its configured hostname.

For example:

```text
kria-kr260.local
```

or:

```text
kria-kv260.local
```

Example SSH connections:

```bash
ssh ubuntu@kria-kr260.local
```

or:

```bash
ssh ubuntu@kria-kv260.local
```

---

## 3. Installing PYNQ and Handling Unattended Upgrades

Ubuntu may automatically run background package updates shortly after the board obtains an internet connection.

During this process, the package management system may be locked by another process. This can interfere with the PYNQ installation process and potentially cause installation failures or timeouts.

The following package management precautions are generally applicable to both platforms.

### Disable Unattended Upgrades

Stop the currently running service:

```bash
sudo systemctl stop unattended-upgrades
```

Disable automatic updates through the package configuration interface:

```bash
sudo dpkg-reconfigure -plow unattended-upgrades
```

When prompted by the configuration interface, select:

```text
No
```

Reboot the board to ensure that any existing package management locks are cleared:

```bash
sudo reboot
```

### Install Kria PYNQ

After the board has restarted, clone the Kria PYNQ repository:

```bash
git clone https://github.com/Xilinx/Kria-PYNQ.git
```

Enter the repository directory:

```bash
cd Kria-PYNQ/
```

Run the installation script according to the target board.

For the KR260:

```bash
sudo bash install.sh -b KR260
```

For the KV260:

```bash
sudo bash install.sh -b KV260
```

> **Important:** Verify the currently supported board identifiers and installation options in the Kria-PYNQ repository before running the installation script, as these may change between software versions.

Wait until the installation process is complete.

Once configured, JupyterLab can be accessed through a web browser using the hostname configured for the target board.

For example:

```text
http://kria-kr260.local:9090
```

or:

```text
http://kria-kv260.local:9090
```

Default credentials may depend on the installed operating system image and PYNQ version. Refer to the corresponding installation documentation if the default credentials differ from the environment described in this guide.

---

## 4. Configuring a USB Sound Card as the Default ALSA Device

When using a USB sound card for audio processing, it can be configured as the default ALSA device instead of the board's default audio interface.

This procedure is applicable to both the KR260 and KV260 when the required USB audio device is supported by the Linux kernel.

### Identify Available Audio Devices

List the available playback hardware:

```bash
aplay -l
```

Identify the card number corresponding to the USB sound card.

For example:

```text
card 1: USB [USB Audio Device], device 0: USB Audio
```

In this example, the USB sound card uses card number `1`.

### Create the ALSA Configuration

Open the global ALSA configuration file:

```bash
sudo nano /etc/asound.conf
```

Add the following configuration:

```text
defaults.pcm.card 1
defaults.ctl.card 1
```

Replace `1` with the appropriate card number if your USB sound card uses a different identifier.

Save the file and exit the editor.

The mixer can then be accessed using:

```bash
alsamixer
```

> **Note:** Audio device numbering may change depending on connected hardware and driver initialization order. Verify the device number with `aplay -l` if the configuration stops working.

---

## 5. Setting Up Remote SSH in Visual Studio Code

Remote SSH allows software, scripts, and hardware-related files to be edited directly from a host computer while the development environment remains on the Kria board.

### Install the Required Extension

Install the **Remote - SSH** extension in Visual Studio Code.

### Configure the SSH Connection

Open the SSH configuration file.

On Linux:

```text
~/.ssh/config
```

On Windows:

```text
C:\Users\<Username>\.ssh\config
```

You can create separate SSH configurations for each platform.

For a KR260:

```text
Host kria-kr260
    HostName kria-kr260.local
    User ubuntu
```

For a KV260:

```text
Host kria-kv260
    HostName kria-kv260.local
    User ubuntu
```

Save the configuration file.

### Connect to the Kria Board

Open the Visual Studio Code Command Palette and select:

```text
Remote-SSH: Connect to Host
```

Then select the appropriate target:

```text
kria-kr260
```

or:

```text
kria-kv260
```

When prompted, enter the password for the configured user account.

After the connection is established, Visual Studio Code can be used to edit and manage files directly on the target Kria platform.

---

## Development Environment Summary

After completing the configuration described in this guide, the Kria KR260 or KV260 can provide the following development environment:

* Reduced persistent system log writes to the SD card.
* Network access through an mDNS hostname.
* PYNQ and JupyterLab support for interactive development.
* Remote development through Visual Studio Code and SSH.
* USB audio device configuration for audio DSP experimentation.
* A practical environment for FPGA development, hardware accelerators, embedded systems, and DSP projects.

Although many software-level configurations are shared between the KR260 and KV260, hardware-specific interfaces and applications may differ between the two platforms.

---

## References

The following resources were used as references for configuring the Kria development environment and installing PYNQ:

* [PYNQ for Kria KV260 — Hackster.io](https://www.hackster.io/vjsubas/pynq-for-kria-kv260-55e419)
* [Kria-PYNQ — Official GitHub Repository](https://github.com/Xilinx/Kria-PYNQ)
