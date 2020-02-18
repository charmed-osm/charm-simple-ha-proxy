#!/usr/bin/env python3

import sys

sys.path.append("lib")

from ops.charm import CharmBase
from ops.main import main
from ops.model import (
    ActiveStatus,
    BlockedStatus,
    MaintenanceStatus,
    WaitingStatus,
    ModelError,
)
import os
import subprocess
import charms.requirementstxt


import paramiko
from charms.osm.sshproxy import SSHProxy


class SimpleCharm(CharmBase):
    def __init__(self, *args):
        super().__init__(*args)

        # Register all of the events we want to observe
        for event in (
            # Charm events
            self.on.config_changed,
            self.on.install,
            self.on.upgrade_charm,
            # Charm actions (primitives)
            self.on.touch_action,
            # OSM actions (primitives)
            self.on.start_action,
            self.on.stop_action,
            self.on.restart_action,
            self.on.reboot_action,
            self.on.upgrade_action,
            # SSH Proxy actions (primitives)
            self.on.generate_ssh_key_action,
            self.on.get_ssh_public_key_action,
            self.on.run_action,
            self.on.verify_ssh_credentials_action,
        ):
            self.framework.observe(event, self)

    def get_ssh_proxy(self):
        """Get the SSHProxy instance"""
        proxy = SSHProxy(
            hostname=self.model.config["ssh-hostname"],
            username=self.model.config["ssh-username"],
            password=self.model.config["ssh-password"],
        )
        return proxy

    def on_config_changed(self, event):
        """Handle changes in configuration"""
        unit = self.model.unit

        # Unit should go into a waiting state until verify_ssh_credentials is successful
        unit.status = WaitingStatus("Waiting for SSH credentials")
        proxy = self.get_ssh_proxy()

        verified = proxy.verify_credentials()
        if verified:
            unit.status = ActiveStatus()
        else:
            unit.status = BlockedStatus("Invalid SSH credentials.")

    def on_install(self, event):
        """Called when the charm is being installed"""
        unit = self.model.unit

        if not SSHProxy.has_ssh_key():
            unit.status = MaintenanceStatus("Generating SSH keys...")

            print("Generating SSH Keys")
            SSHProxy.generate_ssh_key()

        unit.status = ActiveStatus()

    def on_touch_action(self, event):
        """Touch a file."""
        filename = event.params["filename"]

        if len(self.model.config["ssh-hostname"]):
            proxy = self.get_ssh_proxy()

            stdout, stderr = proxy.run("touch {}".format(filename))
            if len(stderr):
                event.set_results({"success": False})
                event.fail(stderr)
            else:
                event.set_results({"success": True})
        else:
            event.set_results({"success": False})

    def on_upgrade_charm(self, event):
        """Upgrade the charm."""
        unit = self.model.unit

        # Mark the unit as under Maintenance.
        unit.status = MaintenanceStatus("Upgrading charm")

        self.on_install(event)

        # When maintenance is done, return to an Active state
        unit.status = ActiveStatus()

    ###############
    # OSM methods #
    ###############
    def on_start_action(self, event):
        """Start the VNF service on the VM."""
        pass

    def on_stop_action(self, event):
        """Stop the VNF service on the VM."""
        pass

    def on_restart_action(self, event):
        """Restart the VNF service on the VM."""
        pass

    def on_reboot_action(self, event):
        """Reboot the VM."""
        proxy = self.get_ssh_proxy()
        stdout, stderr = proxy.run("sudo reboot")

        if len(stderr):
            event.fail(stderr)

    def on_upgrade_action(self, event):
        """Upgrade the VNF service on the VM."""
        pass

    #####################
    # SSH Proxy methods #
    #####################
    def on_generate_ssh_key_action(self, event):
        """Generate a new SSH keypair for this unit."""

        if not SSHProxy.generate_ssh_key():
            event.fail("Unable to generate ssh key")

    def on_get_ssh_public_key_action(self, event):
        """Get the SSH public key for this unit."""

        pubkey = SSHProxy.get_ssh_public_key()

        event.set_results({"pubkey": SSHProxy.get_ssh_public_key()})

    def on_run_action(self, event):
        """Run an arbitrary command on the remote host."""

        cmd = event.params["command"]

        proxy = self.get_ssh_proxy()
        stdout, stderr = proxy.run(cmd)

        event.set_results({"output": stdout})

        if len(stderr):
            event.fail(stderr)

    def on_verify_ssh_credentials_action(self, event):
        """Verify the SSH credentials for this unit."""

        proxy = self.get_ssh_proxy()

        verified = proxy.verify_credentials()
        if verified:
            print("Verified!")
            event.set_results({"verified": True})
        else:
            print("Verification failed!")
            event.set_results({"verified": False})


if __name__ == "__main__":
    main(SimpleCharm)
